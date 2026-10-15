"""Hash-bound atlas crop/resize/tile replacement. No model or shader mutation."""
import hashlib
import json
from pathlib import Path
import re
import shutil

import numpy as np
from PIL import Image


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.png', value):
        raise ValueError('Expected a plain PNG filename')
    return value


def _box(value, size, label):
    if (not isinstance(value, list) or len(value) != 4 or
            any(type(n) is not int for n in value)):
        raise ValueError(f'Invalid {label}')
    x0, y0, x1, y1 = value
    if not (0 <= x0 < x1 <= size[0] and 0 <= y0 < y1 <= size[1]):
        raise ValueError(f'{label} is outside image')
    return value


def replace_atlas(config, source, maps, output, reference=None):
    """Preflight all inputs before creating a fresh output directory."""
    source, maps, output = Path(source), Path(maps), Path(output)
    if output.exists():
        raise FileExistsError('Output must be a fresh directory')
    if output.resolve().is_relative_to(maps.resolve()):
        raise ValueError('Output cannot be inside input maps')
    expected = config['input_maps']
    if not isinstance(expected, dict) or not expected:
        raise ValueError('Empty input map inventory')
    for name, digest in expected.items():
        _name(name)
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Invalid SHA256')
    actual = {p.name for p in maps.iterdir() if p.is_file() and p.suffix.lower() == '.png'}
    if actual != set(expected):
        raise ValueError('Input PNG inventory differs')
    if sha256(source) != config['source_sha256']:
        raise ValueError('Source hash differs')
    for name, digest in expected.items():
        if sha256(maps / name) != digest:
            raise ValueError(f'Input hash differs: {name}')
    targets = config['targets']
    if not targets or len(targets) != len(set(targets)) or not set(targets) <= set(expected):
        raise ValueError('Invalid or duplicate target names')
    with Image.open(source) as im:
        if list(im.size) != config['source_size']:
            raise ValueError('Source dimensions differ')
        atlas = im.convert('RGB')
    crop = _box(config['crop'], atlas.size, 'crop')
    tile_size = config['scaled_size']
    if (len(tile_size) != 2 or any(type(n) is not int or not 1 <= n <= 8192 for n in tile_size)
            or tile_size[0] * (crop[3] - crop[1]) != tile_size[1] * (crop[2] - crop[0])):
        raise ValueError('Resize must have bounded dimensions and preserve aspect ratio')
    rect = config['target_rectangle']
    for name in targets:
        with Image.open(maps / name) as im:
            if im.mode != 'RGB':
                raise ValueError('Target must be RGB; implicit alpha loss is forbidden')
            _box(rect, im.size, 'target rectangle')
    if reference:
        reference = Path(reference)
        if {p.name for p in reference.glob('*.png')} != set(expected):
            raise ValueError('Reference PNG inventory differs')
    tile = atlas.crop(crop).resize(tuple(tile_size), Image.Resampling.LANCZOS)
    x0, y0, x1, y1 = rect
    patch = Image.new('RGB', (x1 - x0, y1 - y0))
    for y in range(0, patch.height, tile.height):
        for x in range(0, patch.width, tile.width):
            patch.paste(tile, (x, y))
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in sorted(expected):
        src, dst = maps / name, output / name
        if name in targets:
            with Image.open(src) as im:
                before = np.asarray(im).copy()
                im.paste(patch, (x0, y0))
                im.save(dst)
            with Image.open(dst) as saved:
                after = np.asarray(saved)
                mask = np.zeros(after.shape[:2], bool)
                mask[y0:y1, x0:x1] = True
                if not np.array_equal(before[~mask], after[~mask]):
                    raise ValueError('Pixels outside replacement changed')
                if not np.array_equal(after[mask], np.asarray(patch).reshape(-1, 3)):
                    raise ValueError('Saved patch differs')
        else:
            shutil.copy2(src, dst)
        changed = sha256(dst) != expected[name]
        if changed != (name in targets):
            raise ValueError(f'Unexpected change classification: {name}')
        row = {'name': name, 'sha256': sha256(dst), 'changed': changed}
        if reference:
            with Image.open(dst) as got, Image.open(reference / name) as want:
                equal = got.mode == want.mode and got.size == want.size and np.array_equal(np.asarray(got), np.asarray(want))
            row.update(reference_pixels_equal=bool(equal), reference_bytes_equal=dst.read_bytes() == (reference / name).read_bytes())
            if not equal:
                raise ValueError(f'Reference pixels differ: {name}')
        rows.append(row)
    # Recheck inputs to catch concurrent modifications during generation.
    if sha256(source) != config['source_sha256'] or any(sha256(maps / n) != h for n, h in expected.items()):
        raise ValueError('Inputs changed during build; discard this partial output')
    report = {'operation': 'atlas_replace', 'maps': rows, 'source_sha256': config['source_sha256'],
              'changed_maps': sum(r['changed'] for r in rows), 'outside_rectangle_equal': True,
              'scope': 'PNG pixels only; no Max, UV, geometry, render, seamlessness or VPM-scale acceptance',
              'delivery_passed': False}
    (output / 'QA.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report

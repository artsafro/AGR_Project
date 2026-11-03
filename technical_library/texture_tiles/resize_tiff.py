"""Exact 2x ImageMagick resampling with fresh outputs and optional pixel replay."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image

EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(executable, *args):
    result = subprocess.run([str(executable), *map(str, args)], capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=180)
    if result.returncode:
        raise RuntimeError('ImageMagick failed: ' + result.stderr.strip())
    return result.stdout.strip()


def absolute(value):
    path = Path(value)
    if not path.is_absolute():
        raise ValueError('Absolute paths required')
    if path.is_symlink():
        raise ValueError('Symlink paths are not supported')
    return path.resolve()


def readback(path, executable):
    info = command(executable, 'identify', '-format', '%n|%w|%h|%z|%[colorspace]|%[compression]\\n', path).splitlines()
    if len(info) != 1:
        raise ValueError('Only single-frame images supported')
    frames, width, height, depth, colorspace, compression = info[0].split('|')
    if frames != '1' or depth != '8' or colorspace != 'sRGB':
        raise ValueError('Only single-frame 8-bit sRGB images supported')
    with Image.open(path) as image:
        image.load()
        if getattr(image, 'n_frames', 1) != 1 or image.mode != 'RGB':
            raise ValueError('Only RGB single-frame images supported')
        if image.size != (int(width), int(height)):
            raise ValueError('Independent size readback mismatch')
        pixels = hashlib.sha256(image.tobytes()).hexdigest()
        icc = hashlib.sha256(image.info.get('icc_profile', b'')).hexdigest()
        return {'size': list(image.size), 'mode': image.mode, 'depth': 8,
                'colorspace': colorspace, 'compression': compression,
                'pixels_sha256': pixels, 'icc_sha256': icc, 'format': image.format}


def run(source, output, magick, reference=None):
    source, output, magick = map(absolute, (source, output, magick))
    reference = absolute(reference) if reference else None
    if not source.is_dir() or not magick.is_file():
        raise ValueError('Source directory and ImageMagick executable must exist')
    if reference and not reference.is_dir():
        raise ValueError('Reference directory unavailable')
    if output.exists() or output.is_symlink():
        raise FileExistsError('Output exists; refusing overwrite')
    if any('approved' in part.lower() for part in output.parts):
        raise ValueError('Refusing write to approved path')
    if not output.parent.is_dir():
        raise ValueError('Output parent must exist')
    if output.is_relative_to(source) or reference and output.is_relative_to(reference):
        raise ValueError('Output must be outside source/reference directories')
    version = command(magick, '-version').splitlines()[0]
    files = sorted((p for p in source.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS), key=lambda p: p.name.casefold())
    if not files:
        raise ValueError('No supported images')
    names = [p.stem.casefold() + '_x2.tiff' for p in files]
    if len(set(names)) != len(names):
        raise ValueError('Output basename collision')
    plan = []
    for path in files:
        if path.is_symlink():
            raise ValueError('Symlink inputs are not supported')
        before = digest(path)
        original = readback(path, magick)
        ref = reference / (path.stem + '_x2.tiff') if reference else None
        if ref and (not ref.is_file() or ref.is_symlink()):
            raise ValueError('Missing or symlink reference image')
        ref_hash, ref_info = (digest(ref), readback(ref, magick)) if ref else (None, None)
        if ref_info and ref_info['size'] != [v * 2 for v in original['size']]:
            raise ValueError('Reference dimensions do not match 2x input')
        plan.append((path, before, original, ref, ref_hash, ref_info))
    # Preflight every image and reference before creating any output.
    output.mkdir()
    rows = []
    for path, before, original, ref, ref_hash, ref_info in plan:
        if digest(path) != before or ref and digest(ref) != ref_hash:
            raise ValueError('Input/reference changed after preflight')
        target = output / (path.stem + '_x2.tiff')
        command(magick, path, '-filter', 'Lanczos', '-resize', '200%', '-compress', 'LZW', target)
        actual = readback(target, magick)
        if actual['size'] != [v * 2 for v in original['size']] or actual['format'] != 'TIFF' or actual['compression'] != 'LZW':
            raise ValueError('Output dimensions/format/compression mismatch')
        if actual['icc_sha256'] != original['icc_sha256']:
            raise ValueError('Source ICC profile changed')
        if ref_info and any(actual[k] != ref_info[k] for k in ('size', 'mode', 'depth', 'pixels_sha256', 'icc_sha256')):
            raise ValueError('Reference pixel/profile replay mismatch')
        rows.append({'source_name': path.name, 'source_sha256': before,
                     'reference_sha256': ref_hash, 'output_name': target.name,
                     'output_sha256': digest(target), 'input_size': original['size'],
                     **actual, 'reference_equal': True if ref else None})
    # Recheck all sources, including ones processed earlier in the batch.
    if any(digest(p) != h or ref and digest(ref) != rh for p, h, _, ref, rh, _ in plan):
        raise ValueError('Input/reference changed during conversion')
    report = {'operation': 'exact-2x-tiff', 'runtime': version, 'files': rows,
              'conversion_readback_passed': True,
              'reference_replay_passed': True if reference else None,
              'source_hashes_unchanged': True, 'delivery_passed': False}
    with (output / 'report.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--magick', required=True)
    parser.add_argument('--reference')
    args = parser.parse_args()
    try:
        report = run(args.source, args.output, args.magick, args.reference)
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps({'files': len(report['files']), 'reference_replay_passed': report['reference_replay_passed']}))


if __name__ == '__main__':
    main()

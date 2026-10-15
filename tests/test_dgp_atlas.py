import hashlib

import numpy as np
import pytest
from PIL import Image

from technical_library.texture_tiles.atlas import replace_atlas


def fixture(tmp_path):
    source = tmp_path / 'source.png'
    pixels = np.arange(8 * 8 * 3, dtype=np.uint8).reshape(8, 8, 3)
    Image.fromarray(pixels).save(source)
    maps = tmp_path / 'maps'
    maps.mkdir()
    for name in ('a.png', 'b.png'):
        Image.new('RGB', (8, 8), (10, 20, 30)).save(maps / name)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    config = {'source_sha256': sha(source), 'source_size': [8, 8], 'crop': [0, 4, 8, 8],
              'scaled_size': [4, 2], 'target_rectangle': [1, 1, 7, 5], 'targets': ['a.png'],
              'input_maps': {p.name: sha(p) for p in maps.glob('*.png')}}
    return source, maps, config


def test_reference_route_and_mask(tmp_path):
    source, maps, config = fixture(tmp_path)
    reference = tmp_path / 'reference'
    reference.mkdir()
    with Image.open(source) as atlas:
        tile = atlas.crop((0, 4, 8, 8)).resize((4, 2), Image.Resampling.LANCZOS)
    patch = Image.new('RGB', (6, 4))
    for y in range(0, 4, 2):
        for x in range(0, 6, 4):
            patch.paste(tile, (x, y))
    with Image.open(maps / 'a.png') as im:
        im.paste(patch, (1, 1))
        im.save(reference / 'a.png')
    (reference / 'b.png').write_bytes((maps / 'b.png').read_bytes())
    report = replace_atlas(config, source, maps, tmp_path / 'result', reference)
    assert report['changed_maps'] == 1
    assert report['outside_rectangle_equal']
    assert all(r['reference_bytes_equal'] for r in report['maps'])
    assert not report['delivery_passed']


@pytest.mark.parametrize('failure', ['source_hash', 'map_hash', 'inventory', 'traversal', 'duplicate', 'bounds', 'scale', 'alpha', 'occupied', 'nested'])
def test_preflight_no_output(tmp_path, failure):
    source, maps, config = fixture(tmp_path)
    output = tmp_path / 'result'
    if failure == 'source_hash':
        source.write_bytes(b'changed')
    elif failure == 'map_hash':
        (maps / 'a.png').write_bytes(b'changed')
    elif failure == 'inventory':
        (maps / 'b.png').unlink()
    elif failure == 'traversal':
        config['input_maps']['../evil.png'] = '0' * 64
    elif failure == 'duplicate':
        config['targets'] *= 2
    elif failure == 'bounds':
        config['target_rectangle'][2] = 99
    elif failure == 'scale':
        config['scaled_size'] = [4, 3]
    elif failure == 'alpha':
        Image.new('RGBA', (8, 8)).save(maps / 'a.png')
        config['input_maps']['a.png'] = hashlib.sha256((maps / 'a.png').read_bytes()).hexdigest()
    elif failure == 'occupied':
        output.mkdir()
        (output / 'keep.txt').write_text('retained')
    elif failure == 'nested':
        output = maps / 'nested'
    with pytest.raises((ValueError, FileExistsError)):
        replace_atlas(config, source, maps, output)
    if failure == 'occupied':
        assert (output / 'keep.txt').read_text() == 'retained'
    else:
        assert not output.exists()

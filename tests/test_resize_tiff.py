import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'technical_library/texture_tiles/resize_tiff.py'
MAGICK = os.environ.get('AGR_MAGICK') or shutil.which('magick')
pytestmark = pytest.mark.skipif(not MAGICK, reason='ImageMagick executable unavailable')


def invoke(source, output, reference=None):
    args = [sys.executable, str(SCRIPT), '--source', str(source), '--output', str(output), '--magick', MAGICK]
    if reference:
        args += ['--reference', str(reference)]
    return subprocess.run(args, text=True, capture_output=True, timeout=180)


def fixture_image(source):
    source.mkdir()
    image = Image.new('RGB', (13, 9))
    image.putdata([(x * 17, y * 21, (x + y) * 9) for y in range(9) for x in range(13)])
    image.save(source / 'example.png')


def test_cli_resample_readback_and_reference(tmp_path):
    source = tmp_path / 'source'
    fixture_image(source)
    first, second = tmp_path / 'first', tmp_path / 'second'
    result = invoke(source, first)
    assert result.returncode == 0, result.stderr
    report = json.loads((first / 'report.json').read_text())
    assert report['reference_replay_passed'] is None
    assert report['delivery_passed'] is False
    assert report['files'][0]['size'] == [26, 18]
    assert report['files'][0]['compression'] == 'LZW'
    assert report['files'][0]['mode'] == 'RGB'
    result = invoke(source, second, first)
    assert result.returncode == 0, result.stderr
    report2 = json.loads((second / 'report.json').read_text())
    assert report2['reference_replay_passed'] is True
    assert report2['files'][0]['pixels_sha256'] == report['files'][0]['pixels_sha256']


def test_existing_output_unchanged(tmp_path):
    source, output = tmp_path / 'source', tmp_path / 'output'
    fixture_image(source)
    output.mkdir()
    sentinel = output / 'example_x2.tiff'
    sentinel.write_bytes(b'approved existing bytes')
    result = invoke(source, output)
    assert result.returncode == 1
    assert 'refusing overwrite' in result.stderr
    assert sentinel.read_bytes() == b'approved existing bytes'


def test_basename_collision_before_output(tmp_path):
    source, output = tmp_path / 'source', tmp_path / 'output'
    fixture_image(source)
    Image.new('RGB', (2, 2)).save(source / 'EXAMPLE.jpg')
    result = invoke(source, output)
    assert result.returncode == 1
    assert 'collision' in result.stderr
    assert not output.exists()


def test_multiframe_rejected_before_output(tmp_path):
    source, output = tmp_path / 'source', tmp_path / 'output'
    source.mkdir()
    a = Image.new('RGB', (4, 4))
    a.save(source / 'animation.tiff', save_all=True, append_images=[a])
    result = invoke(source, output)
    assert result.returncode == 1
    assert 'single-frame' in result.stderr
    assert not output.exists()


def test_missing_reference_before_output(tmp_path):
    source, output = tmp_path / 'source', tmp_path / 'output'
    fixture_image(source)
    result = invoke(source, output, tmp_path / 'absent')
    assert result.returncode == 1
    assert 'Reference directory unavailable' in result.stderr
    assert not output.exists()


@pytest.mark.parametrize('kind', ['protected', 'source-child'])
def test_protected_paths_are_not_created(tmp_path, kind):
    source = tmp_path / 'source'
    fixture_image(source)
    if kind == 'protected':
        parent = tmp_path / 'approved-v001'
        parent.mkdir()
        output = parent / 'new'
    else:
        output = source / 'new'
    result = invoke(source, output)
    assert result.returncode == 1
    assert not output.exists()


def test_cmyk_rejected_before_output(tmp_path):
    source, output = tmp_path / 'source', tmp_path / 'output'
    source.mkdir()
    Image.new('CMYK', (4, 4)).save(source / 'example.jpg')
    result = invoke(source, output)
    assert result.returncode == 1
    assert 'sRGB' in result.stderr
    assert not output.exists()


def test_reference_difference_fails_without_success_report(tmp_path):
    source, reference, output = tmp_path / 'source', tmp_path / 'reference', tmp_path / 'output'
    fixture_image(source)
    reference.mkdir()
    Image.new('RGB', (26, 18), 'red').save(reference / 'example_x2.tiff', compression='tiff_lzw')
    result = invoke(source, output, reference)
    assert result.returncode == 1
    assert 'replay mismatch' in result.stderr
    assert not (output / 'report.json').exists()


def test_private_eight_image_replay(tmp_path):
    source, reference = os.environ.get('AGR_TIFF_SOURCE'), os.environ.get('AGR_TIFF_REFERENCE')
    if not source or not reference:
        pytest.skip('Private TIFF replay inputs not supplied')
    output = tmp_path / 'private-replay'
    result = invoke(Path(source).resolve(), output, Path(reference).resolve())
    assert result.returncode == 0, result.stderr
    report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
    assert len(report['files']) == 8
    assert report['reference_replay_passed'] is True
    assert report['source_hashes_unchanged'] is True
    assert all(row['reference_equal'] for row in report['files'])

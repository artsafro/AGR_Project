"""CLI safety checks; private exact-input replay is opt-in, never an embedded model."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

PACKAGE = Path(__file__).resolve().parents[1] / 'technical_library/mesh_audit/pipe_lattice'
NODE = shutil.which('node')
pytestmark = pytest.mark.skipif(not NODE, reason='Node runtime unavailable')


def invoke(source, reference, output, *extra):
    return subprocess.run(
        [NODE, str(PACKAGE / 'lattice.cjs'), '--source', str(source),
         '--reference', str(reference), '--output-directory', str(output), *extra],
        text=True, capture_output=True, timeout=45,
    )


def test_changed_source_rejected_before_output(tmp_path):
    source = tmp_path / 'source.json'
    source.write_text('[{"i":1,"pos":[0,0,0]}]', encoding='utf-8')
    before = source.read_bytes()
    output = tmp_path / 'new'
    result = invoke(source, tmp_path / 'missing-reference.json', output)
    assert result.returncode == 1
    assert 'Source SHA256 mismatch' in result.stderr
    assert source.read_bytes() == before
    assert not output.exists()


def test_existing_output_is_never_touched(tmp_path):
    output = tmp_path / 'existing'
    output.mkdir()
    sentinel = output / 'mesh.json'
    sentinel.write_bytes(b'approved original')
    result = invoke(tmp_path / 'missing-source', tmp_path / 'missing-reference', output)
    assert result.returncode == 1
    assert 'refusing overwrite' in result.stderr
    assert sentinel.read_bytes() == b'approved original'
    assert sorted(p.name for p in output.iterdir()) == ['mesh.json']


def test_config_drift_rejected(tmp_path):
    config = json.loads((PACKAGE / 'scenario.json').read_text(encoding='utf-8'))
    config['gap_m'] = 0.01
    config_path = tmp_path / 'changed.json'
    config_path.write_text(json.dumps(config), encoding='utf-8')
    output = tmp_path / 'new'
    result = invoke(tmp_path / 'missing-source', tmp_path / 'missing-reference', output,
                    '--config', str(config_path))
    assert result.returncode == 1
    assert 'config drift' in result.stderr
    assert not output.exists()


def test_relative_input_rejected(tmp_path):
    result = invoke(Path('relative-source.json'), tmp_path / 'reference', tmp_path / 'new')
    assert result.returncode == 1
    assert '--source must be absolute' in result.stderr
    assert not (tmp_path / 'new').exists()


def test_private_same_input_replay_and_roundtrip(tmp_path):
    names = ('AGR_PIPE_SOURCE', 'AGR_PIPE_REFERENCE')
    if not all(os.environ.get(name) for name in names):
        pytest.skip('Private source/reference not supplied through AGR_PIPE_SOURCE/REFERENCE')
    source, reference = (Path(os.environ[name]).resolve() for name in names)
    if not source.is_file() or not reference.is_file():
        pytest.skip('Private source/reference unavailable on this machine')
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, reference)]
    output = tmp_path / 'new'
    result = invoke(source, reference, output)
    assert result.returncode == 0, result.stderr
    mesh = json.loads((output / 'mesh.json').read_text(encoding='utf-8'))
    expected = json.loads(reference.read_text(encoding='utf-8'))
    report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
    assert mesh['faces'] == expected['faces']
    assert len(mesh['vertices']) == 22608
    assert len(mesh['faces']) == 23760
    error = max(abs(a-b) for actual, target in zip(mesh['vertices'], expected['vertices'])
                for a, b in zip(actual, target))
    assert error <= 1e-12
    assert report['max_coordinate_error_m'] == error
    assert mesh['parameters']['gap'] == 0.0102
    assert report['delivery_passed'] is False
    assert str(source) not in json.dumps(report)
    assert before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, reference)]
    # Re-running through the actual public entrypoint must preserve produced bytes.
    saved = {p.name: p.read_bytes() for p in output.iterdir()}
    again = invoke(source, reference, output)
    assert again.returncode == 1
    assert saved == {p.name: p.read_bytes() for p in output.iterdir()}

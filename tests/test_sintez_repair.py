"""Negative gates for the case adapter, executable without Blender/addon/assets."""
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('sintez_case', ROOT / 'technical_library/sintez_repair/repair.py')
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


@pytest.mark.parametrize('name', ['../bad', 'a/b', 'a\\b', 'C:bad', '.', '..', ''])
def test_names_cannot_escape_output(name):
    with pytest.raises(ValueError, match='Unsafe'):
        repair.safe_name(name)


def test_existing_output_is_protected(tmp_path):
    with pytest.raises(ValueError, match='NEW'):
        repair.empty_output(tmp_path, [])


def test_output_cannot_enclose_or_enter_input(tmp_path):
    source = tmp_path / 'source' / 'a.blend'
    for output in [source, source.parent, source / 'nested']:
        with pytest.raises(ValueError, match='overlaps'):
            repair.empty_output(output, [source])


def test_new_disjoint_output_allowed(tmp_path):
    output = tmp_path / 'new'
    assert repair.empty_output(output, [tmp_path / 'source.blend']) == output
    assert not output.exists()


def test_addon_code_and_requirements_drift_changes_pin(tmp_path):
    (tmp_path / 'core.py').write_text('x = 1')
    first = repair.addon_digest(tmp_path)
    (tmp_path / 'requirements.csv').write_text('changed rule')
    assert repair.addon_digest(tmp_path) != first
    second = repair.addon_digest(tmp_path)
    (tmp_path / 'core.py').write_text('x = 2')
    assert repair.addon_digest(tmp_path) != second


def test_wrong_snapshot_fails_before_blender_or_output_mutation(tmp_path):
    source = tmp_path / 'input.blend'
    source.write_bytes(b'changed')
    output = tmp_path / 'new'
    with pytest.raises(ValueError, match='Snapshot hash mismatch'):
        repair.repair(None, {'snapshot_sha256': '0' * 64}, source, output)
    assert not output.exists()


def test_changed_saved_blend_fails_before_native_execution(tmp_path):
    blend = tmp_path / 'repaired.blend'
    blend.write_bytes(b'changed')
    (tmp_path / 'repair.json').write_text(json.dumps({'blend_sha256': '0' * 64}))
    with pytest.raises(ValueError, match='Saved blend changed'):
        repair.readback(None, {}, blend, tmp_path, tmp_path / 'qa')
    assert not (tmp_path / 'qa').exists()


def test_changed_archive_fails_before_native_execution(tmp_path):
    blend = tmp_path / 'repaired.blend'
    blend.write_bytes(b'unchanged')
    (tmp_path / 'case.zip').write_bytes(b'changed')
    (tmp_path / 'repair.json').write_text(json.dumps({'blend_sha256': repair.sha(blend), 'archive_sha256': '0' * 64}))
    with pytest.raises(ValueError, match='ZIP changed'):
        repair.readback(None, {'package': 'case'}, blend, tmp_path, tmp_path / 'qa')
    assert not (tmp_path / 'qa').exists()


def test_source_drift_after_export_blocks_final_save_and_success(tmp_path):
    source = tmp_path / 'source.blend'
    source.write_bytes(b'original pinned snapshot')
    expected = repair.sha(source)
    # Inject another writer after initial pin check/export.
    source.write_bytes(b'changed while exporting')
    output = tmp_path / 'new-output'
    with pytest.raises(ValueError, match='Snapshot changed during repair'):
        repair.save_new_blend(None, source, output, expected)
    assert not output.exists()

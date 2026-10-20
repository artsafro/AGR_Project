"""Synthetic safety counterexamples; native Blender readback is a separate gate."""
from types import SimpleNamespace

import pytest

from technical_library.mesh_audit.smoothing import validate_paths, validate_targets


def inputs(tmp_path):
    source = tmp_path / 'source.blend'
    source.write_bytes(b'synthetic, not a Blender model')
    return source, tmp_path / 'output.blend', tmp_path / 'report.json'


def test_paths_accept_new_distinct_outputs(tmp_path):
    paths = inputs(tmp_path)
    assert validate_paths(*paths)[:3] == paths
    assert not paths[1].exists() and not paths[2].exists()


def test_blend1_historical_reference_is_read_only_and_never_an_output(tmp_path):
    paths = inputs(tmp_path)
    reference = tmp_path / 'historical.blend1'
    reference.write_bytes(b'historical fixture')
    assert validate_paths(*paths, reference=reference)[3] == reference
    assert reference.read_bytes() == b'historical fixture'
    with pytest.raises(ValueError, match='Output must be'):
        validate_paths(paths[0], tmp_path / 'new.blend1', paths[2])


@pytest.mark.parametrize('angle', [0, 180, -1, float('nan'), float('inf')])
def test_reject_invalid_angles(tmp_path, angle):
    with pytest.raises(ValueError, match='Angle'):
        validate_paths(*inputs(tmp_path), angle=angle)


@pytest.mark.parametrize('count', [0, -1, 1.5, True])
def test_reject_invalid_count(tmp_path, count):
    with pytest.raises(ValueError, match='count'):
        validate_paths(*inputs(tmp_path), count=count)


@pytest.mark.parametrize('which', [1, 2])
def test_no_existing_output_or_report_overwrite(tmp_path, which):
    paths = inputs(tmp_path)
    paths[which].write_bytes(b'keep exactly')
    with pytest.raises(ValueError, match='overwrite'):
        validate_paths(*paths)
    assert paths[which].read_bytes() == b'keep exactly'


def test_source_output_alias_and_reference_alias_rejected(tmp_path):
    source, output, report = inputs(tmp_path)
    with pytest.raises(ValueError, match='distinct'):
        validate_paths(source, source.parent / '.' / source.name, report)
    with pytest.raises(ValueError, match='distinct'):
        validate_paths(source, output, report, reference=source)


def test_paths_reject_protected_directory_and_missing_parents(tmp_path):
    source, _, report = inputs(tmp_path)
    approved = tmp_path / 'approved-v2'
    approved.mkdir()
    with pytest.raises(ValueError, match='approved'):
        validate_paths(source, approved / 'new.blend', report)
    with pytest.raises(ValueError, match='parents'):
        validate_paths(source, tmp_path / 'absent' / 'new.blend', report)


def target(name='mesh', data=None):
    return SimpleNamespace(name=name, data=data or SimpleNamespace(library=None), library=None,
                           override_library=None, is_editable=True, mode='OBJECT', modifiers=[])


@pytest.mark.parametrize('field,value', [('library', 'external'), ('override_library', 'override'),
                                        ('is_editable', False), ('mode', 'EDIT'),
                                        ('modifiers', ['existing'])])
def test_target_guard_rejects_unsupported_source(field, value):
    obj = target()
    setattr(obj, field, value)
    with pytest.raises(ValueError):
        validate_targets([obj], [obj], 1)


def test_linked_mesh_data_guard():
    obj = target(data=SimpleNamespace(library='external'))
    with pytest.raises(ValueError, match='Linked'):
        validate_targets([obj], [obj], 1)


def test_shared_data_outside_target_fails_but_all_target_users_allowed():
    first = target('first')
    second = target('second', first.data)
    with pytest.raises(ValueError, match='untargeted'):
        validate_targets([first], [first, second], 1)
    validate_targets([first, second], [first, second], 2)


def test_wrong_scene_mesh_count_fails_closed():
    obj = target()
    with pytest.raises(ValueError, match='count'):
        validate_targets([obj], [obj], 16)

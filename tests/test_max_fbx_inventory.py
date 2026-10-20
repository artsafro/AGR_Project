"""FBX inventory tests use actual container bytes, never a running DCC."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
import types

import pytest

_SOURCE = Path(__file__).resolve().parents[1] / "technical_library/max_texture_linker/fbx_inventory.py"
_SPEC = importlib.util.spec_from_file_location("npm_fbx_inventory", _SOURCE)
inv = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(inv)


def test_standalone_script_embeds_current_reader():
    import base64
    import re
    script = (_SOURCE.parent / "NPM_Texture_Linker.ms").read_text(encoding="utf-8-sig")
    match = re.search(r'^AGR_NPMFbx_Payload = "([A-Za-z0-9+/=]+)"$', script, re.M)
    assert match is not None
    assert base64.b64decode(match[1], validate=True) == _SOURCE.read_bytes()


def ascii_fbx(names=("SM_Test_Main",), kind="Mesh"):
    models = "\n".join(f'Model: {i}, "Model::{name}", "{kind}" {{}}' for i, name in enumerate(names, 1))
    return ('; FBX 7.4.0 project file\nFBXHeaderExtension: { FBXVersion: 7400 }\nObjects: {\n' + models + '\n}\n').encode()


def binary_fbx(version=7400, names=("SM_Test_Main",)):
    wide = version >= 7500
    fmt = "<QQQB" if wide else "<IIIB"
    header_size = struct.calcsize(fmt)

    def string(value):
        data = value.encode()
        return b"S" + struct.pack("<I", len(data)) + data

    def model(start, number, name, kind):
        props = b"L" + struct.pack("<q", number) + string(name + "\x00\x01Model") + string(kind)
        end = start + header_size + 5 + len(props)
        return struct.pack(fmt, end, 3, len(props), 5) + b"Model" + props

    start = 27 + header_size + len(b"Objects")
    children = b""
    for i, name in enumerate(names):
        child = model(start + len(children), i + 1, name, "Mesh")
        children += child
    children += model(start + len(children), 99, "Ignored", "Null")
    children += bytes(header_size)
    root = struct.pack(fmt, start + len(children), 0, 0, 7) + b"Objects" + children
    return inv._MAGIC + struct.pack("<I", version) + root + bytes(header_size)


@pytest.mark.parametrize("version", [7400, 7500, 7700])
def test_binary_versions_and_nonmesh(version):
    assert inv._mesh_names(binary_fbx(version)) == (version, ["SM_Test_Main"])


def test_ascii_names_and_nonmesh():
    data = ascii_fbx(("Корпус_А",)).replace(b"\n}\n", b'\nModel: 50, "Model::Camera", "Camera" {}\n}\n')
    assert inv._mesh_names(data) == (7400, ["Корпус_А"])


@pytest.mark.parametrize("names", [("A", "a"), ("STRASSE", "Straße"), ("",)])
@pytest.mark.parametrize("binary", [False, True])
def test_invalid_mesh_names(names, binary):
    with pytest.raises(ValueError):
        inv._mesh_names(binary_fbx(names=names) if binary else ascii_fbx(names))


@pytest.mark.parametrize("version", [7400, 7500])
def test_binary_truncation_and_corrupt_offsets(version):
    data = binary_fbx(version)
    for cut in (0, 20, 26, 30, len(data) - 1, len(data) - 20):
        with pytest.raises((ValueError, UnicodeError)):
            inv._mesh_names(data[:cut])
    damaged = bytearray(data)
    struct.pack_into("<Q" if version >= 7500 else "<I", damaged, 27, len(data) + 100)
    with pytest.raises(ValueError, match="offset"):
        inv._mesh_names(bytes(damaged))


def test_binary_property_count_length_and_unknown_type():
    data = bytearray(binary_fbx())
    model_offset = 27 + 13 + 7
    struct.pack_into("<I", data, model_offset + 4, 4)
    with pytest.raises(ValueError):
        inv._mesh_names(bytes(data))
    data = bytearray(binary_fbx())
    data[model_offset + 13 + 5] = ord("Z")
    with pytest.raises(ValueError, match="property type"):
        inv._mesh_names(bytes(data))


@pytest.mark.parametrize("data", [b"not an FBX", ascii_fbx()[:-2], ascii_fbx().replace(b'"Mesh" {}', b'"Mesh" {'), ascii_fbx().replace(b'"Mesh"', b'"Mesh')])
def test_invalid_ascii(data):
    with pytest.raises(ValueError):
        inv._mesh_names(data)


def test_ascii_nesting_limit():
    with pytest.raises(ValueError, match="nesting"):
        inv._mesh_names(b"FBXVersion: 7400\n" + b"{" * 130 + b"}" * 130)


def test_ascii_fake_model_inside_multiline_string_is_not_inventory():
    fake = b'Note: "text\nModel: 20, \\"Model::Bogus\\", \\"Mesh\\" {}\n"\n'
    assert inv._mesh_names(ascii_fbx() + fake)[1] == ["SM_Test_Main"]


def make_source(tmp_path):
    source = tmp_path / "nested" / "building.FBX"
    source.parent.mkdir()
    source.write_bytes(ascii_fbx())
    return source


def write_inventory(tmp_path, payload):
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_recursive_scan_hashes_ignore_outputs_and_no_source_mutation(tmp_path):
    source = make_source(tmp_path)
    before = source.read_bytes()
    ignored = tmp_path / "NPM_FBX_20261016"
    ignored.mkdir()
    (ignored / "broken.fbx").write_bytes(b"deliberately invalid")
    payload = inv.analyze_folder(tmp_path)
    assert len(payload["files"]) == 1
    item = payload["files"][0]
    assert item["relative_path"] == "nested/building.FBX"
    assert item["size"] == len(before)
    assert item["sha256"] == inv.hashlib.sha256(before).hexdigest()
    saved = inv.save_inventory(tmp_path)
    assert inv.validate_inventory(saved) == payload
    second = inv.save_inventory(tmp_path)
    assert saved != second and Path(saved).is_file()
    assert source.read_bytes() == before


def test_hash_drift_and_inventory_name_tampering(tmp_path):
    source = make_source(tmp_path)
    payload = inv.analyze_folder(tmp_path)
    path = write_inventory(tmp_path, payload)
    source.write_bytes(ascii_fbx(("Changed",)))
    with pytest.raises(ValueError, match="source changed"):
        inv.validate_inventory(path)
    source.write_bytes(ascii_fbx())
    payload["files"][0]["mesh_names"] = ["Forged"]
    path = write_inventory(tmp_path, payload)
    with pytest.raises(ValueError, match="inventory mismatch"):
        inv.validate_inventory(path)


@pytest.mark.parametrize("relative", ["../escape.fbx", "/absolute.fbx", "C:/escape.fbx", "nested/../building.fbx", "nested\\building.FBX", "nested//building.FBX", "nested/building.FBX.", "NPM_FBX_output/model.fbx"])
def test_reject_unsafe_inventory_paths(tmp_path, relative):
    make_source(tmp_path)
    payload = inv.analyze_folder(tmp_path)
    payload["files"][0]["relative_path"] = relative
    with pytest.raises(ValueError, match="[Uu]nsafe"):
        inv.validate_inventory(write_inventory(tmp_path, payload))


def test_duplicate_paths_and_absolute_path_mismatch(tmp_path):
    make_source(tmp_path)
    payload = inv.analyze_folder(tmp_path)
    duplicate = copy.deepcopy(payload["files"][0])
    duplicate["relative_path"] = duplicate["relative_path"].upper()
    payload["files"].append(duplicate)
    with pytest.raises(ValueError, match="Duplicate inventory path"):
        inv.validate_inventory(write_inventory(tmp_path, payload))
    payload["files"].pop()
    payload["files"][0]["path"] = str(tmp_path / "other.fbx")
    with pytest.raises(ValueError, match="absolute path mismatch"):
        inv.validate_inventory(write_inventory(tmp_path, payload))


def test_symlink_skipped_on_scan_and_rejected_on_load(tmp_path):
    source = make_source(tmp_path)
    link = tmp_path / "linked.fbx"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Symlink creation unavailable")
    payload = inv.analyze_folder(tmp_path)
    assert len(payload["files"]) == 1
    payload["files"][0]["relative_path"] = "linked.fbx"
    payload["files"][0]["path"] = str(link)
    with pytest.raises(ValueError, match="Linked"):
        inv.validate_inventory(write_inventory(tmp_path, payload))


def test_duplicate_json_keys(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version": 1, "schema_version": 1}')
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        inv.validate_inventory(path)


def test_pymxs_bridge_success_and_error_clear_jobs(tmp_path, monkeypatch):
    source = tmp_path / "nested/1234_Test_Address_01.fbx"
    source.parent.mkdir()
    source.write_bytes(binary_fbx(names=("SM_Test_Address_001_Main",)))
    workspace = tmp_path / "NPM_FBX_workspace"
    workspace.mkdir()
    class Runtime:
        AGR_NPMFbx_SourceRoot = str(tmp_path)
        AGR_NPMFbx_Workspace = str(workspace)
        AGR_NPMFbx_JsonPath = ""
        AGR_NPMFbx_Error = ""
        AGR_NPMFbx_Jobs = None

        @staticmethod
        def Array(*values):
            return list(values)

    runtime = Runtime()
    monkeypatch.setitem(sys.modules, "pymxs", types.SimpleNamespace(runtime=runtime))
    inv.agr_npm_fbx_analyze()
    assert runtime.AGR_NPMFbx_Error == ""
    assert runtime.AGR_NPMFbx_Jobs == [["nested/1234_Test_Address_01.fbx", ["SM_Test_Address_001_Main"]]]
    assert Path(runtime.AGR_NPMFbx_JsonPath).is_file()
    assert Path(runtime.AGR_NPMFbx_JsonPath).parent == workspace
    source.write_bytes(binary_fbx(names=("SM_Changed_001_Main",)))
    inv.agr_npm_fbx_load()
    assert "source changed" in runtime.AGR_NPMFbx_Error
    assert runtime.AGR_NPMFbx_Jobs == []


def test_export_verification_receipt_and_nooverwrite(tmp_path):
    make_source(tmp_path)
    inventory = inv.save_inventory(tmp_path)
    output = tmp_path / "NPM_FBX_result"
    (output / "nested").mkdir(parents=True)
    target = output / "nested/building.FBX"
    target.write_bytes(binary_fbx(7500, ("sm_test_main",)))
    report = inv.verify_exports(inventory, output)
    assert report["verified"] and not report["native_geometry_verified"]
    assert report["verification_scope"] == "mesh_membership_only"
    assert report["files"][0]["output_sha256"] == inv.hashlib.sha256(target.read_bytes()).hexdigest()
    assert json.loads((output / "export_report.json").read_text())["verified"]
    with pytest.raises(FileExistsError):
        inv.verify_exports(inventory, output)


@pytest.mark.parametrize("names", [("Wrong",), ("SM_Test_Main", "Extra")])
def test_export_verification_rejects_wrong_membership(tmp_path, names):
    make_source(tmp_path)
    inventory = inv.save_inventory(tmp_path)
    output = tmp_path / "NPM_FBX_result"
    (output / "nested").mkdir(parents=True)
    (output / "nested/building.FBX").write_bytes(ascii_fbx(names))
    with pytest.raises(ValueError, match="membership mismatch"):
        inv.verify_exports(inventory, output)
    assert not (output / "export_report.json").exists()


def test_export_verification_rejects_missing_empty_and_source_root(tmp_path):
    make_source(tmp_path)
    inventory = inv.save_inventory(tmp_path)
    output = tmp_path / "NPM_FBX_result"
    output.mkdir()
    with pytest.raises(FileNotFoundError):
        inv.verify_exports(inventory, output)
    (output / "nested").mkdir()
    (output / "nested/building.FBX").write_bytes(b"")
    with pytest.raises(ValueError, match="Empty export"):
        inv.verify_exports(inventory, output)
    with pytest.raises(ValueError, match="differ from source"):
        inv.verify_exports(inventory, tmp_path)


def test_npm_candidate_oks_ground_workspace_and_hashes(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    oks = nested / "1234_Test_Address_20.fbx"
    oks.write_bytes(binary_fbx(names=("SM_Test_Address_001_Main", "SM_Test_Address_020_MainGlass")))
    ground = nested / "1234_Test_Address_Ground.fbx"
    ground.write_bytes(binary_fbx(names=("SM_Test_Address_Ground",)))
    hashes = {p: p.read_bytes() for p in (oks, ground)}
    output = tmp_path / "NPM_FBX_workspace"
    output.mkdir()
    (output / "not_a_source.fbx").write_bytes(b"invalid ignored output")
    inventory = inv.save_inventory(tmp_path, output_dir=output, npm_only=True)
    assert Path(inventory).parent == output
    payload = inv.validate_inventory(inventory, npm_only=True)
    assert len(payload["files"]) == 2
    assert payload["selection_scope"] == "npm_naming_binary7400_candidates_only"
    assert payload["full_npm_verified"] is False
    assert payload["skipped"] == []
    assert all(p.read_bytes() == data for p, data in hashes.items())
    assert not list(tmp_path.glob("*.json"))


@pytest.mark.parametrize("filename,version,names,ascii_data", [
    ("plain.fbx", 7400, ("SM_Test_001_Main",), False),
    ("123_Test_01.fbx", 7400, ("SM_Test_001_Main",), False),
    ("1234_Test-Address_01.fbx", 7400, ("SM_Test_001_Main",), False),
    ("1234_Test_00.fbx", 7400, ("SM_Test_001_Main",), False),
    ("1234_Test_21.fbx", 7400, ("SM_Test_001_Main",), False),
    ("1234_Test_01.fbx", 7500, ("SM_Test_001_Main",), False),
    ("1234_Test_01.fbx", 7400, ("SM_Other_001_Main",), False),
    ("1234_Test_01.fbx", 7400, ("SM_Test_000_Main",), False),
    ("1234_Test_01.fbx", 7400, ("SM_Test_021_Main",), False),
    ("1234_Test_01.fbx", 7400, ("SM_Test_001_MainGlass01",), False),
    ("1234_Test_Ground.fbx", 7400, ("SM_Test_001_Main",), False),
    ("1234_Test_01.fbx", 7400, ("SM_Test_Ground",), False),
    ("1234_Test_01.fbx", 7400, (), False),
    ("1234_Test_01.fbx", 7400, ("SM_Test_001_Main",), True),
])
def test_npm_filter_records_each_rejected_candidate(tmp_path, filename, version, names, ascii_data):
    good = tmp_path / "1234_Valid_01.fbx"
    good.write_bytes(binary_fbx(names=("SM_Valid_001_Main",)))
    bad = tmp_path / filename
    bad.write_bytes(ascii_fbx(names) if ascii_data else binary_fbx(version, names))
    payload = inv.analyze_folder(tmp_path, npm_only=True)
    assert len(payload["files"]) == 1
    assert payload["skipped"][0]["relative_path"] == filename
    assert payload["skipped"][0]["reason"]


def test_npm_filter_malformed_skip_and_zero_candidates(tmp_path):
    bad = tmp_path / "1234_Test_01.fbx"
    bad.write_bytes(binary_fbx()[:-8])
    with pytest.raises(ValueError, match="rejected FBX: 1"):
        inv.analyze_folder(tmp_path, npm_only=True)
    good = tmp_path / "1234_Valid_Ground.fbx"
    good.write_bytes(binary_fbx(names=("SM_Valid_Ground",)))
    payload = inv.analyze_folder(tmp_path, npm_only=True)
    assert len(payload["skipped"]) == 1
    with pytest.raises(ValueError):
        inv.analyze_folder(tmp_path)


def test_npm_load_rejects_legacy_inventory_with_invalid_candidate(tmp_path):
    make_source(tmp_path)
    path = inv.save_inventory(tmp_path)
    assert inv.validate_inventory(path)
    with pytest.raises(ValueError, match="binary FBX"):
        inv.validate_inventory(path, npm_only=True)


def test_npm_inventory_requires_separate_real_workspace(tmp_path):
    source = tmp_path / "1234_Test_01.fbx"
    source.write_bytes(binary_fbx(names=("SM_Test_001_Main",)))
    with pytest.raises(ValueError, match="separate output"):
        inv.save_inventory(tmp_path, npm_only=True)
    with pytest.raises(ValueError, match="differ"):
        inv.save_inventory(tmp_path, output_dir=tmp_path, npm_only=True)
    with pytest.raises(ValueError, match="real directory"):
        inv.save_inventory(tmp_path, output_dir=tmp_path / "missing", npm_only=True)


def test_npm_max_stem_length_and_read_errors_abort(tmp_path, monkeypatch):
    # Direct candidate gate avoids filesystem component-length constraints.
    data = binary_fbx(names=("SM_Test_001_Main",))
    with pytest.raises(ValueError, match="max stem 254"):
        inv._npm_candidate(Path("1234_" + "A" * 250 + "_01.fbx"), data, 7400, ["SM_Test_001_Main"])
    source = tmp_path / "1234_Test_01.fbx"
    source.write_bytes(data)
    def denied(path):
        raise PermissionError("fixture denied")
    monkeypatch.setattr(inv, "_read_source", denied)
    with pytest.raises(PermissionError, match="fixture denied"):
        inv.analyze_folder(tmp_path, npm_only=True)

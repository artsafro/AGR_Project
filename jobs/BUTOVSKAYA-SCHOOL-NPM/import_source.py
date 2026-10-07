"""Import a Revit FBX reference in a fresh, background Blender process.

blender --background --factory-startup --disable-autoexec --python-exit-code 1
  --python import_source.py -- --source source.fbx --sidecar source.json
  --output new-reference-directory

This creates a measured reference, not a modeled/accepted NPM BODY. Full FBX
names are parsed before Blender's name shortening; ambiguous mappings stay
explicit. Geometry, matrices, materials and hierarchy remain as imported.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

import bpy
import numpy as np
from io_scene_fbx import import_fbx, parse_fbx


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def property_value(parent, name):
    props = next((e for e in parent.elems if e.id == b"Properties70"), None)
    if props:
        entry = next((e for e in props.elems if e.id == b"P" and e.props[0] == name), None)
        if entry and len(entry.props) > 4:
            return entry.props[4]
    return None


def parse_source_names(path):
    root, version = parse_fbx.parse(str(path))
    objects = next(e for e in root.elems if e.id == b"Objects")
    rows = []
    for element in objects.elems:
        if element.id != b"Model":
            continue
        raw = element.props[1].split(b"\x00\x01")[0]
        name = raw.decode("utf-8", "replace")
        rows.append({
            "fbx_id": int(element.props[0]),
            "full_name": name,
            "blender_name": import_fbx.validate_blend_names(raw),
            "revit_id_candidates": re.findall(r"\[(\d+)\]", name),
            "element_kind": element.props[2].decode("utf-8", "replace"),
        })
    settings = next((e for e in root.elems if e.id == b"GlobalSettings"), None)
    units = {name: property_value(settings, name.encode()) if settings else None
             for name in ("UnitScaleFactor", "OriginalUnitScaleFactor", "UpAxis",
                          "UpAxisSign", "FrontAxis", "FrontAxisSign", "CoordAxis", "CoordAxisSign")}
    return rows, version, units


def object_record(obj, names, sidecar_elements):
    matches = names.get(obj.name, [])
    # Blender may append .001 when several FBX Models share one name. Retain
    # every candidate instead of silently assigning the suffix to a source ID.
    if not matches:
        base = re.sub(r"\.\d{3,}$", "", obj.name)
        matches = names.get(base, [])
    row = {
        "name": obj.name, "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "collections": [c.name for c in obj.users_collection],
        "matrix_world": [list(r) for r in obj.matrix_world],
        "source_models": matches,
        "source_mapping_status": "unique" if len(matches) == 1 else "ambiguous" if matches else "unmatched",
        "revit_id_candidates": sorted({v for m in matches for v in m["revit_id_candidates"]}),
    }
    candidates = row["revit_id_candidates"]
    source_instances = sidecar_elements.get(candidates[0], []) if len(candidates) == 1 and len(matches) == 1 else []
    if len(source_instances) == 1:
        source_instance = source_instances[0]
        obj["revit_element_id"] = str(source_instance["elementId"])
        for key in ("type", "category", "family", "uniqueId", "level"):
            value = source_instance.get(key)
            if value is not None:
                obj["revit_" + key] = str(value)
        row["sidecar_mapping_status"] = "unique"
        row["revit_metadata"] = {key: source_instance.get(key) for key in
                                 ("elementId", "uniqueId", "category", "family", "type", "materials", "level", "boundingBox")}
        row["revit_bbox_units"] = "feet"
    else:
        row["sidecar_mapping_status"] = "ambiguous" if source_instances else "unmatched"
    if obj.type != "MESH":
        return row
    mesh = obj.data
    coords = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", coords)
    coords = coords.reshape((-1, 3))
    matrix = np.asarray(obj.matrix_world, dtype=np.float64)
    world = coords @ matrix[:3, :3].T + matrix[:3, 3]
    mesh.calc_loop_triangles()
    row.update({
        "mesh": mesh.name,
        "vertices": len(mesh.vertices), "edges": len(mesh.edges),
        "faces": len(mesh.polygons), "triangles": len(mesh.loop_triangles),
        "face_degrees": dict(Counter(str(len(p.vertices)) for p in mesh.polygons)),
        "world_bbox_min": world.min(axis=0).tolist() if len(world) else None,
        "world_bbox_max": world.max(axis=0).tolist() if len(world) else None,
        "materials": [m.name if m else None for m in mesh.materials],
        "material_face_counts": dict(Counter(str(p.material_index) for p in mesh.polygons)),
        "uv_layers": [layer.name for layer in mesh.uv_layers],
        "geometry_location": "SOURCE_REFERENCE.blend:" + mesh.name,
    })
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if not bpy.app.background:
        raise RuntimeError("Run only in a separate background Blender process; live-scene use is forbidden")
    source, sidecar, output = [p.resolve() for p in (args.source, args.sidecar, args.output)]
    if source.suffix.lower() != ".fbx" or not source.is_file() or not sidecar.is_file():
        raise ValueError("Existing FBX and sidecar JSON inputs are required")
    sidecar_data = json.loads(sidecar.read_text(encoding="utf-8-sig"))
    sidecar_elements = defaultdict(list)
    for group in sidecar_data.get("types", []):
        for instance in group.get("instances", []):
            sidecar_elements[str(instance["elementId"])].append(instance)
    input_hashes = {"fbx": sha256(source), "sidecar": sha256(sidecar)}
    full_names, fbx_version, fbx_units = parse_source_names(source)
    names = defaultdict(list)
    for row in full_names:
        names[row["blender_name"]].append(row)
    output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source), use_image_search=False, use_custom_props=True)
    records = [object_record(obj, names, sidecar_elements) for obj in bpy.context.scene.objects]
    if not any(r["type"] == "MESH" and r["vertices"] for r in records):
        raise RuntimeError("FBX imported no nonempty mesh; preserve output directory as failure evidence")
    blend = output / "SOURCE_REFERENCE.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    if input_hashes != {"fbx": sha256(source), "sidecar": sha256(sidecar)}:
        raise RuntimeError("Source input changed during import")
    inventory = {
        "stage": "source_reference", "produced": True,
        "geometry_checks_passed": False, "visual_acceptance": "pending", "delivery_passed": False,
        "blender_version": bpy.app.version_string, "fbx_version": fbx_version,
        "source": str(source), "sidecar": str(sidecar), "input_sha256": input_hashes,
        "blend": str(blend), "blend_sha256": sha256(blend),
        "fbx_global_settings": fbx_units,
        "scene_units": {"system": bpy.context.scene.unit_settings.system,
                        "scale_length": bpy.context.scene.unit_settings.scale_length},
        "unit_note": "World coordinates are imported Blender units. Verify FBX units and source control distances before treating them as metres.",
        "sidecar_top_level_keys": sorted(sidecar_data) if isinstance(sidecar_data, dict) else None,
        "totals": {"objects": len(records), "meshes": sum(r["type"] == "MESH" for r in records),
                   **{key: sum(r.get(key, 0) for r in records) for key in ("vertices", "faces", "triangles")}},
        "source_mapping_counts": dict(Counter(r["source_mapping_status"] for r in records)),
        "sidecar_mapping_counts": dict(Counter(r["sidecar_mapping_status"] for r in records)),
        "fbx_models": full_names, "objects": records,
        "limitations": ["Canonical sidecar metadata is assigned only where a unique full FBX name has exactly one ID candidate and sidecar instance.",
                        "Duplicate source names are ambiguous; FBX import does not expose model UIDs per Blender object.",
                        "This inventory does not verify facade completeness, topology or dimensional accuracy.",
                        "Native save completed; independent saved-file readback remains required."],
    }
    (output / "inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SOURCE_REFERENCE_SUMMARY", json.dumps({"blend": str(blend), "inventory": str(output / "inventory.json"),
          "totals": inventory["totals"], "mapping": inventory["source_mapping_counts"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()

"""Read an exported FBX in a separate factory-startup Blender process.

Usage: blender -b --factory-startup --python check_fbx.py -- --fbx file --report file.json
This is structural readback, not topology certification or an AGR Checker pass.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy

parser = argparse.ArgumentParser()
parser.add_argument("--fbx", required=True)
parser.add_argument("--report", required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
report = {
    "source": str(Path(args.fbx).resolve()),
    "readback_ok": False,
    "delivery_passed": False,
    "scope": "FBX structural readback only. No AGR, topology/overlap or appearance approval.",
    "meshes": [],
}
try:
    # Standalone factory process only; remove its default cube/camera/light.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(Path(args.fbx).resolve()))
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        points = [obj.matrix_world @ v.co for v in obj.data.vertices]
        if any(not math.isfinite(c) for p in points for c in p):
            raise ValueError("Non-finite vertex coordinates: " + obj.name)
        uv = obj.data.uv_layers.active
        uv_points = [tuple(x.uv) for x in uv.data] if uv else []
        if any(not math.isfinite(c) for p in uv_points for c in p):
            raise ValueError("Non-finite UV: " + obj.name)
        report["meshes"].append({
            "name": obj.name,
            "vertices": len(points),
            "polygons": len(obj.data.polygons),
            "bounds_m": [
                [min(p[i] for p in points) for i in range(3)],
                [max(p[i] for p in points) for i in range(3)],
            ] if points else None,
            "uv_loops": len(uv_points),
            "uv_bounds": [
                [min(p[i] for p in uv_points) for i in range(2)],
                [max(p[i] for p in uv_points) for i in range(2)],
            ] if uv_points else None,
            "materials": [s.material.name if s.material else None for s in obj.material_slots],
        })
    report["readback_ok"] = bool(report["meshes"]) and all(
        m["vertices"] > 0 and m["polygons"] > 0 for m in report["meshes"]
    )
    if not report["readback_ok"]:
        report["error"] = "No non-empty meshes"
except Exception as exc:
    report["error"] = f"{type(exc).__name__}: {exc}"
Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("AGRWB_READBACK", report["readback_ok"])
if not report["readback_ok"]:
    sys.exit(2)


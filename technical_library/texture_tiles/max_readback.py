"""Read a scene loaded by 3dsmaxbatch -sceneFile; never saves or edits it.

Set AGR_MAX_AUDIT_OUTPUT to a new JSON path. Run only in a separate batch process.
The hashes describe evaluated triangle geometry/UV, not editable polygon structure.
"""
import hashlib
import json
import os
from pathlib import Path


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    import pymxs
    rt = pymxs.runtime
    output = Path(os.environ["AGR_MAX_AUDIT_OUTPUT"]).resolve()
    if output.exists():
        raise FileExistsError(output)
    scene = Path(str(rt.maxFilePath)) / str(rt.maxFileName)
    source_hash = hashlib.sha256(scene.read_bytes()).hexdigest()
    # Native loops avoid hundreds of thousands of Python/Max crossings.
    rt.execute('''fn agrAuditMesh n = (
        local m = snapshotAsMesh n
        local g = stringStream "", u = stringStream ""
        for i=1 to m.numverts do format "%\\n" (getVert m i) to:g
        for i=1 to m.numfaces do format "%|%|%\\n" (getFace m i) (getFaceMatID m i) (getFaceSmoothGroup m i) to:g
        for channel=0 to 99 where meshop.getMapSupport m channel do (
            format "channel %\\n" channel to:u
            for i=1 to meshop.getNumMapVerts m channel do format "%\\n" (meshop.getMapVert m channel i) to:u
            for i=1 to meshop.getNumMapFaces m channel do format "%\\n" (meshop.getMapFace m channel i) to:u
        )
        #(g as string, u as string, m.numverts, m.numfaces)
    )''')
    nodes = []
    for n in rt.objects:
        entry = {"name": str(n.name), "class": str(rt.classOf(n)),
                 "hidden": bool(n.isHidden), "layer": str(n.layer.name),
                 "transform": str(n.transform),
                 "material": str(n.material.name) if n.material else None}
        if rt.superClassOf(n) == rt.GeometryClass:
            g, u, nv, nf = rt.agrAuditMesh(n)
            entry.update(geometry_sha256=digest(g), uv_sha256=digest(u), vertices=nv, faces=nf)
        nodes.append(entry)
    maps = []
    for m in rt.getClassInstances(rt.Bitmaptexture):
        path = Path(str(m.filename))
        maps.append({"name": str(m.name), "file": str(path), "exists": path.is_file(),
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None})
    if hashlib.sha256(scene.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Source changed during readback")
    report = {"scene": str(scene), "sha256": source_hash, "max_version": str(rt.maxVersion()),
              "scope": "read-only evaluated triangles/face IDs/smoothing/UV/transform/bitmap files; native point formatting precision limits; no explicit normals or visual acceptance",
              "nodes": sorted(nodes, key=lambda n: n["name"]), "maps": maps}
    with output.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("AGR_MAX_READBACK_OK", len(nodes), len(maps), source_hash)


if __name__ == "__main__":
    main()

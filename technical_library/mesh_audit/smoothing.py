"""Scoped Blender 4.4 smoothing with saved-file preservation readback.

Run with Blender --background --factory-startup --disable-autoexec --python-exit-code 1.
This changes shading only; it does not certify visual or AGR acceptance.
"""
import argparse
import array
import hashlib
import json
import math
import sys
from pathlib import Path


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def validate_paths(source, output, report, reference=None, angle=30, count=16):
    """Reject collisions/overwrites before importing bpy or opening a source."""
    source, output, report = (Path(p).resolve() for p in (source, output, report))
    reference = Path(reference).resolve() if reference else None
    if not math.isfinite(angle) or not 0 < angle < 180:
        raise ValueError('Angle must be finite and strictly between 0 and 180 degrees')
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError('Expected mesh count must be a positive integer')
    if source.suffix.lower() != '.blend' or not source.is_file():
        raise ValueError('Source must be an existing .blend file')
    if reference and (reference.suffix.lower() not in {'.blend', '.blend1'} or not reference.is_file()):
        raise ValueError('Reference must be an existing .blend or .blend1 file')
    if output.suffix.lower() != '.blend' or report.suffix.lower() != '.json':
        raise ValueError('Output must be .blend and report must be .json')
    paths = [source, output, report] + ([reference] if reference else [])
    if len(set(paths)) != len(paths):
        raise ValueError('Source, reference, output and report must be distinct')
    for path in (output, report):
        if path.exists() or path.is_symlink():
            raise ValueError('Refusing overwrite: ' + path.name)
        if any('approved' in part.lower() for part in path.parts):
            raise ValueError('Refusing write to an approved path')
        if not path.parent.is_dir():
            raise ValueError('Output and report parents must already exist')
    return source, output, report, reference


def validate_targets(objects, all_objects, count):
    """No existing modifiers, linked data or sharing beyond targeted scene meshes."""
    if len(objects) != count:
        raise ValueError('Unexpected scene mesh count: ' + str(len(objects)))
    for obj in objects:
        if obj.library or obj.data.library or obj.override_library or not obj.is_editable:
            raise ValueError('Linked, overridden or noneditable mesh: ' + obj.name)
        if obj.mode != 'OBJECT' or obj.modifiers:
            raise ValueError('Mesh must be in Object mode without modifiers: ' + obj.name)
        if any(other.data == obj.data and not any(other == target for target in objects)
               for other in all_objects):
            raise ValueError('Mesh data shared with an untargeted object: ' + obj.name)


def geometry_fingerprint(obj, mesh=None):
    """Original verify_saved.py byte sequence: topology, UV, material slots and TM."""
    mesh = mesh if mesh is not None else obj.data
    digest = hashlib.sha256()
    for values, prop, code, size in [
        (mesh.vertices, 'co', 'f', 3), (mesh.edges, 'vertices', 'i', 2),
        (mesh.loops, 'vertex_index', 'i', 1),
        (mesh.polygons, 'loop_start', 'i', 1),
        (mesh.polygons, 'loop_total', 'i', 1),
        (mesh.polygons, 'material_index', 'i', 1),
    ]:
        buffer = array.array(code, [0]) * (len(values) * size)
        values.foreach_get(prop, buffer)
        digest.update(buffer.tobytes())
    for uv in mesh.uv_layers:
        digest.update(uv.name.encode())
        buffer = array.array('f', [0]) * (len(uv.data) * 2)
        uv.data.foreach_get('uv', buffer)
        digest.update(buffer.tobytes())
    digest.update(repr([list(row) for row in obj.matrix_world]).encode())
    digest.update(repr([s.material.name if s.material else None for s in obj.material_slots]).encode())
    return digest.hexdigest()


def snapshot(bpy):
    return {o.name: geometry_fingerprint(o) for o in bpy.context.scene.objects if o.type == 'MESH'}


def scene_structure(bpy):
    """Supplementary preservation guard: scenes, objects, collections and transforms."""
    return {
        'scenes': {s.name: sorted(o.name for o in s.objects) for s in bpy.data.scenes},
        'collections': {c.name: (sorted(o.name for o in c.objects), sorted(x.name for x in c.children))
                        for c in bpy.data.collections},
        'objects': {o.name: (o.type, o.data.name if o.data else None,
                           o.parent.name if o.parent else None,
                           [list(row) for row in o.matrix_world],
                           o.hide_render, o.hide_viewport)
                    for o in bpy.data.objects},
    }


def load_smoothing_asset(bpy, asset_library=None):
    asset = Path(asset_library) if asset_library else (
        Path(bpy.utils.resource_path('LOCAL')) / 'datafiles/assets/geometry_nodes/smooth_by_angle.blend')
    if not asset.is_file():
        raise ValueError('Installed Smooth by Angle asset missing; supply --asset-library explicitly')
    with bpy.data.libraries.load(str(asset), link=False) as (available, loaded):
        if 'Smooth by Angle' not in available.node_groups:
            raise ValueError('Asset library has no Smooth by Angle node group')
        loaded.node_groups = ['Smooth by Angle']
    group = loaded.node_groups[0]
    sockets = {s.identifier: s for s in group.interface.items_tree if s.item_type == 'SOCKET'}
    if not {'Input_1', 'Socket_1'} <= sockets.keys():
        raise ValueError('Unexpected Blender 4.4 Smooth by Angle interface')
    return group, file_hash(asset)


def apply(bpy, objects, angle, group):
    for obj in objects:
        if obj.data.has_custom_normals:
            with bpy.context.temp_override(object=obj, active_object=obj,
                                           selected_objects=[obj], selected_editable_objects=[obj]):
                result = bpy.ops.mesh.customdata_custom_splitnormals_clear()
            if 'FINISHED' not in result:
                raise RuntimeError('Custom normals clear failed: ' + obj.name)
        for edge in obj.data.edges:
            edge.use_edge_sharp = False
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        modifier = obj.modifiers.new('Smooth by Angle', 'NODES')
        modifier.node_group = group
        modifier['Input_1'] = math.radians(angle)
        modifier['Socket_1'] = False
        obj.data.update()
    bpy.context.view_layer.update()


def verify(bpy, expected, angle):
    if snapshot(bpy) != expected:
        raise RuntimeError('Raw geometry/UV/material assignments/transforms changed')
    graph = bpy.context.evaluated_depsgraph_get()
    result = {}
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        if mesh.has_custom_normals or any(e.use_edge_sharp for e in mesh.edges):
            raise RuntimeError('Custom normals or base sharp flags remain: ' + obj.name)
        if not all(p.use_smooth for p in mesh.polygons) or len(obj.modifiers) != 1:
            raise RuntimeError('Unexpected smooth flags/modifier count: ' + obj.name)
        modifier = obj.modifiers[0]
        if (modifier.type != 'NODES' or not modifier.node_group or
                not math.isclose(modifier.get('Input_1', -1), math.radians(angle), abs_tol=1e-6) or
                modifier.get('Socket_1') != False or not modifier.show_viewport or not modifier.show_render):
            raise RuntimeError('Unexpected smoothing modifier: ' + obj.name)
        evaluated = obj.evaluated_get(graph)
        evaluated_mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=graph)
        try:
            if geometry_fingerprint(obj, evaluated_mesh) != expected[obj.name]:
                raise RuntimeError('Evaluated geometry/UV/material assignments changed: ' + obj.name)
            # Include flags and loop normals: counts alone cannot establish shading equivalence.
            digest = hashlib.sha256()
            for values, prop, code, width in [
                (evaluated_mesh.edges, 'use_edge_sharp', 'b', 1),
                (evaluated_mesh.polygons, 'use_smooth', 'b', 1),
                (evaluated_mesh.corner_normals, 'vector', 'f', 3),
            ]:
                buffer = array.array(code, [0]) * (len(values) * width)
                values.foreach_get(prop, buffer)
                digest.update(buffer.tobytes())
            result[obj.name] = {'geometry_sha256': expected[obj.name],
                                'evaluated_shading_sha256': digest.hexdigest(),
                                'evaluated_sharp_edges': sum(e.use_edge_sharp for e in evaluated_mesh.edges),
                                'faces': len(mesh.polygons)}
        finally:
            evaluated.to_mesh_clear()
    return result


def run(source, output, report, reference=None, angle=30, count=16, asset_library=None):
    source, output, report, reference = validate_paths(source, output, report, reference, angle, count)
    import bpy
    if bpy.app.version[:2] != (4, 4):
        raise ValueError('Only Blender 4.4 is supported by this scoped transfer')
    source_sha = file_hash(source)
    reference_sha = file_hash(reference) if reference else None
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    validate_targets(objects, list(bpy.data.objects), count)
    baseline, structure = snapshot(bpy), scene_structure(bpy)
    group, asset_sha = load_smoothing_asset(bpy, asset_library)
    apply(bpy, objects, angle, group)
    checks = verify(bpy, baseline, angle)
    if scene_structure(bpy) != structure:
        raise RuntimeError('Scene structure changed')
    # Compare historical success before writing a new deliverable.
    if reference:
        bpy.ops.wm.open_mainfile(filepath=str(reference), load_ui=False, use_scripts=False)
        if verify(bpy, baseline, angle) != checks:
            raise RuntimeError('Historical output differs from transferred shading/geometry')
        bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        validate_targets(objects, list(bpy.data.objects), count)
        group, asset_sha = load_smoothing_asset(bpy, asset_library)
        apply(bpy, objects, angle, group)
        if verify(bpy, baseline, angle) != checks or scene_structure(bpy) != structure:
            raise RuntimeError('Replay differs before save')
    if file_hash(source) != source_sha or (reference and file_hash(reference) != reference_sha):
        raise RuntimeError('Protected input changed')
    # Recheck collision immediately before saving. No overwrite or .blend1 history.
    validate_paths(source, output, report, reference, angle, count)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), relative_remap=False)
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    if snapshot(bpy) != baseline or scene_structure(bpy) != structure:
        raise RuntimeError('Saved source readback mismatch')
    bpy.ops.wm.open_mainfile(filepath=str(output), load_ui=False, use_scripts=False)
    if verify(bpy, baseline, angle) != checks or scene_structure(bpy) != structure:
        raise RuntimeError('Saved output readback mismatch')
    if file_hash(source) != source_sha or (reference and file_hash(reference) != reference_sha):
        raise RuntimeError('Protected input changed during readback')
    evidence = {'blender_version': bpy.app.version_string, 'source_sha256': source_sha,
                'output_sha256': file_hash(output), 'asset_sha256': asset_sha,
                'reference_sha256': reference_sha, 'reference_equivalent': True if reference else None,
                'angle_degrees': angle, 'mesh_count': count, 'source_unchanged': True,
                'saved_source_output_invariants_equal': True, 'native_checks_passed': True,
                'objects': checks, 'visual_acceptance': 'pending', 'user_acceptance': 'pending',
                'full_agr_acceptance': 'pending', 'delivery_passed': False,
                'scope': 'Blender 4.4 local meshes without prior modifiers; shading-only operation'}
    with report.open('x', encoding='utf-8') as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2)
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--asset-library', type=Path)
    parser.add_argument('--expected-mesh-count', type=int, default=16)
    parser.add_argument('--angle', type=float, default=30)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
    run(args.source, args.output, args.report, args.reference, args.angle,
        args.expected_mesh_count, args.asset_library)


if __name__ == '__main__':
    main()

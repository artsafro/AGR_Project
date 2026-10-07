"""Read-only candidate vertical surfaces and sampled wall occlusion; no automatic selection."""
import argparse
import json
import hashlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def main():
    parser = argparse.ArgumentParser()
    for name in ('reference', 'inventory', 'selection', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--minimum-plane-area', type=float, default=.000001)
    parser.add_argument('--maximum-vertical-normal-z',type=float,default=.00001)
    parser.add_argument('--vertical-projection-tolerance-m',type=float,default=.002)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not bpy.app.background:
        raise RuntimeError('Separate background Blender required; live app use forbidden')
    if not np.isfinite(args.maximum_vertical_normal_z) or not 0<args.maximum_vertical_normal_z<=.001:
        raise ValueError('Near-vertical angular limit must be between zero and0.001')
    if not np.isfinite(args.vertical_projection_tolerance_m) or not 0<args.vertical_projection_tolerance_m<=.002:
        raise ValueError('Measured vertical projection bound must not exceed2mm')
    output = Path(args.output)
    if output.exists():
        raise RuntimeError('Fresh output directory required')
    inventory = json.loads(Path(args.inventory).read_text(encoding='utf-8'))
    selection = json.loads(Path(args.selection).read_text(encoding='utf-8'))
    selected = {int(x['id']): x['type'] for x in selection['elements']}
    wall_ids = {int(o['revit_metadata']['elementId']) for o in inventory['objects']
                if o.get('revit_metadata', {}).get('category') == 'Стены'}
    bpy.ops.wm.open_mainfile(filepath=args.reference)
    vertices, triangles, triangle_ids = [], [], []
    objects = {}
    for obj in bpy.context.scene.objects:
        element_id = int(obj.get('revit_element_id', -1))
        if obj.type != 'MESH' or element_id not in wall_ids:
            continue
        local = np.array([tuple(v.co) for v in obj.data.vertices], dtype=np.float64)
        matrix = np.array(obj.matrix_world, dtype=np.float64)
        world = local @ matrix[:3, :3].T + matrix[:3, 3]
        obj.data.calc_loop_triangles()
        faces = [tuple(f.vertices) for f in obj.data.loop_triangles]
        offset = len(vertices)
        vertices.extend(world.tolist())
        triangles.extend(tuple(offset + v for v in f) for f in faces)
        triangle_ids.extend([element_id] * len(faces))
        if element_id in selected:
            if obj.get('revit_type') != selected[element_id]:
                raise RuntimeError('Explicit type/ID contract mismatch: ' + str(element_id))
            objects[element_id] = (obj, world, faces)
    if set(objects) != set(selected):
        raise RuntimeError('Missing explicit source IDs: ' + str(sorted(set(selected) - set(objects))))
    bvh = BVHTree.FromPolygons(vertices, triangles, all_triangles=True)
    epsilon, distance = .005, .65
    barycentrics = np.array([[1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
    planes, tiny, filtered = [], [], []
    for element_id, (obj, world, faces) in sorted(objects.items()):
        groups = defaultdict(list)
        for index, face in enumerate(faces):
            pts = world[list(face)]
            normal = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            magnitude = np.linalg.norm(normal)
            if magnitude < 1e-12:
                continue
            normal /= magnitude
            if abs(normal[2]) > args.maximum_vertical_normal_z:
                filtered.append({'id':element_id,'source_triangle_index':index,'area_m2':float(magnitude/2),
                    'normal':normal.tolist(),'reason':'Outside explicit near-vertical angular contract'})
                continue
            horizontal=normal.copy();horizontal[2]=0;horizontal/=np.linalg.norm(horizontal)
            vertical_d=float(np.median(pts@horizontal))
            vertical_error=float(np.max(abs(pts@horizontal-vertical_d)))
            if vertical_error>args.vertical_projection_tolerance_m:
                filtered.append({'id':element_id,'source_triangle_index':index,'area_m2':float(magnitude/2),
                    'normal':normal.tolist(),'vertical_projection_error_m':vertical_error,
                    'reason':'Measured source triangle cannot project vertically within declared tolerance'})
                continue
            d = float(normal @ pts[0])
            key = tuple(round(float(v), 5) for v in normal) + (round(d, 4),)
            groups[key].append((index, pts, normal, magnitude / 2, d))
        for key, fragments in groups.items():
            area = sum(x[3] for x in fragments)
            if area < args.minimum_plane_area:
                tiny.append({'id': element_id, 'normal': list(key[:3]), 'd': key[3], 'area_m2': area})
                continue
            clear_area, blockers, back_hits, detailed = 0., Counter(), Counter(), []
            for face_index, pts, normal, face_area, d in fragments:
                samples = []
                clear_count = 0
                for center in barycentrics @ pts:
                    hit, _, hit_index, hit_distance = bvh.ray_cast(Vector(center + normal * epsilon), Vector(normal), distance)
                    obstruction = triangle_ids[hit_index] if hit_index is not None else None
                    if obstruction is None:
                        clear_count += 1
                    else:
                        blockers[obstruction] += face_area / len(barycentrics)
                    _, _, back_index, back_distance = bvh.ray_cast(Vector(center + normal * epsilon), Vector(-normal), distance)
                    back_id = triangle_ids[back_index] if back_index is not None else None
                    _, _, thickness_index, thickness_distance = bvh.ray_cast(Vector(center - normal * epsilon), Vector(-normal), distance)
                    thickness_id = triangle_ids[thickness_index] if thickness_index is not None else None
                    if back_id is not None:
                        back_hits[back_id] += face_area / len(barycentrics)
                    samples.append({'position_m': center.tolist(), 'forward_hit_id': obstruction,
                                    'forward_hit_distance_m': hit_distance if obstruction is not None else None,
                                    'back_hit_id': back_id,
                                    'back_hit_distance_m': back_distance if back_id is not None else None,
                                    'inward_hit_id': thickness_id,
                                    'inward_hit_distance_m': thickness_distance if thickness_id is not None else None,
                                    'same_element_thickness_m': thickness_distance + epsilon if thickness_id == element_id else None})
                clear_area += face_area * clear_count / len(barycentrics)
                detailed.append({'source_triangle_index': face_index, 'points_m': pts.tolist(),
                                 'area_m2': face_area, 'samples': samples, 'clear_fraction': clear_count / len(barycentrics)})
            fraction = clear_area / area
            tangent = np.array([-fragments[0][2][1], fragments[0][2][0], 0.])
            allpts = np.concatenate([x[1] for x in fragments])
            classification = 'sampled_clear' if fraction == 1 else 'sampled_blocked' if fraction == 0 else 'sampled_mixed'
            planes.append({'plane_key': str(element_id) + ':' + ','.join(str(x) for x in key),
                           'revit_element_id': element_id, 'revit_type': selected[element_id],
                           'source_object': obj.name, 'normal': fragments[0][2].tolist(),
                           'plane_d_m': fragments[0][4], 'tangent': tangent.tolist(),
                           't_range_m': [float(min(allpts @ tangent)), float(max(allpts @ tangent))],
                           'z_range_m': [float(min(allpts[:, 2])), float(max(allpts[:, 2]))],
                           'area_m2': area, 'clear_fraction': fraction, 'classification': classification,
                           'forward_obstruction_area_m2': dict(blockers), 'back_hit_area_m2': dict(back_hits),
                           'triangles': detailed, 'material_slots': [m.name if m else None for m in obj.data.materials]})
    output.mkdir(parents=True)
    np.savez_compressed(output / 'wall_geometry.npz',
                        vertices=np.asarray(vertices, dtype=np.float64),
                        triangles=np.asarray(triangles, dtype=np.int64),
                        revit_ids=np.asarray(triangle_ids, dtype=np.int64))
    axes = []
    for element_id in sorted(objects):
        element_planes = [p for p in planes if p['revit_element_id'] == element_id]
        unoriented = defaultdict(float)
        for plane in element_planes:
            n = np.asarray(plane['normal'])
            sign = 1 if n[0] > 1e-6 or (abs(n[0]) <= 1e-6 and n[1] > 0) else -1
            axis_key = tuple(round(float(v), 4) for v in n * sign)
            unoriented[axis_key] += plane['area_m2']
        if not unoriented:
            axes.append({'revit_element_id': element_id, 'classification': 'no_vertical_axis'})
            continue
        principal = max(unoriented, key=unoriented.get)
        directions = {}
        for sign in (1, -1):
            matches = [p for p in element_planes if float(np.dot(p['normal'], principal)) * sign > .99999]
            blockers = Counter()
            for p in matches:
                blockers.update(p['forward_obstruction_area_m2'])
            total = sum(p['area_m2'] for p in matches)
            clear = sum(p['area_m2'] * p['clear_fraction'] for p in matches)
            directions[str(sign)] = {'normal': [v * sign for v in principal], 'surface_area_m2': total,
                                     'sampled_clear_area_m2': clear, 'clear_fraction': clear / total if total else None,
                                     'nearest_blocking_ids_area_m2': dict(blockers)}
        positive, negative = [directions[str(s)]['sampled_clear_area_m2'] for s in (1, -1)]
        classification = ('both_directions_sampled_clear' if positive > 1e-6 and negative > 1e-6 else
                          'zero_directions_sampled_clear' if positive <= 1e-6 and negative <= 1e-6 else
                          'only_positive_sampled_clear' if positive > 1e-6 else 'only_negative_sampled_clear')
        substrate = selected[element_id].startswith(('НР_', 'ADSK_Наружная_'))
        axes.append({'revit_element_id': element_id, 'revit_type': selected[element_id],
                     'principal_unoriented_axis': list(principal), 'summed_axis_surface_area_m2': unoriented[principal],
                     'directions': directions, 'classification': classification,
                     'substrate_direction_requires_finish_coverage': substrate,
                     'selection_warning': 'Direction not selected. For substrates use measured adjacent finish-layer coverage; clear-area maximum can select inner faces.'})
    (output / 'principal_axes.json').write_text(json.dumps(axes, ensure_ascii=False, indent=2), encoding='utf-8')
    report = {'source_reference': str(Path(args.reference).resolve()), 'selection': selection,
              'probe_contract': {'epsilon_m': epsilon, 'max_distance_m': distance, 'samples_per_triangle': 4,
                                 'opaque_obstacles': 'All exported wall triangles including structure/interior',
                                 'limitations': 'Sampled visibility does not prove full exposed contours. No automatic visibility threshold selects planes. Back probes first hit source face; inward probes start inside and report same-element thickness only when the first hit belongs to it. Parts absent from reference mappings.'},
              'wall_obstacle_ids': len(wall_ids), 'bvh_triangles': len(triangles),
              'candidate_planes': planes, 'tiny_planes_below_minimum': tiny,
              'minimum_plane_area_m2': args.minimum_plane_area,
              'source_reference_sha256':hashlib.sha256(Path(args.reference).read_bytes()).hexdigest(),
              'vertical_candidate_contract':{'maximum_abs_source_normal_z':args.maximum_vertical_normal_z,
                  'maximum_measured_vertical_projection_m':args.vertical_projection_tolerance_m,
                  'complete_group_projection_checked_again_by_compositor':True},
              'filtered_source_triangles':filtered}
    (output / 'envelope.json').write_text(json.dumps(report, ensure_ascii=False), encoding='utf-8')
    summary = {'candidate_objects': len(objects), 'candidate_planes': len(planes),
               'classification_counts': dict(Counter(p['classification'] for p in planes)),
               'principal_axis_classification_counts': dict(Counter(p['classification'] for p in axes)),
               'principal_axis_ambiguous_ids': [p['revit_element_id'] for p in axes if p['classification'] in ('both_directions_sampled_clear', 'zero_directions_sampled_clear', 'no_vertical_axis')],
               'tiny_planes': len(tiny), 'output': str(output.resolve())}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()

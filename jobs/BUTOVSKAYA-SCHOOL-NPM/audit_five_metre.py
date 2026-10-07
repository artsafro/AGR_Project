"""Audit saved BODY and measured source silhouettes in Revit-origin 5m cells.

No DCC imports, source mutation, or master cutting. Cells contain intersections
of original faces; checking an intersection never changes original cardinality.
Requires NumPy/Shapely. --self-test runs synthetic crossing/hole/missing tests.
"""
import argparse
import csv
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon, box, shape
from shapely.affinity import affine_transform

CELL = 5.0
DISTANCE_TOLERANCE = .002
AREA_EPSILON = 1e-10


def areal_geometry(geometry):
    """Cell-edge point/line contacts carry zero facade area, not boundaries."""
    if geometry.geom_type in ('Polygon', 'MultiPolygon'):
        return geometry
    polygons = []
    for part in getattr(geometry, 'geoms', []):
        area = areal_geometry(part)
        if not area.is_empty:
            polygons.append(area)
    return shapely.union_all(polygons) if polygons else Polygon()


def cell_indices(low, high):
    """Closed bbox broad phase; exact intersections establish occupancy."""
    ranges = [range(math.floor(a / CELL), math.floor(b / CELL) + 1)
              for a, b in zip(low, high)]
    return itertools.product(*ranges)


def clip_profile(profile, normal, tangent, depth, cell):
    """Exact intersection of a vertical measured plane with a world 5m cube."""
    lo = np.array(cell, dtype=float) * CELL
    hi = lo + CELL
    umin, umax = -math.inf, math.inf
    for axis in (0, 1):
        coefficient = tangent[axis]
        offset = normal[axis] * depth
        if abs(coefficient) < 1e-12:
            if offset < lo[axis] - 1e-9 or offset > hi[axis] + 1e-9:
                return Polygon()
        else:
            a, b = sorted(((lo[axis] - offset) / coefficient,
                           (hi[axis] - offset) / coefficient))
            umin, umax = max(umin, a), min(umax, b)
    if umin >= umax:
        return Polygon()
    return areal_geometry(profile.intersection(box(umin, lo[2], umax, hi[2])))


def profile_world_bounds(profile, normal, tangent, depth):
    u0, z0, u1, z1 = profile.bounds
    pts = np.array([normal * depth + tangent * u + [0, 0, z]
                    for u in (u0, u1) for z in (z0, z1)])
    return pts.min(axis=0), pts.max(axis=0)


def geometry_check(points, expected_normal):
    if len(points) != 4:
        return {'quad': False, 'convex': False, 'normal': False,
                'planarity_m': None}
    relative = points - points[0]
    area_vector = np.cross(relative, np.roll(relative, -1, axis=0)).sum(axis=0)
    size = np.linalg.norm(area_vector)
    if size < 2 * AREA_EPSILON or not np.isfinite(points).all():
        return {'quad': True, 'convex': False, 'normal': False,
                'planarity_m': None}
    geometric_normal = area_vector / size
    edges = np.roll(points, -1, axis=0) - points
    turns = np.cross(edges, np.roll(edges, -1, axis=0)) @ geometric_normal
    return {'quad': True, 'convex': bool(np.all(turns > 0)),
            'normal': bool(geometric_normal @ expected_normal >= .99999),
            'planarity_m': float(np.max(abs(relative @ geometric_normal)))}


def transform_profile(profile, old_n, old_t, old_d, target_t):
    return affine_transform(profile, [float(old_t @ target_t), 0, 0, 1,
                                      float(old_n @ target_t) * old_d, 0])


def compare_profiles(source, modeled):
    source, modeled = areal_geometry(source), areal_geometry(modeled)
    # Grid coordinates are final comparison coordinates. Overlay measurement
    # must not snap the DIFFERENCE a second time: thin positive differences can
    # otherwise collapse to zero despite distinct source/model boundaries.
    source, modeled = shapely.set_precision(source, 0), shapely.set_precision(modeled, 0)
    missing = float(source.difference(modeled).area)
    extra = float(modeled.difference(source).area)
    distance = (None if source.is_empty or modeled.is_empty else
                float(source.boundary.hausdorff_distance(modeled.boundary)))
    # Distance alone can miss an absent small component. Empty versus nonempty
    # is always a missing/extra surface; source statuses are independent gates.
    if source.is_empty != modeled.is_empty:
        passed = False
    elif source.is_empty:
        passed = True
    else:
        allowance = max(AREA_EPSILON,
                        (source.boundary.length + modeled.boundary.length) * DISTANCE_TOLERANCE)
        passed = distance <= DISTANCE_TOLERANCE and max(missing, extra) <= allowance
    return {'missing_m2': missing, 'extra_m2': extra,
            'contour_distance_m': distance, 'coverage_passed': bool(passed)}


def normalize_union(polygons, precision):
    """Snap canonical physical UV coordinates BEFORE union and cell clipping."""
    if not polygons:
        return Polygon()
    if not precision:
        return areal_geometry(shapely.union_all(polygons))
    return areal_geometry(shapely.union_all(
        [shapely.set_precision(p, precision) for p in polygons], grid_size=precision))


def normalize_native_union(polygons, precision):
    """Native shared-coordinate face union first; snap its whole silhouette.

    Snapping individual quad subdivisions can erase a preserved narrow tip.
    This changes comparison representation only; original faces remain checked.
    """
    geometry = normalize_union(polygons, 0)
    if precision:
        def ring_without_subdivision(ring):
            points = list(ring.coords)[:-1]
            changed = True
            while changed and len(points) > 3:
                changed = False
                for i in range(len(points)):
                    before, point, after = [np.array(points[j % len(points)]) for j in (i-1,i,i+1)]
                    segment = after-before
                    length = np.linalg.norm(segment)
                    if length == 0:
                        continue
                    alpha = float((point-before) @ segment / (length*length))
                    distance = np.linalg.norm(point-(before+alpha*segment))
                    if 0 <= alpha <= 1 and distance <= 1e-10:
                        points.pop(i);changed = True;break
            return points
        parts = []
        for p in areal_components(geometry):
            simplified = Polygon(ring_without_subdivision(p.exterior),
                                 [ring_without_subdivision(r) for r in p.interiors])
            if not simplified.is_valid:
                raise ValueError('Numerical collinear subdivision removal changed topology')
            parts.append(simplified)
        geometry = shapely.union_all(parts)
    return areal_geometry(shapely.set_precision(geometry, precision)) if precision else geometry


def resolved_holes(geometry, precision):
    polygons = [geometry] if geometry.geom_type == 'Polygon' else getattr(geometry, 'geoms', [])
    return [Polygon(ring) for p in polygons if p.geom_type == 'Polygon' for ring in p.interiors
            if Polygon(ring).area > max(AREA_EPSILON, ring.length * precision / math.sqrt(2))]


def areal_components(geometry):
    if geometry.is_empty:
        return []
    return ([geometry] if geometry.geom_type == 'Polygon' else
            [p for p in getattr(geometry, 'geoms', []) if p.geom_type == 'Polygon'])


def audit(native, master, composition, directions, envelope, freshness, comparison_precision=0):
    if not 0 <= comparison_precision <= .00005:
        raise ValueError('Comparison precision must be between zero and 50 micrometres')
    vertices = np.asarray(native['vertices_m'], dtype=np.float64)
    faces = native['faces']
    if vertices.ndim != 2 or vertices.shape[1] != 3 or not np.isfinite(vertices).all():
        raise ValueError('Native saved world vertices must be finite Nx3')
    if len(faces) != len(master['faces']):
        raise ValueError('Native original face count differs from source registry')
    records = {r['plane_key']: r for r in composition['planes']}
    plan = {int(r['id']): r for r in directions['elements']}
    models = defaultdict(list)
    source = defaultdict(list)
    plane_meta = {}
    face_group = {}
    # Canonical measured plane identities, not world bbox substitutes.
    for r in composition['planes']:
        n = np.asarray(r['normal'], float)
        key = tuple(np.round(n, 5)) + (round(r['plane_d_m'], 4),)
        if key not in plane_meta:
            plane_meta[key] = (n, np.array(r['tangent'], float), r['plane_d_m'])
        exposed = shape(r['exposed_profile'])
        if exposed.area > AREA_EPSILON:
            source[key].append((exposed, r['revit_element_id'], r['status'], n,
                                np.array(r['tangent']), r['plane_d_m']))
    for gi, group in enumerate(master['groups']):
        record = records[group['source_plane_keys'][0]]
        n = np.array(group['normal'], float)
        key = tuple(np.round(n, 5)) + (round(record['plane_d_m'], 4),)
        if key not in plane_meta:
            plane_meta[key] = (n, np.array([-n[1], n[0], 0]), record['plane_d_m'])
        for fi in range(group['face_start'], group['face_start'] + group['face_count']):
            indices = faces[fi]
            if min(indices) < 0 or max(indices) >= len(vertices):
                raise ValueError('Native face vertex index outside saved mesh')
            pts = vertices[indices]
            relative = pts - pts[0]
            normal_actual = np.cross(relative, np.roll(relative, -1, axis=0)).sum(axis=0)
            normal_actual[2] = 0
            if np.linalg.norm(normal_actual) < 1e-16:
                normal_actual = n.copy()
            else:
                normal_actual /= np.linalg.norm(normal_actual)
            tangent_actual = np.array([-normal_actual[1], normal_actual[0], 0.])
            depth_actual = float(np.median(pts @ normal_actual))
            polygon = Polygon(np.column_stack((pts @ tangent_actual, pts[:, 2])))
            if not polygon.is_valid:
                raise ValueError('Native projected face invalid: ' + str(fi))
            check = geometry_check(pts, n)
            check['source_plane_displacement_m'] = float(np.max(abs(pts @ n - plane_meta[key][2])))
            face_group[fi] = (gi, key, check)
            # Shared saved vertices must produce identical canonical UV values.
            # Per-face plane reconstruction followed by affine projection adds
            # rounding noise exactly at grid half-ties and can open false cracks.
            canonical_polygon = Polygon(np.column_stack((pts @ plane_meta[key][1], pts[:, 2])))
            models[key].append((polygon, fi, normal_actual, tangent_actual, depth_actual, canonical_polygon))
    # Unknown direction source remains geometrically located, not declared pass.
    for candidate in envelope['candidate_planes']:
        eid = int(candidate['revit_element_id'])
        decision = plan.get(eid)
        normals = [] if decision is None else decision.get('normals',
                    [decision['normal']] if decision.get('normal') is not None else [])
        if normals or (decision and decision.get('excluded', False)):
            continue
        n = np.asarray(candidate['normal'], float); n[2] = 0; n /= np.linalg.norm(n)
        t = np.array([-n[1], n[0], 0.]); measured = np.concatenate([x['points_m'] for x in candidate['triangles']])
        depth = float(np.median(measured @ n))
        key = ('unknown', eid, candidate['plane_key'])
        profile = shapely.union_all([Polygon(np.column_stack((np.array(tri['points_m']) @ t,
                                                            np.array(tri['points_m'])[:, 2])))
                                     for tri in candidate['triangles']])
        if profile.area > AREA_EPSILON:
            plane_meta[key] = (n, t, depth)
            source[key].append((profile, eid, 'unknown_direction', n, t, depth))
    cells = defaultdict(lambda: {'source': defaultdict(list), 'modeled': defaultdict(list),
                                'face_indices': set(), 'source_ids': set(), 'blockers': set(),
                                'seam_duplicate_positions': 0})
    normalized_cells = defaultdict(lambda: {'source': {}, 'modeled': {}, 'holes': {},
                                             'raw_holes': {}, 'global_missing': {}})
    normalization_receipts = []
    normalization_bad_keys = set()
    for key in set(source) | set(models):
        n, t, depth = plane_meta[key]
        # Every polygon of this key uses ONE physical UV frame. Computing unions
        # of separately clipped near-identical native frames creates nanogaps.
        canonical_source = [transform_profile(g, sn, st, sd, t)
                            for g, _, _, sn, st, sd in source[key]]
        canonical_model = [canonical for _, _, _, _, _, canonical in models[key]]
        raw_source = normalize_union(canonical_source, 0)
        raw_model = normalize_union(canonical_model, 0)
        global_missing_components = [p for p in areal_components(raw_source)
                                     if p.area > AREA_EPSILON and p.intersection(raw_model).area <= AREA_EPSILON]
        global_missing = normalize_union(global_missing_components, 0)
        normalized_source = normalize_union(canonical_source, comparison_precision)
        normalized_model = normalize_native_union(canonical_model, comparison_precision)
        holes = resolved_holes(raw_source, comparison_precision)
        protected = normalize_union(holes, comparison_precision)
        lost_hole_area = float(shapely.set_precision(protected, 0).intersection(
            shapely.set_precision(normalized_source, 0)).area)
        hole_allowance = max(AREA_EPSILON, protected.length * comparison_precision / math.sqrt(2))
        if lost_hole_area > hole_allowance:
            normalization_bad_keys.add(key)
        normalization_receipts.append({'plane_key': list(key),
            'canonical_normal': n.tolist(), 'canonical_tangent': t.tolist(), 'canonical_depth_m': float(depth),
            'raw_source_area_m2': float(raw_source.area), 'normalized_source_area_m2': float(normalized_source.area),
            'raw_model_area_m2': float(raw_model.area), 'normalized_model_area_m2': float(normalized_model.area),
            'source_symmetric_difference_m2': float(raw_source.symmetric_difference(shapely.set_precision(normalized_source, 0)).area),
            'model_symmetric_difference_m2': float(raw_model.symmetric_difference(shapely.set_precision(normalized_model, 0)).area),
            'normalized_resolved_holes': len(resolved_holes(normalized_source, comparison_precision)),
            'raw_global_source_components': len(areal_components(raw_source)),
            'raw_global_components_without_native_coverage': [
                {'area_m2': float(p.area), 'bounds_uv_m': list(p.bounds)} for p in global_missing_components],
            'protected_resolved_holes': len(holes), 'lost_protected_hole_area_m2': lost_hole_area,
            'protected_holes_preserved': bool(lost_hole_area <= hole_allowance)})
        for label, geometry in [('source', normalized_source), ('modeled', normalized_model), ('holes', protected),
                                ('raw_holes', normalize_union(holes, 0)), ('global_missing', global_missing)]:
            if geometry.is_empty:
                continue
            low, high = profile_world_bounds(geometry, n, t, depth)
            for cell in cell_indices(low, high):
                clipped = clip_profile(geometry, n, t, depth, cell)
                if clipped.area > AREA_EPSILON:
                    normalized_cells[cell][label][key] = clipped
                    # Retain normalized-only occupancy and do not hide source-only cells.
                    cells[cell]
        for geometry, eid, state, source_n, source_t, source_d in source[key]:
            low, high = profile_world_bounds(geometry, source_n, source_t, source_d)
            for cell in cell_indices(low, high):
                clipped = clip_profile(geometry, source_n, source_t, source_d, cell)
                if clipped.area <= AREA_EPSILON:
                    continue
                entry = cells[cell]
                entry['source'][key].append(transform_profile(clipped, source_n, source_t, source_d, t))
                entry['source_ids'].add(eid)
                if state not in ('modeled', 'covered'):
                    entry['blockers'].add(state + ':' + str(eid))
        for geometry, fi, actual_n, actual_t, actual_d, canonical in models[key]:
            low, high = profile_world_bounds(geometry, actual_n, actual_t, actual_d)
            for cell in cell_indices(low, high):
                clipped = clip_profile(geometry, actual_n, actual_t, actual_d, cell)
                if clipped.area <= AREA_EPSILON:
                    continue
                entry = cells[cell]
                entry['modeled'][key].append(transform_profile(clipped, actual_n, actual_t, actual_d, t))
                entry['face_indices'].add(fi)
                group = master['groups'][face_group[fi][0]]
                entry['source_ids'].update(group['source_ids'])
                bases = group.get('face_attribution_basis', [])
                if bases and bases[fi-group['face_start']].startswith('within explicit'):
                    entry['blockers'].add('source_attribution_tolerance_only:' + str(fi))
    # Positional duplicate candidates are reported, not blindly welded. Shared
    # source vertices with one index are not counted as split seam candidates.
    positions = defaultdict(list)
    for i, point in enumerate(vertices):
        positions[tuple(np.round(point, 5))].append(i)
    for position, indices in positions.items():
        if len(indices) > 1:
            cell = tuple(math.floor(x / CELL) for x in position)
            if cell in cells:
                cells[cell]['seam_duplicate_positions'] += len(indices) - 1
    result = []
    for cell, entry in sorted(cells.items()):
        comparisons = []
        for key in (set(entry['source']) | set(entry['modeled']) |
                    set(normalized_cells[cell]['source']) | set(normalized_cells[cell]['modeled'])):
            s = shapely.union_all(entry['source'][key]) if entry['source'][key] else Polygon()
            m = shapely.union_all(entry['modeled'][key]) if entry['modeled'][key] else Polygon()
            raw_comparison = compare_profiles(s, m)
            ns = normalized_cells[cell]['source'].get(key, Polygon())
            nm = normalized_cells[cell]['modeled'].get(key, Polygon())
            normalized_comparison = compare_profiles(ns, nm) if comparison_precision else raw_comparison.copy()
            # Precision normalization may remove a complete thin feature. Raw
            # positive-area components must actually intersect native coverage;
            # counting normalized components cannot establish survival.
            missing_raw_components = [p for p in areal_components(s)
                                      if p.area > AREA_EPSILON and p.intersection(m).area <= AREA_EPSILON]
            clip_ghosts = [
                {'area_m2': float(p.area), 'bounds_uv_m': list(p.bounds)} for p in missing_raw_components]
            global_missing_here = normalized_cells[cell]['global_missing'].get(key, Polygon())
            survival_passed = global_missing_here.area <= AREA_EPSILON
            if comparison_precision and ((not s.is_empty and ns.is_empty) or (not m.is_empty and nm.is_empty)):
                entry['blockers'].add('comparison_precision_collapsed_surface')
            protected = normalized_cells[cell]['holes'].get(key, Polygon())
            filled = float(shapely.set_precision(protected, 0).intersection(shapely.set_precision(nm, 0)).area)
            # Resolved source openings remain a separate hard gate. A tolerance
            # strip at their boundary is numerical; filling a window is not.
            hole_allowance = max(AREA_EPSILON, protected.length * DISTANCE_TOLERANCE)
            normalized_holes_passed = bool(filled <= hole_allowance and key not in normalization_bad_keys)
            raw_holes = normalized_cells[cell]['raw_holes'].get(key, Polygon())
            raw_filled = float(raw_holes.intersection(m).area)
            raw_holes_passed = raw_filled <= max(AREA_EPSILON, raw_holes.length * DISTANCE_TOLERANCE)
            raw_comparison['protected_hole_filled_m2'] = raw_filled
            raw_comparison['protected_holes_passed'] = bool(raw_holes_passed)
            raw_comparison['coverage_passed'] = bool(raw_comparison['coverage_passed'] and raw_holes_passed and survival_passed)
            normalized_comparison['protected_hole_filled_m2'] = filled
            normalized_comparison['protected_holes_passed'] = normalized_holes_passed
            normalized_comparison['coverage_passed'] = bool(normalized_comparison['coverage_passed'] and normalized_holes_passed and survival_passed)
            # Raw actual geometry is independent evidence. A precision-induced
            # failure may use RAW only if the unchanged 2mm and feature gates
            # pass; retain uncertainty and prohibit a PASS cell.
            precision_uncertain = bool(comparison_precision and not normalized_comparison['coverage_passed']
                                       and raw_comparison['coverage_passed'])
            if precision_uncertain:
                entry['blockers'].add('comparison_precision_uncertain')
            comparison = (raw_comparison if precision_uncertain else normalized_comparison).copy()
            comparison['raw_comparison'] = raw_comparison
            comparison['normalized_comparison'] = normalized_comparison
            comparison['selected_evidence'] = 'raw_actual_with_precision_uncertainty' if precision_uncertain else 'normalized' if comparison_precision else 'raw_actual'
            comparison['raw_cell_components_without_native_coverage_receipt'] = clip_ghosts
            comparison['raw_components_without_native_coverage'] = [
                {'area_m2': float(p.area), 'bounds_uv_m': list(p.bounds)} for p in areal_components(global_missing_here)]
            comparison['raw_component_survival_passed'] = bool(survival_passed)
            comparison['plane_key'] = list(key)
            comparison['selection_known'] = bool(key[0] != 'unknown')
            comparisons.append(comparison)
        checks = [face_group[fi][2] for fi in entry['face_indices']]
        bad_faces = [fi for fi in entry['face_indices']
                     if not all(face_group[fi][2][k] for k in ('quad', 'convex', 'normal'))
                     or face_group[fi][2]['planarity_m'] > DISTANCE_TOLERANCE
                     or face_group[fi][2]['source_plane_displacement_m'] > DISTANCE_TOLERANCE]
        coverage = all(c['coverage_passed'] for c in comparisons if c['selection_known'])
        geometry_passed = not bad_faces and coverage
        blockers = sorted(entry['blockers'])
        if entry['seam_duplicate_positions']:
            blockers.append('split_seam_position_candidates')
        if not freshness.get('verified_current_revit', False):
            blockers.append('current_revit_source_freshness_pending')
        status = 'fail' if not geometry_passed else 'pending' if blockers else 'pass'
        result.append({'cell': list(cell), 'bbox_min_m': [v * CELL for v in cell],
                       'bbox_max_m': [(v + 1) * CELL for v in cell], 'status': status,
                       'geometry_checks_passed': geometry_passed,
                       'source_ids': sorted(entry['source_ids']), 'original_faces_checked': len(checks),
                       'nonquad_faces': sum(not c['quad'] for c in checks),
                       'nonconvex_faces': sum(not c['convex'] for c in checks),
                       'wrong_normals': sum(not c['normal'] for c in checks),
                       'bad_original_face_indices': sorted(bad_faces),
                       'missing_area_m2': sum(c['missing_m2'] for c in comparisons if c['selection_known']),
                       'extra_area_m2': sum(c['extra_m2'] for c in comparisons if c['selection_known']),
                       'unselected_source_candidate_area_m2': sum(c['missing_m2'] for c in comparisons if not c['selection_known']),
                       'max_meaningful_contour_distance_m': max((c['contour_distance_m'] for c in comparisons
                                                                  if c['contour_distance_m'] is not None), default=None),
                       'split_seam_position_candidates': entry['seam_duplicate_positions'],
                       'blockers': blockers, 'plane_comparisons': comparisons})
    return {'grid': {'cell_size_m': CELL, 'origin_m': [0, 0, 0], 'coordinates': 'Revit internal metres',
                     'master_cut': False, 'occupied_source_or_modeled_cells': len(result)},
            'contract': {'source_geometry': 'Exact measured exposed profiles; unresolved directions retain candidate source triangle silhouettes',
                         'contour_tolerance_m': DISTANCE_TOLERANCE,
                         'comparison_precision_m': comparison_precision,
                         'normalization': 'Canonical physical UV per key; source silhouette precision before source union; native shared-coordinate face union before whole-silhouette precision; then cell clipping; raw comparisons retained',
                         'numerical_collinear_native_boundary_removal_m': 1e-10,
                         'overlay_measurement': 'Measure differences at double precision using normalized coordinates, without resnapping the resulting differences',
                         'raw_component_survival': 'Original GLOBAL source components before clipping must intersect positive actual native area; global missing features localized in cells, raw clip ghosts retained as receipt',
                         'precision_uncertainty': 'Raw actual coverage passing unchanged2mm gates can establish geometry when normalization fails; explicit blocker keeps cell pending, both comparisons retained',
                         'area_numerical_epsilon_m2': AREA_EPSILON,
                         'face_cardinality': 'Original saved faces, never clipping-generated polygons',
                         'seam_candidates': 'Duplicate saved positions rounded10um; candidates require native seam classification',
                         'limits': 'Per-cell geometry audit does not prove whole-school source selection or global intersections.'},
            'source_freshness': {k:v for k,v in freshness.items() if k!='wall_geometry'},
            'normalization_receipts': normalization_receipts,
            'original_face_geometry_summary': {
                'faces_checked': len(face_group), 'nonquads': sum(not c[2]['quad'] for c in face_group.values()),
                'nonconvex': sum(not c[2]['convex'] for c in face_group.values()),
                'wrong_normals': sum(not c[2]['normal'] for c in face_group.values()),
                'scope': 'Saved original faces, counted once independent of cell overlap'},
            'summary': dict(Counter(c['status'] for c in result)),
            'cells': result, 'delivery_passed': False,
            'all_cells_passed': bool(result) and all(c['status'] == 'pass' for c in result)}


def self_test():
    n, t = np.array([1., 0, 0]), np.array([0., 1, 0])
    crossing = box(4, 0, 6, 2)
    a = clip_profile(crossing, n, t, 1, (0, 0, 0))
    b = clip_profile(crossing, n, t, 1, (0, 1, 0))
    assert abs(a.area + b.area - crossing.area) < 1e-10
    assert geometry_check(np.array([[1,4,0],[1,6,0],[1,6,2],[1,4,2]], float), n)['quad']
    hole = Polygon([(0,0),(5,0),(5,5),(0,5)], holes=[[(1,1),(1,2),(2,2),(2,1)]])
    assert abs(clip_profile(hole, n, t, 1, (0,0,0)).area - 24) < 1e-10
    assert not compare_profiles(hole, box(0,0,5,5))['coverage_passed']
    assert not compare_profiles(crossing, Polygon())['coverage_passed']
    # Whole absent panel still creates source-only occupied cells.
    records={'planes':[{'plane_key':'1', 'revit_element_id':1,'normal':n.tolist(), 'tangent':t.tolist(),
                       'plane_d_m':1,'exposed_profile':crossing.__geo_interface__, 'status':'unsupported_profile'}]}
    empty={'vertices_m':[[0,0,0]],'faces':[]}
    report=audit(empty,{'faces':[],'groups':[]},records,{'elements':[]},{'candidate_planes':[]},
                 {'verified_current_revit':True})
    assert report['grid']['occupied_source_or_modeled_cells']==2 and report['summary']=={'fail':2}
    candidate={'plane_key':'unknown-1','revit_element_id':1,'normal':n.tolist(),
               'triangles':[{'points_m':[[1,4,0],[1,6,0],[1,6,2]]},
                            {'points_m':[[1,4,0],[1,6,2],[1,4,2]]}]}
    unknown=audit(empty,{'faces':[],'groups':[]},{'planes':[]},
                  {'elements':[{'id':1,'normals':[]}]},{'candidate_planes':[candidate]},
                  {'verified_current_revit':True})
    assert unknown['summary']=={'pending':2} and not unknown['all_cells_passed']
    shifted={'vertices_m':[[2,4,0],[2,6,0],[2,6,2],[2,4,2]],'faces':[[0,1,2,3]]}
    master={'faces':shifted['faces'],'groups':[{'normal':n.tolist(),'source_plane_keys':['1'],
             'source_ids':[1],'face_start':0,'face_count':1}]}
    shifted_report=audit(shifted,master,records,{'elements':[]},{'candidate_planes':[]},
                         {'verified_current_revit':True})
    assert shifted_report['summary']=={'fail':2}
    assert all(c['bad_original_face_indices']==[0] for c in shifted_report['cells'])
    normalized_missing = audit(empty,{'faces':[],'groups':[]},records,{'elements':[]},
                               {'candidate_planes':[]},{'verified_current_revit':True}, .00005)
    assert normalized_missing['summary'] == {'fail':2}
    thin_record={'planes':[dict(records['planes'][0], exposed_profile=box(1,1,1.00002,4).__geo_interface__,status='modeled')]}
    thin_missing=audit(empty,{'faces':[],'groups':[]},thin_record,{'elements':[]},{'candidate_planes':[]},
                       {'verified_current_revit':True},.00005)
    assert thin_missing['summary']=={'fail':1}
    assert not thin_missing['cells'][0]['plane_comparisons'][0]['raw_component_survival_passed']
    tip_source = shapely.set_precision(Polygon([(-1.7372,3.9351),(-1.5372,3.8713),(-1.5372,3.87125)]), .00005)
    tip_model = shapely.set_precision(Polygon([(-1.60385,3.89255),(-1.5372,3.8713),(-1.5372,3.87125)]), .00005)
    assert compare_profiles(tip_source, tip_model)['missing_m2'] > 1e-6
    triangle = np.array([[-1.7372,3.9351],[-1.5372,3.87125],[-1.5372,3.8713]])
    center = triangle.mean(axis=0)
    mid = (triangle + np.roll(triangle,-1,axis=0)) / 2
    quads = [Polygon([triangle[i],mid[i],center,mid[(i-1)%3]]) for i in range(3)]
    assert all(p.is_valid and p.area>0 for p in quads)
    preserved_tip = normalize_native_union(quads,.00005)
    assert compare_profiles(tip_source,preserved_tip)['coverage_passed']
    assert not compare_profiles(tip_source,normalize_native_union([tip_model],.00005))['coverage_passed']
    # A micron native boundary perturbation preserves the actual tip within2mm
    # but grid snapping distorts it: the only acceptable outcome is PENDING.
    perturbed_mid = mid.copy();perturbed_mid[0,1] += 1e-6
    uv_quads = [[triangle[i],perturbed_mid[i],center,perturbed_mid[(i-1)%3]] for i in range(3)]
    uv_vertices=[];tip_faces=[];lookup={}
    for quad in uv_quads:
        face=[]
        for uv in quad:
            key=tuple(uv)
            if key not in lookup:
                lookup[key]=len(uv_vertices);uv_vertices.append([1,float(uv[0]),float(uv[1])])
            face.append(lookup[key])
        tip_faces.append(face)
    tip_native={'vertices_m':uv_vertices,'faces':tip_faces}
    tip_master={'faces':tip_faces,'groups':[dict(master['groups'][0],face_count=3)]}
    tip_records={'planes':[dict(records['planes'][0],exposed_profile=Polygon(triangle).__geo_interface__,status='modeled')]}
    uncertain=audit(tip_native,tip_master,tip_records,{'elements':[]},{'candidate_planes':[]},
                    {'verified_current_revit':True},.00005)
    assert uncertain['summary']=={'pending':1}
    assert uncertain['cells'][0]['geometry_checks_passed']
    assert 'comparison_precision_uncertain' in uncertain['cells'][0]['blockers']
    # Two solid pieces separated only by a submicrometre numerical seam must
    # compare as one surface; raw evidence still reports the artificial contour.
    pieces = [box(0,0,2.5,5), box(2.5000005,0,5,5),
              box(2.5,0,2.5000005,1), box(2.5,4,2.5000005,5)]
    raw_gap = normalize_union(pieces, 0)
    normalized_gap = normalize_union(pieces, .00005)
    assert not compare_profiles(box(0,0,5,5), raw_gap)['coverage_passed']
    assert compare_profiles(box(0,0,5,5), normalized_gap)['coverage_passed']
    normalized_hole = normalize_union([hole], .00005)
    assert len(resolved_holes(normalized_hole, .00005)) == 1
    assert not compare_profiles(normalized_hole, normalize_union([box(0,0,5,5)], .00005))['coverage_passed']
    hole_records={'planes':[dict(records['planes'][0], exposed_profile=hole.__geo_interface__,status='modeled')]}
    filled={'vertices_m':[[1,0,0],[1,5,0],[1,5,5],[1,0,5]],'faces':[[0,1,2,3]]}
    filled_master=dict(master,faces=filled['faces'])
    filled_report=audit(filled,filled_master,hole_records,{'elements':[]},{'candidate_planes':[]},
                        {'verified_current_revit':True},.00005)
    assert any(c['status']=='fail' and any(not p['protected_holes_passed'] for p in c['plane_comparisons'])
               for c in filled_report['cells'])
    print(json.dumps({'synthetic':True,'tests_passed':['face crosses grid boundary without master cut',
                     'hole preserved and filled-hole detected','entire missing panel creates failing source-only cells',
                     'unknown direction stays pending','normal-direction source shift cannot pass projected silhouette check',
                     'normalized source-only cells still fail', 'nanogap removed with raw evidence retained',
                     'resolved real window fill fails after normalization',
                     'whole absent 20um modeled-status source strip cannot pass grid collapse',
                     'positive thin difference area survives overlay measurement',
                     'narrow triangle subdivided into 3 quads preserves tip; genuinely missing tip fails',
                     'raw actual tip passes but snap damage stays explicit pending']}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    for name in ('native','mesh-source','composition','directions','envelope','output'):
        parser.add_argument('--'+name,type=Path)
    parser.add_argument('--source-freshness',type=Path)
    parser.add_argument('--comparison-precision-m',type=float,default=0,
                        help='Explicit canonical UV comparison grid, 0 (raw) to 0.00005 m')
    args=parser.parse_args()
    if args.self_test:
        self_test();return
    names=('native','mesh_source','composition','directions','envelope','output')
    if any(getattr(args,n) is None for n in names):parser.error('All input paths and output required')
    output=args.output.resolve()
    if output.exists():raise ValueError('Fresh audit output required')
    paths={n:getattr(args,n).resolve() for n in names if n!='output'}
    input_hashes={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in paths.items()}
    inputs={n:json.loads(p.read_text(encoding='utf-8-sig')) for n,p in paths.items()}
    freshness=(json.loads(args.source_freshness.read_text(encoding='utf-8-sig'))
               if args.source_freshness else {'verified_current_revit':False,'reason':'Fresh Revit comparison receipt not supplied'})
    report=audit(inputs['native'],inputs['mesh_source'],inputs['composition'],inputs['directions'],inputs['envelope'],freshness,args.comparison_precision_m)
    if input_hashes!={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in paths.items()}:
        raise RuntimeError('Audit input changed while being checked')
    report['input_sha256']=input_hashes
    if args.source_freshness:report['input_sha256']['freshness']=hashlib.sha256(args.source_freshness.read_bytes()).hexdigest()
    output.mkdir(parents=True)
    (output/'five-metre-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    fields=['cell','bbox_min_m','bbox_max_m','status','geometry_checks_passed','source_ids','original_faces_checked',
            'nonquad_faces','nonconvex_faces','wrong_normals','missing_area_m2','extra_area_m2','unselected_source_candidate_area_m2',
            'max_meaningful_contour_distance_m','split_seam_position_candidates','blockers']
    with (output/'five-metre-audit.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in report['cells']:writer.writerow({k:json.dumps(row[k],ensure_ascii=False) if isinstance(row[k],list) else row[k] for k in fields})
    worst=sorted(report['cells'],key=lambda c:c['missing_area_m2']+c['extra_area_m2'],reverse=True)[:15]
    compact={k:report[k] for k in ('grid','summary','original_face_geometry_summary','all_cells_passed','source_freshness','delivery_passed')}
    compact['worst_cells']=[{k:c[k] for k in ('cell','status','source_ids','missing_area_m2','extra_area_m2','blockers')} for c in worst]
    (output/'summary.json').write_text(json.dumps(compact,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in compact.items() if k!='worst_cells'},ensure_ascii=False))


if __name__=='__main__':main()

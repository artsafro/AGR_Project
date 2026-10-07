"""Pure, measured planar rectilinear BODY rebuilding; no scene or file I/O.

Input may be triangle coordinate lists, Shapely polygons (including holes), or
GeoJSON polygon mappings. Precision normalization is bounded and reported;
unsupported contours raise ValueError rather than being approximated.
"""
import numpy as np
import shapely
from shapely.geometry import Polygon, shape as geometry_shape


def rebuild_profile(polygons_2d, normal3, tangent3, plane_d,
                    rail_cluster_m=.15, coordinate_precision_m=.00005):
    """Return vertices_m, faces and QA for one measured vertical plane.

    Disconnected profiles are rebuilt independently, avoiding unrelated cuts.
    The second profile coordinate is world Z; normals/tangents must therefore
    be unit horizontal vectors perpendicular to each other.
    """
    n, tangent = np.asarray(normal3, float), np.asarray(tangent3, float)
    if (n.shape != (3,) or tangent.shape != (3,) or
            not np.isfinite(np.r_[n, tangent, plane_d]).all() or
            abs(np.linalg.norm(n)-1) > 1e-6 or
            abs(np.linalg.norm(tangent)-1) > 1e-6 or
            abs(n[2]) > 1e-6 or abs(tangent[2]) > 1e-6 or
            abs(np.dot(n, tangent)) > 1e-6):
        raise ValueError('Requires finite orthonormal horizontal normal/tangent')
    if (not np.isfinite([coordinate_precision_m, rail_cluster_m]).all() or
            not 0 < coordinate_precision_m <= .00005 or rail_cluster_m < 0):
        raise ValueError('Precision must be positive and at most 0.05mm; rails nonnegative')
    source = []
    for coords in polygons_2d:
        p = (coords if isinstance(coords, Polygon) else
             geometry_shape(coords) if isinstance(coords, dict) else Polygon(coords))
        if p.geom_type != 'Polygon' or p.is_empty or not p.is_valid or p.area <= 1e-12:
            raise ValueError('Invalid, empty or degenerate source polygon')
        source.append(p)
    if not source:
        raise ValueError('Empty source profile')
    raw = shapely.union_all(source)
    if raw.geom_type not in ('Polygon', 'MultiPolygon') or not raw.is_valid:
        raise ValueError('Invalid source union')
    profile = shapely.set_precision(raw, coordinate_precision_m).simplify(
        .000001, preserve_topology=True)
    if profile.is_empty or profile.geom_type not in ('Polygon', 'MultiPolygon'):
        raise ValueError('Precision collapsed source profile')
    parts = list(profile.geoms) if profile.geom_type == 'MultiPolygon' else [profile]
    raw_parts = list(raw.geoms) if raw.geom_type == 'MultiPolygon' else [raw]
    if (len(parts) != len(raw_parts) or
            sum(len(p.interiors) for p in parts) != sum(len(p.interiors) for p in raw_parts)):
        raise ValueError('Precision changed components or opening loops')
    precision_distance = float(shapely.hausdorff_distance(raw.boundary, profile.boundary))
    if precision_distance > coordinate_precision_m * 1.5:
        raise ValueError('Precision normalization exceeds numerical-noise bound')
    vertices, faces, lookup, cells, cut_counts = [], [], {}, [], []
    origin = n * plane_d
    winding = np.dot(np.cross(tangent, [0, 0, 1]), n)
    min_span = float('inf')
    for part in parts:
        rings = [list(part.exterior.coords)] + [list(r.coords) for r in part.interiors]
        segments = [(u, v) for ring in rings for u, v in zip(ring, ring[1:])]
        if any(min(abs(u[0]-v[0]), abs(u[1]-v[1])) > 1e-8 for u, v in segments):
            raise ValueError('Sloped contour: rectilinear rebuilding cannot preserve it')
        axes = [sorted(set(v[i] for ring in rings for v in ring)) for i in (0, 1)]
        if max(map(len, axes)) > 400:
            raise ValueError('Unsupported excessive boundary complexity')
        min_span = min(min_span, *(float(np.diff(axis).min()) for axis in axes))
        groups = []
        for axis in axes:
            g = []
            for value in axis:
                if not g or not rail_cluster_m or value-g[-1][0] > rail_cluster_m:
                    g.append([value])
                else:
                    g[-1].append(value)
            groups.append(g)
        for _ in range(20):
            constraints, conflicts = [{}, {}], [set(), set()]
            for i, gu in enumerate(groups[0]):
                for j, gv in enumerate(groups[1]):
                    for axis, group, cross in ((0, gu, gv), (1, gv, gu)):
                        other = 1-axis
                        choices = set()
                        for u, v in segments:
                            if abs(u[axis]-v[axis]) < 1e-9 and any(abs(u[axis]-q) < 1e-9 for q in group):
                                lo, hi = sorted((u[other], v[other]))
                                if hi >= cross[0]-1e-9 and lo <= cross[-1]+1e-9:
                                    choices.add(u[axis])
                        if len(choices) > 1:
                            conflicts[axis].add(i if axis == 0 else j)
                        elif choices:
                            constraints[axis][i, j] = next(iter(choices))
            if not any(conflicts):
                break
            for axis in (0, 1):
                groups[axis] = [part for k, g in enumerate(groups[axis])
                                for part in ([[q] for q in g] if k in conflicts[axis] else [g])]
        else:
            raise ValueError('Local rail constraints did not converge')
        nx, nz = map(len, groups)
        cut_counts.append([nx, nz])
        grid = np.empty((nx, nz, 2))
        for i in range(nx):
            for j in range(nz):
                for axis in (0, 1):
                    if (i, j) in constraints[axis]:
                        value = constraints[axis][i, j]
                    else:
                        line = sorted((k[1-axis], v) for k, v in constraints[axis].items()
                                      if k[axis] == (i if axis == 0 else j))
                        value = (float(np.interp(j if axis == 0 else i,
                                 [q for q, _ in line], [v for _, v in line]))
                                 if line else float(np.mean(groups[axis][i if axis == 0 else j])))
                    grid[i, j, axis] = value
        for i in range(nx-1):
            for j in range(nz-1):
                corners = [tuple(grid[ii, jj]) for ii, jj in ((i,j),(i+1,j),(i+1,j+1),(i,j+1))]
                cell = Polygon(corners)
                vectors = np.roll(np.array(corners), -1, axis=0)-corners
                turns = vectors[:,0]*np.roll(vectors[:,1],-1)-vectors[:,1]*np.roll(vectors[:,0],-1)
                if not cell.is_valid or cell.area < 1e-10 or not np.all(turns > 1e-10):
                    raise ValueError('Invalid or nonconvex transition quad')
                area = cell.intersection(part).area
                if area < 1e-12:
                    continue
                if abs(area-cell.area) > 1e-8:
                    raise ValueError('Partial cell would approximate source')
                cells.append(cell)
                face = []
                for uv in corners:
                    if uv not in lookup:
                        lookup[uv] = len(vertices)
                        vertices.append((origin+tangent*uv[0]+np.array([0,0,uv[1]])).tolist())
                    face.append(lookup[uv])
                faces.append(face if winding > 0 else list(reversed(face)))
    if not faces:
        raise ValueError('No rebuilt faces')
    rebuilt = shapely.union_all(cells)
    missing = float(profile.difference(rebuilt).area)
    extra = float(rebuilt.difference(profile).area)
    overlap = float(sum(c.area for c in cells)-rebuilt.area)
    distance = float(shapely.hausdorff_distance(raw.boundary, rebuilt.boundary))
    if distance > .002 or max(missing, extra, abs(overlap)) > 1e-8:
        raise ValueError('Rebuild fails contour/coverage/overlap contract')
    edges = {}
    for f in faces:
        for i, j in zip(f, f[1:]+f[:1]):
            key = tuple(sorted((i,j)))
            edges[key] = edges.get(key, 0)+1
    if max(edges.values()) > 2:
        raise ValueError('Nonmanifold surface')
    qa = dict(quads=len(faces), source_components=len(raw_parts),
              source_opening_loops=sum(len(p.interiors) for p in raw_parts),
              contour_hausdorff_m=distance,
              symmetric_difference_m2=float(raw.symmetric_difference(rebuilt).area),
              precision_hausdorff_m=precision_distance,
              precision_symmetric_difference_m2=float(raw.symmetric_difference(profile).area),
              coordinate_precision_m=coordinate_precision_m,
              missing_area_m2=missing, extra_area_m2=extra, overlap_area_m2=max(0., overlap),
              boundary_edges=sum(c == 1 for c in edges.values()), max_edge_face_count=max(edges.values()),
              min_grid_span_m=min_span, cut_counts=cut_counts,
              min_edge_length_m=min(float(np.linalg.norm(np.array(vertices[i])-vertices[j])) for i,j in edges),
              cut_style='local constrained rails' if rail_cluster_m else 'coordinate grid',
              visual_acceptance='pending', delivery_passed=False)
    return dict(vertices_m=vertices, faces=faces, qa=qa,
                source_profile_geojson=profile.__geo_interface__,
                raw_source_profile_geojson=raw.__geo_interface__)

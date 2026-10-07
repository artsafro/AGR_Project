"""Exact planar irregular-profile fallback, not regular architectural quad flow.

Constrained Delaunay triangles are split into three convex quads with shared
edge midpoints and one triangle centroid. No boundary snapping, scene mutation,
or I/O occurs. Caller selects this fallback explicitly for measured contours.
"""
import numpy as np
import shapely
from shapely.geometry import Polygon, shape as geometry_shape


def rebuild_profile(polygons_2d, normal3, tangent3, plane_d,
                    rail_cluster_m=.15, coordinate_precision_m=.00005,
                    contour_simplification_m=0):
    """Rebuild vertical-plane arbitrary Polygon/MultiPolygon-with-holes as quads.

    Parameters match quad_geometry for integration, but rails and precision are
    not applied: this route preserves source coordinates without normalization.
    """
    n, tangent = np.asarray(normal3, dtype=np.float64), np.asarray(tangent3, dtype=np.float64)
    if (n.shape != (3,) or tangent.shape != (3,) or
            not np.isfinite(np.r_[n,tangent,plane_d]).all() or
            abs(np.linalg.norm(n)-1) > 1e-9 or
            abs(np.linalg.norm(tangent)-1) > 1e-9 or
            abs(n[2]) > 1e-9 or abs(tangent[2]) > 1e-9 or
            abs(n@tangent) > 1e-9):
        raise ValueError('Requires finite true orthonormal horizontal normal/tangent')
    polygons = []
    for coordinates in polygons_2d:
        poly = (coordinates if isinstance(coordinates, Polygon) else
                geometry_shape(coordinates) if isinstance(coordinates, dict) else Polygon(coordinates))
        if poly.geom_type != 'Polygon' or not poly.is_valid or poly.is_empty or poly.area <= 0:
            raise ValueError('Invalid, empty or degenerate source polygon')
        polygons.append(poly)
    if not polygons:
        raise ValueError('Empty source profile')
    if not np.isfinite(contour_simplification_m) or not 0 <= contour_simplification_m <= .00005:
        raise ValueError('Explicit contour simplification must be between0 and50um')
    profile = shapely.union_all(polygons)
    if profile.geom_type not in ('Polygon','MultiPolygon') or not profile.is_valid:
        raise ValueError('Invalid source union')
    raw_profile=profile
    original_parts=list(profile.geoms) if profile.geom_type=='MultiPolygon' else [profile]
    simplification_qa=None
    if contour_simplification_m:
        reduced=profile.simplify(contour_simplification_m,preserve_topology=True)
        reduced_parts=list(reduced.geoms) if reduced.geom_type=='MultiPolygon' else [reduced]
        if (len(original_parts)!=len(reduced_parts) or
                sum(len(p.interiors) for p in original_parts)!=sum(len(p.interiors) for p in reduced_parts)):
            raise ValueError('Contour simplification changed components or opening loops')
        simplification_distance=float(profile.boundary.hausdorff_distance(reduced.boundary))
        if simplification_distance>contour_simplification_m+1e-12:
            raise ValueError('Contour simplification exceeds explicit boundary displacement bound')
        for p in original_parts:
            for ring in p.interiors:
                if reduced.intersection(Polygon(ring).buffer(-.000075)).area>1e-10:
                    raise ValueError('Contour simplification filled a protected source opening')
        simplification_qa=dict(applied=True,tolerance_m=contour_simplification_m,
                              boundary_hausdorff_m=simplification_distance,
                              symmetric_difference_m2=float(profile.symmetric_difference(reduced).area),
                              components_before=len(original_parts),components_after=len(reduced_parts),
                              opening_loops_before=sum(len(p.interiors) for p in original_parts),
                              opening_loops_after=sum(len(p.interiors) for p in reduced_parts))
        profile=reduced
    parts = list(profile.geoms) if profile.geom_type == 'MultiPolygon' else [profile]
    triangle_collection = shapely.constrained_delaunay_triangles(profile)
    triangles = list(triangle_collection.geoms)
    if not triangles:
        raise ValueError('No constrained source triangles')
    vertices, faces, cells, lookup = [], [], [], {}
    origin = n*float(plane_d)
    winding = np.dot(np.cross(tangent,[0,0,1]),n)
    for triangle in triangles:
        if triangle.geom_type != 'Polygon' or len(triangle.exterior.coords) != 4 or triangle.area <= 0:
            raise ValueError('Unexpected constrained triangulation output')
        coords = np.asarray(triangle.exterior.coords[:-1],dtype=np.float64)
        a,b = coords[1]-coords[0],coords[2]-coords[0]
        if a[0]*b[1]-a[1]*b[0] < 0:
            coords = coords[::-1]
        mids = (coords+np.roll(coords,-1,axis=0))/2
        center = coords.mean(axis=0)
        for i in range(3):
            corners = [tuple(coords[i]),tuple(mids[i]),tuple(center),tuple(mids[(i-1)%3])]
            vectors = np.roll(np.asarray(corners),-1,axis=0)-corners
            turns = vectors[:,0]*np.roll(vectors[:,1],-1)-vectors[:,1]*np.roll(vectors[:,0],-1)
            cell = Polygon(corners)
            if not cell.is_valid or cell.area <= 0 or not np.all(turns > 0):
                raise ValueError('Nonconvex or degenerate fallback quad')
            cells.append(cell)
            face = []
            for uv in corners:
                if uv not in lookup:
                    lookup[uv] = len(vertices)
                    vertices.append((origin+tangent*uv[0]+[0,0,uv[1]]).tolist())
                face.append(lookup[uv])
            faces.append(face if winding > 0 else list(reversed(face)))
    rebuilt = shapely.union_all(cells)
    tolerance_area = max(1e-10, profile.area*1e-12)
    distance = float(profile.boundary.hausdorff_distance(rebuilt.boundary))
    missing, extra = float(profile.difference(rebuilt).area), float(rebuilt.difference(profile).area)
    overlap = float(sum(cell.area for cell in cells)-rebuilt.area)
    rebuilt_parts = list(rebuilt.geoms) if rebuilt.geom_type == 'MultiPolygon' else [rebuilt]
    holes = sum(len(p.interiors) for p in parts)
    if (distance > .002 or max(missing,extra,abs(overlap)) > tolerance_area or
            len(parts) != len(rebuilt_parts) or
            holes != sum(len(p.interiors) for p in rebuilt_parts)):
        raise ValueError('Fallback fails source boundary/coverage/holes/overlap contract')
    if contour_simplification_m and any(cell.intersection(raw_profile).area<=0 for cell in cells):
        raise ValueError('Simplified fallback emits a quad without positive raw source intersection')
    edges = {}
    for face in faces:
        for i,j in zip(face,face[1:]+face[:1]):
            key = tuple(sorted((i,j)))
            edges[key] = edges.get(key,0)+1
    if max(edges.values()) > 2:
        raise ValueError('Nonmanifold fallback surface')
    result=dict(vertices_m=vertices,faces=faces,
                source_profile_geojson=profile.__geo_interface__,
                raw_source_profile_geojson=raw_profile.__geo_interface__,
                qa=dict(quads=len(faces),source_triangles=len(triangles),source_components=len(parts),
                        source_opening_loops=holes,contour_hausdorff_m=distance,
                        symmetric_difference_m2=float(profile.symmetric_difference(rebuilt).area),
                        precision_hausdorff_m=0.,precision_symmetric_difference_m2=0.,
                        coordinate_precision_m=0.,requested_coordinate_precision_m=coordinate_precision_m,
                        missing_area_m2=missing,extra_area_m2=extra,overlap_area_m2=max(0.,overlap),
                        boundary_edges=sum(c==1 for c in edges.values()),max_edge_face_count=max(edges.values()),
                        min_edge_length_m=min(float(np.linalg.norm(np.array(vertices[i])-vertices[j])) for i,j in edges),
                        cut_style='constrained triangle subdivision fallback; irregular quad flow',
                        visual_acceptance='pending',delivery_passed=False))
    if simplification_qa is not None:
        result['qa']['contour_simplification']=simplification_qa
        result['qa']['contour_hausdorff_m']=float(raw_profile.boundary.hausdorff_distance(rebuilt.boundary))
        result['qa']['symmetric_difference_m2']=float(raw_profile.symmetric_difference(rebuilt).area)
    return result


def rebuild_normalized_profile(polygons_2d, normal3, tangent3, plane_d,
                               rail_cluster_m=.15, coordinate_precision_m=.00005,
                               contour_simplification_m=0):
    """Explicit bounded numerical-noise normalization before irregular fallback.

    Retains the exact route above unchanged. A 50um maximum precision grid is
    permitted only when component/hole topology survives and measured boundary
    displacement is at most 75um. Removed/added area is bounded by the measured
    perimeter times that displacement. Resulting quads below 1e-10 m2 reject.
    """
    if not np.isfinite(coordinate_precision_m) or not 0 < coordinate_precision_m <= .00005:
        raise ValueError('Normalized fallback requires precision up to 50um')
    polygons=[]
    for coordinates in polygons_2d:
        poly=(coordinates if isinstance(coordinates,Polygon) else
              geometry_shape(coordinates) if isinstance(coordinates,dict) else Polygon(coordinates))
        if poly.geom_type!='Polygon' or not poly.is_valid or poly.is_empty or poly.area<=0:
            raise ValueError('Invalid source profile for bounded normalization')
        polygons.append(poly)
    if not polygons:raise ValueError('Empty source profile')
    raw=shapely.union_all(polygons)
    if raw.geom_type not in ('Polygon','MultiPolygon') or not raw.is_valid:
        raise ValueError('Invalid source union')
    normalized=shapely.set_precision(raw,coordinate_precision_m)
    if normalized.is_empty or normalized.geom_type not in ('Polygon','MultiPolygon'):
        raise ValueError('Normalization collapsed source profile')
    raw_parts=list(raw.geoms) if raw.geom_type=='MultiPolygon' else [raw]
    parts=list(normalized.geoms) if normalized.geom_type=='MultiPolygon' else [normalized]
    raw_holes=sum(len(p.interiors) for p in raw_parts)
    holes=sum(len(p.interiors) for p in parts)
    if len(parts)!=len(raw_parts) or holes!=raw_holes:
        raise ValueError('Normalization changed components or opening loops')
    distance=float(raw.boundary.hausdorff_distance(normalized.boundary))
    bound=coordinate_precision_m*1.5
    if distance>bound:
        raise ValueError('Normalization boundary displacement exceeds 75um precision bound')
    removed=float(raw.difference(normalized).area)
    added=float(normalized.difference(raw).area)
    area_bound=float(raw.boundary.length*bound+np.pi*bound**2)
    if max(removed,added)>area_bound:
        raise ValueError('Normalization coverage change exceeds perimeter-bound allowance')
    result=rebuild_profile(parts,normal3,tangent3,plane_d,rail_cluster_m,coordinate_precision_m,contour_simplification_m)
    normalized_output=geometry_shape(result['source_profile_geojson'])
    total_distance=float(raw.boundary.hausdorff_distance(normalized_output.boundary))
    if total_distance>.000075:
        raise ValueError('Normalization plus contour simplification exceeds total75um boundary bound')
    if max(raw.difference(normalized_output).area,normalized_output.difference(raw).area)>area_bound:
        raise ValueError('Total normalization/simplification coverage exceeds perimeter allowance')
    for p in raw_parts:
        for ring in p.interiors:
            if normalized_output.intersection(Polygon(ring).buffer(-.000075)).area>1e-10:
                raise ValueError('Total normalization/simplification filled protected opening')
    vertices=np.asarray(result['vertices_m'],dtype=np.float64)
    min_area=float('inf')
    for face in result['faces']:
        relative=vertices[face]-vertices[face[0]]
        area=float(np.linalg.norm(np.cross(relative,np.roll(relative,-1,axis=0)).sum(axis=0))*.5)
        min_area=min(min_area,area)
    if min_area<1e-10:
        raise ValueError('Normalized fallback would emit native-degenerate quad area below 1e-10m2')
    qa=result['qa']
    qa.update(contour_hausdorff_m=total_distance,
              symmetric_difference_m2=float(raw.symmetric_difference(normalized_output).area),
              precision_hausdorff_m=distance,
              precision_symmetric_difference_m2=float(raw.symmetric_difference(normalized).area),
              coordinate_precision_m=coordinate_precision_m,min_quad_area_m2=min_area,
              source_normalization=dict(applied=True,grid_m=coordinate_precision_m,
                  max_boundary_displacement_m=distance,allowed_boundary_displacement_m=bound,
                  removed_area_m2=removed,added_area_m2=added,allowed_area_change_m2=area_bound,
                  topology_components_before=len(raw_parts),topology_components_after=len(parts),
                  opening_loops_before=raw_holes,opening_loops_after=holes))
    if contour_simplification_m:
        qa['source_normalization']['total_boundary_displacement_m']=total_distance
    result['raw_source_profile_geojson']=raw.__geo_interface__
    return result

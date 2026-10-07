"""Read-only global surface seam QA in float64; no DCC or source mutation.

Near positions are candidates, not authorization to merge: 50um proximity can
also represent a real thin feature. T-junction repair requires coordinated quad
subdivision and is deliberately left as an explicit repair proposal.
"""
from collections import defaultdict
from itertools import product
import numpy as np
import shapely
from shapely.geometry import LineString, box


def inspect_seams(vertices, faces, tolerance_m=.00005):
    """Inspect exact edge incidence, proximity pairs, T-junctions and boundaries.

    Returned edge identifiers are sorted vertex-index pairs; T-junctions include
    the vertex, edge, edge face indices, actual distance and interpolation t.
    Boundary components refer to the exact current indexed mesh, before welding.
    """
    points = np.asarray(vertices, dtype=np.float64)
    if (points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all() or
            not np.isfinite(tolerance_m) or tolerance_m <= 0):
        raise ValueError('Requires finite Nx3 vertices and positive tolerance')
    face_list = [list(f) for f in faces]
    incidence = defaultdict(list)
    degenerate_faces = []
    used = set()
    for fi, face in enumerate(face_list):
        if any(not isinstance(i,(int,np.integer)) or i < 0 or i >= len(points) for i in face):
            raise ValueError('Invalid face vertex index')
        face = [int(i) for i in face]
        face_list[fi] = face
        if len(face) < 3 or len(set(face)) != len(face):
            degenerate_faces.append(fi)
        used.update(face)
        for i,j in zip(face,face[1:]+face[:1]):
            incidence[tuple(sorted((int(i),int(j))))].append(fi)
    # Spatial hash checks all neighbouring buckets, including bucket boundaries.
    buckets = defaultdict(list)
    pairs = []
    for i,point in enumerate(points):
        key = tuple(np.floor(point/tolerance_m).astype(np.int64))
        for shift in product((-1,0,1),repeat=3):
            for j in buckets[tuple(k+s for k,s in zip(key,shift))]:
                distance = float(np.linalg.norm(point-points[j]))
                if distance <= tolerance_m:
                    pairs.append(dict(vertices=[j,i],distance_m=distance,exact=bool(np.array_equal(point,points[j]))))
        buckets[key].append(i)
    # Group proximity graph only for reporting. Transitive groups MUST NOT be
    # welded blindly: their diameter can exceed tolerance.
    adjacency = defaultdict(set)
    for pair in pairs:
        i,j=pair['vertices'];adjacency[i].add(j);adjacency[j].add(i)
    position_groups=[]; visited=set()
    for start in sorted(adjacency):
        if start in visited:continue
        pending=[start]; group=[];visited.add(start)
        while pending:
            i=pending.pop();group.append(i)
            for j in adjacency[i]-visited:visited.add(j);pending.append(j)
        position_groups.append(sorted(group))
    edge_keys=list(incidence)
    segments=[LineString(points[[i,j],:2]) for i,j in edge_keys]
    tree=shapely.STRtree(segments)
    junctions=[];zero_edges=[]
    for edge in edge_keys:
        if np.linalg.norm(points[edge[1]]-points[edge[0]])==0:zero_edges.append(list(edge))
    # XY broad phase, followed by full 3D point-to-segment distance. Vertical
    # edges have degenerate XY boxes but remain valid broad-phase candidates.
    for vi in sorted(used):
        p=points[vi]
        query=box(p[0]-tolerance_m,p[1]-tolerance_m,p[0]+tolerance_m,p[1]+tolerance_m)
        for ei in tree.query(query):
            i,j=edge_keys[ei]
            if vi in (i,j):continue
            a,b=points[i],points[j];delta=b-a;den=float(delta@delta)
            if den==0:continue
            t=float((p-a)@delta/den)
            if not 0 < t < 1:continue
            # Coincident endpoint vertices belong in proximity QA, not T QA.
            if min(np.linalg.norm(p-a),np.linalg.norm(p-b))<=tolerance_m:continue
            distance=float(np.linalg.norm(p-(a+t*delta)))
            if distance<=tolerance_m:
                junctions.append(dict(vertex=vi,edge=[i,j],edge_faces=incidence[(i,j)],
                                      distance_m=distance,t=t))
    boundary_edges=[edge for edge,owners in incidence.items() if len(owners)==1]
    boundary_adjacency=defaultdict(set)
    for i,j in boundary_edges:boundary_adjacency[i].add(j);boundary_adjacency[j].add(i)
    components=[];visited=set()
    for start in sorted(boundary_adjacency):
        if start in visited:continue
        pending=[start];group=[];visited.add(start)
        while pending:
            i=pending.pop();group.append(i)
            for j in boundary_adjacency[i]-visited:visited.add(j);pending.append(j)
        edges=[list(edge) for edge in sorted({tuple(sorted((i,j)))
                                             for i in group for j in boundary_adjacency[i]})]
        degree={i:len(boundary_adjacency[i]) for i in group}
        components.append(dict(vertices=sorted(group),edges=edges,
                               closed_simple_loop=all(d==2 for d in degree.values()),
                               branch_vertices=sorted(i for i,d in degree.items() if d>2),
                               end_vertices=sorted(i for i,d in degree.items() if d==1)))
    nonmanifold=[dict(edge=list(edge),faces=owners) for edge,owners in incidence.items() if len(owners)>2]
    shared=[dict(edge=list(edge),faces=owners) for edge,owners in incidence.items() if len(owners)==2]
    vertex_faces=defaultdict(set);vertex_links=defaultdict(lambda:defaultdict(set))
    for fi,face in enumerate(face_list):
        for vi in face:vertex_faces[vi].add(fi)
    for (i,j),owners in incidence.items():
        for vi in (i,j):
            for owner in owners:vertex_links[vi][owner].update(set(owners)-{owner})
    disconnected_fans=[]
    for vi,owners in vertex_faces.items():
        seen=set();fans=[]
        for start in sorted(owners):
            if start in seen:continue
            pending=[start];fan=[];seen.add(start)
            while pending:
                fi=pending.pop();fan.append(fi)
                for next_face in vertex_links[vi][fi]-seen:seen.add(next_face);pending.append(next_face)
            fans.append(sorted(fan))
        if len(fans)>1:disconnected_fans.append(dict(vertex=int(vi),face_fans=fans))
    boundary_branch_vertices=sorted(i for i,neighbours in boundary_adjacency.items() if len(neighbours)>2)
    return dict(tolerance_m=tolerance_m,duplicate_position_pairs=pairs,
                duplicate_position_groups=position_groups,shared_edges=shared,
                t_junctions=junctions,nonmanifold_edges=nonmanifold,
                boundary_components=components,boundary_edges=[list(e) for e in boundary_edges],
                zero_length_edges=zero_edges,degenerate_faces=degenerate_faces,
                disconnected_vertex_fans=disconnected_fans,
                boundary_branch_vertices=boundary_branch_vertices,
                unused_vertices=sorted(set(range(len(points)))-used),
                counts=dict(vertices=len(points),faces=len(face_list),edges=len(incidence),
                            duplicate_position_pairs=len(pairs),duplicate_position_groups=len(position_groups),
                            shared_edges=len(shared),t_junctions=len(junctions),
                            nonmanifold_edges=len(nonmanifold),boundary_edges=len(boundary_edges),
                            boundary_components=len(components),
                            disconnected_vertex_fans=len(disconnected_fans),
                            boundary_branch_vertices=len(boundary_branch_vertices)),
                repair_proposal=dict(status='inspection only; no automatic mutation',
                    steps=['Review proximity candidates by plane, source and intended joint ownership.',
                           'Weld only an approved anchored cluster whose every displacement is within tolerance; reject collapsed faces.',
                           'Insert every accepted seam vertex into incident edge constraints.',
                           'Locally rebuild affected adjacent coplanar profiles with common boundary coordinates and convex quads.',
                           'Propagate edge subdivision only into affected neighbours; rerun seams and independent source contour/area QA.',
                           'Stop if convex quad closure requires broader geometry changes; preserve original and present the affected patch.']))

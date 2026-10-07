"""Bounded coplanar patch rebuilding; preserves input and writes a fresh mesh.

Only explicitly named groups are candidates. Opposed/orthogonal planes are never
welded. Every accepted patch retains measured source boundary within2mm, convex
quads and face provenance; rejected attempts remain in the receipt.
"""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon,shape,mapping
from shapely.affinity import affine_transform
from quad_geometry import rebuild_profile
from quad_irregular import rebuild_profile as rebuild_exact
from seam_geometry import inspect_seams


def parts(poly):
    return list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly]


def patch_candidate(mesh,indices,allow_contact_repair=False,numeric_certificate=None):
    groups=[mesh['groups'][i] for i in indices]
    n=np.array(groups[0]['normal'],dtype=float);n/=np.linalg.norm(n)
    t=np.array([-n[1],n[0],0.]);points=np.array(mesh['vertices_m'])
    source_profiles=[];current_cells=[];plane_points=[]
    for g in groups:
        old_n=np.array(g['normal']);old_t=np.array([-old_n[1],old_n[0],0.])
        if float(n@old_n)<1-1e-10:raise ValueError('Patch is not identically oriented coplanar')
        fi=g['face_start'];old_d=float(points[mesh['faces'][fi][0]]@old_n)
        source_profiles.append(affine_transform(shape(g['exposed_profile']),
            [float(old_t@t),0,0,1,float(old_n@t)*old_d,0]))
        for face in mesh['faces'][fi:fi+g['face_count']]:
            xyz=points[face];plane_points.extend(xyz)
            current_cells.append(Polygon(np.column_stack((xyz@t,xyz[:,2]))))
    plane_points=np.array(plane_points);d=float(np.median(plane_points@n))
    if float(np.max(np.abs(plane_points@n-d)))>.00005:
        raise ValueError('Coplanar patch exceeds 50um plane displacement allowance')
    source=shapely.union_all(source_profiles);current=shapely.union_all(current_cells)
    if not source.is_valid or not current.is_valid:raise ValueError('Invalid coplanar union')
    attempts=[]
    candidates=[('measured_source_union',source)]
    canonical=None;numeric_qa=None
    if numeric_certificate is not None:
        eid=numeric_certificate['id']
        if eid not in (5630274,2680489) or {i for g in groups for i in g['source_ids']}!={eid}:
            raise ValueError('Numeric contact certificate is not authorized for these source IDs')
        certified_raw=shape(numeric_certificate['profiles']['source'])
        if source.symmetric_difference(certified_raw).area>1e-8:
            raise ValueError('Input measured profile does not match numeric-contact certificate')
        canonical=shapely.union_all([shapely.set_precision(p,.00005) for profile in source_profiles for p in parts(profile)])
        certified_canonical=shape(numeric_certificate['profiles']['source_snapped'])
        if canonical.symmetric_difference(certified_canonical).area>1e-10:
            raise ValueError('Snap-before-union differs from certified physical contour')
        if len(parts(canonical))!=1 or sum(len(p.interiors) for p in parts(canonical))!=0:
            raise ValueError('Certified patch physical topology changed')
        max_motion=0.
        for profile in source_profiles:
            for p in parts(profile):
                for ring in [p.exterior]+list(p.interiors):
                    coords=np.array(ring.coords)
                    max_motion=max(max_motion,float(np.linalg.norm(coords-np.round(coords/.00005)*.00005,axis=1).max()))
        if max_motion>.00005:raise ValueError('Certified source vertex normalization exceeds50um')
        # Continuous full-surface distance bound; internal nano-crack traces are
        # identified by certificate and are not exterior contour displacement.
        if (not source.difference(canonical.buffer(.00005)).is_empty or
                not canonical.difference(source.buffer(.00005)).is_empty):
            raise ValueError('Certified source surfaces differ by more than50um')
        numeric_qa=dict(certificate_id=eid,evidence=numeric_certificate['evidence'],
                        max_source_boundary_vertex_motion_m=max_motion,
                        continuous_source_surface_distance_upper_bound_m=.00005,
                        raw_internal_trace_boundary_hausdorff_m=float(source.boundary.hausdorff_distance(canonical.boundary)),
                        comparison_basis='Certified physical contour: source components snapped50um before union; raw nano-crack traces retained in evidence',
                        expected_physical_components=1,expected_patch_holes=0,
                        protected_full_source_holes=numeric_certificate['result']['raw_source_snap_union']['holes'],
                        protected_full_source_hole_areas_m2=numeric_certificate['result']['raw_source_snap_union']['hole_areas_m2'])
        candidates.insert(0,('certified_numeric_contact_snap_before_union',canonical))
    simplified=current.simplify(.0002,preserve_topology=True)
    if (len(parts(simplified))==len(parts(current)) and
            sum(len(p.interiors) for p in parts(simplified))==sum(len(p.interiors) for p in parts(current)) and
            current.boundary.hausdorff_distance(simplified.boundary)<=.0002 and
            source.boundary.hausdorff_distance(simplified.boundary)<=.002):
        candidates.append(('bounded_mesh_simplification_0.2mm',simplified))
    candidates.append(('existing_measured_mesh_union',current))
    if allow_contact_repair:
        # Explicitly opted-in local contact repair, never blanket cleanup.
        # Closing by25um resolves an almost-touching boundary corner; topology
        # and the actual measured boundary displacement remain mandatory gates.
        closed=source.buffer(.000025,join_style='mitre').buffer(-.000025,join_style='mitre')
        if (closed.geom_type in ('Polygon','MultiPolygon') and len(parts(closed))==len(parts(source)) and
                sum(len(p.interiors) for p in parts(closed))==sum(len(p.interiors) for p in parts(source)) and
                source.boundary.hausdorff_distance(closed.boundary)<=.002):
            candidates.append(('explicit_contact_closure_25um',closed))
    for profile_name,profile in candidates:
        routes=[('exact_irregular',rebuild_exact)] if profile_name=='explicit_contact_closure_25um' else [('regular_local_rails',rebuild_profile),('exact_irregular',rebuild_exact)]
        for route,builder in routes:
            try:
                result=builder(parts(profile),n,t,d)
                coords=np.array(result['vertices_m'])
                cells=[Polygon(np.column_stack((coords[f]@t,coords[f][:,2]))) for f in result['faces']]
                rebuilt=shapely.union_all(cells)
                contour_source=canonical if profile_name=='certified_numeric_contact_snap_before_union' else source
                distance=float(contour_source.boundary.hausdorff_distance(rebuilt.boundary))
                if distance>.002:raise ValueError('Measured source boundary exceeds2mm: '+str(distance))
                if min(c.area for c in cells)<1e-10:raise ValueError('Native near-zero quad area')
                old_min_edge=min(g['qa'].get('min_edge_length_m',float('inf')) for g in groups)
                if np.isfinite(old_min_edge) and result['qa']['min_edge_length_m']<old_min_edge*.99:
                    raise ValueError('Repair would introduce a thinner edge than the measured input patch')
                if any(c.intersection(source).area<=0 for c in cells):
                    raise ValueError('Repair emits face with no positive measured source intersection')
                if profile_name=='certified_numeric_contact_snap_before_union':
                    full_source=shape(numeric_certificate['profiles']['raw_snapped'])
                    true_holes=[Polygon(r) for p in parts(full_source) for r in p.interiors]
                    if len(true_holes)!=numeric_qa['protected_full_source_holes']:
                        raise ValueError('Certified full-source real window hole count changed')
                    if any(c.intersection(h).area>1e-10 for c in cells for h in true_holes):
                        raise ValueError('Repair fills part of a certified real window opening')
                local_seams=inspect_seams(result['vertices_m'],result['faces'])
                exact_t=[j for j in local_seams['t_junctions'] if j['distance_m']<=1e-8]
                if exact_t or local_seams['disconnected_vertex_fans'] or local_seams['nonmanifold_edges']:
                    raise ValueError('Patch remains exact T-junction/bowtie/nonmanifold')
                # Match both removed and added measured coverage, not only bbox.
                changed_area=float(source.symmetric_difference(rebuilt).area)
                area_bound=float(source.boundary.length*.002+np.pi*.002**2)
                if changed_area>area_bound:raise ValueError('Measured coverage changed beyond2mm perimeter allowance')
                result['qa'].update(measured_source_boundary_hausdorff_m=distance,
                    measured_source_symmetric_difference_m2=changed_area,
                    native_min_quad_area_m2=min(c.area for c in cells),
                    all_patch_faces_have_positive_source_intersection=True,
                    accepted_repair_profile=profile_name,accepted_repair_route=route,
                    local_exact_t_junctions=0,local_disconnected_vertex_fans=0)
                if profile_name=='certified_numeric_contact_snap_before_union':
                    result['qa']['certified_numeric_contact']=numeric_qa
                return dict(result=result,normal=n.tolist(),tangent=t.tolist(),plane_d_m=d,
                            source=source,canonical=canonical,rebuilt=rebuilt,attempts=attempts,old_groups=groups)
            except ValueError as error:
                attempts.append(dict(profile=profile_name,route=route,rejected=str(error)))
    return dict(result=None,attempts=attempts,
                source_mesh_boundary_hausdorff_m=float(source.boundary.hausdorff_distance(current.boundary)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mesh',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--patches',default='[[267,268],[402,403],[32,33],[929]]')
    parser.add_argument('--allow-contact-repair-groups',default='[]',help='Explicit opt-in for bounded25um local contact closing')
    parser.add_argument('--numeric-contact-certificates',help='Explicit verified certificate folder; only IDs5630274/2680489 permitted')
    args=parser.parse_args();output=Path(args.output)
    if output.exists():raise ValueError('Fresh output required')
    mesh=json.loads(Path(args.mesh).read_text(encoding='utf-8'));patches=json.loads(args.patches)
    contact_groups=set(json.loads(args.allow_contact_repair_groups))
    certificates={}
    if args.numeric_contact_certificates:
        folder=Path(args.numeric_contact_certificates)
        results=json.loads((folder/'results.json').read_text(encoding='utf-8'))
        cracks={r['id']:r for r in json.loads((folder/'crack-evidence.json').read_text(encoding='utf-8'))}
        for row in results:
            eid=row['id']
            if eid not in (5630274,2680489):continue
            if cracks[eid]['max_internal_boundary_opposite_component_distance_m']>.000002:
                raise ValueError('Numeric source crack certificate exceeds2um')
            profiles=folder/('ID'+str(eid)+'-profiles.json')
            paths=[folder/'results.json',folder/'crack-evidence.json',folder/'source-topology-evidence.json',profiles]
            certificates[eid]=dict(id=eid,result=row,profiles=json.loads(profiles.read_text(encoding='utf-8')),
                evidence=[dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths])
    flat=[i for patch in patches for i in patch]
    if len(flat)!=len(set(flat)):raise ValueError('Patch groups must be disjoint')
    if any(i<0 or i>=len(mesh['groups']) for i in flat):raise ValueError('Invalid patch index')
    output.mkdir(parents=True);replacements={};receipts=[]
    for indices in patches:
        ids={eid for gi in indices for eid in mesh['groups'][gi]['source_ids']}
        certificate=certificates.get(next(iter(ids))) if len(ids)==1 else None
        try:patch=patch_candidate(mesh,indices,bool(set(indices)&contact_groups),certificate)
        except ValueError as error:patch=dict(result=None,attempts=[dict(rejected=str(error))])
        receipt=dict(groups=indices,source_ids=sorted({i for gi in indices for i in mesh['groups'][gi]['source_ids']}),
                     accepted=patch['result'] is not None,attempts=patch['attempts'])
        if patch['result'] is not None:
            replacements[indices[0]]=(indices,patch)
            receipt['qa']=patch['result']['qa'];receipt['old_quads']=sum(mesh['groups'][i]['face_count'] for i in indices)
        else:receipt['source_mesh_boundary_hausdorff_m']=patch.get('source_mesh_boundary_hausdorff_m')
        receipts.append(receipt)
    removed={gi for indices,patch in replacements.values() for gi in indices[1:]}
    vertices=[];faces=[];groups=[];normals=[];owner_ids=[]
    old_points=np.array(mesh['vertices_m'])
    for gi,original in enumerate(mesh['groups']):
        if gi in removed:continue
        if gi in replacements:
            indices,patch=replacements[gi];result=patch['result'];local_vertices=result['vertices_m'];local_faces=result['faces']
            group={k:copy.deepcopy(v) for k,v in original.items() if not k.startswith('face_')}
            group.update(source_ids=sorted({i for g in patch['old_groups'] for i in g['source_ids']}),
                source_plane_keys=sorted({key for g in patch['old_groups'] for key in g['source_plane_keys']}),
                source_types={key:value for g in patch['old_groups'] for key,value in g['source_types'].items()},
                qa=result['qa'],normal=patch['normal'],exposed_profile=mapping(patch['source']),
                repaired_from_group_indices=indices)
            # Positive source-area attribution is recomputed using the project
            # refine_provenance utility after root integration. Seed all source
            # IDs explicitly; no source ID is silently discarded during repair.
            group['face_source_ids']=[group['source_ids'][:] for f in local_faces]
            if patch.get('canonical') is not None:
                group['certified_canonical_exposed_profile']=mapping(patch['canonical'])
                group['raw_exposed_profile_preserved']=mapping(patch['source'])
            owners=[group['source_ids'][0] if len(group['source_ids'])==1 else 0]*len(local_faces)
        else:
            group=copy.deepcopy(original);local_faces=[];local_vertices=[];lookup={}
            start=original['face_start'];end=start+original['face_count']
            for face in mesh['faces'][start:end]:
                new_face=[]
                for v in face:
                    if v not in lookup:lookup[v]=len(local_vertices);local_vertices.append(mesh['vertices_m'][v])
                    new_face.append(lookup[v])
                local_faces.append(new_face)
            owners=mesh['owner_ids'][start:end]
        offset=len(vertices);group['face_start']=len(faces);group['face_count']=len(local_faces)
        vertices.extend(local_vertices);faces.extend([[v+offset for v in f] for f in local_faces]);groups.append(group)
        owner_ids.extend(owners);normals.extend([group['normal']]*len(local_faces))
    updated=copy.deepcopy(mesh);updated.update(vertices_m=vertices,faces=faces,groups=groups,owner_ids=owner_ids,face_normals=normals,
        repair_stage='coplanar patches; source provenance refinement pending',delivery_passed=False)
    updated['source_hashes']['before_coplanar_repair']=hashlib.sha256(Path(args.mesh).read_bytes()).hexdigest()
    updated['coplanar_repair_receipts']=receipts
    (output/'body-mesh.json').write_text(json.dumps(updated,ensure_ascii=False),encoding='utf-8')
    qa=inspect_seams(vertices,faces)
    summary=dict(patch_receipts=receipts,quads_before=len(mesh['faces']),quads_after=len(faces),seam_counts_after=qa['counts'],
                 exact_t_junctions_after=sum(j['distance_m']<=1e-8 for j in qa['t_junctions']),
                 provenance_refinement_required=any(r['accepted'] for r in receipts),delivery_passed=False)
    (output/'seams.json').write_text(json.dumps(qa),encoding='utf-8')
    (output/'receipt.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()

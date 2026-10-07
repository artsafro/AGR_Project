"""Compose measured facade layers with exact projected wall silhouettes.

Exposure probes inform direction review only. They never become a polygon.
Every modeled profile is source geometry minus geometrically projected blockers.
"""
import argparse, json, hashlib
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, mapping
from shapely.affinity import affine_transform
from quad_geometry import rebuild_profile
from quad_irregular import rebuild_normalized_profile as rebuild_irregular
from quad_irregular import rebuild_profile as rebuild_exact_irregular


def clip(poly, normal, bound, greater):
    result=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da=float(a@normal)-bound; db=float(b@normal)-bound
        ia=da>=0 if greater else da<=0; ib=db>=0 if greater else db<=0
        if ia: result.append(a)
        if ia!=ib: result.append(a+(b-a)*(da/(da-db)))
    return result


def profile_of(plane, tangent=None, precision=0):
    t=np.array(plane['tangent']) if tangent is None else tangent
    polygons=[]
    for tri in plane['triangles']:
        pts=np.array(tri['points_m'])
        poly=Polygon(np.column_stack((pts@t,pts[:,2])))
        if poly.area>1e-12: polygons.append(poly)
    return shapely.union_all(polygons,grid_size=precision) if precision else shapely.union_all(polygons)


def polygonal_parts(geometry):
    if geometry.geom_type=='Polygon': return [geometry]
    return [p for part in getattr(geometry,'geoms',[]) for p in polygonal_parts(part)]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--envelope',required=True)
    p.add_argument('--walls',required=True)
    p.add_argument('--axes',required=True)
    p.add_argument('--directions',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--profiles-only',action='store_true')
    p.add_argument('--profile-precision-m',type=float,default=0)
    p.add_argument('--contour-simplification-m',type=float,default=0)
    a=p.parse_args(); out=Path(a.output).resolve()
    if not 0<=a.profile_precision_m<=.00005:raise ValueError('Projection precision must be between0 and50um')
    if not np.isfinite(a.contour_simplification_m) or not 0<=a.contour_simplification_m<=.00005:raise ValueError('Contour simplification must be between0 and50um')
    if out.exists(): raise ValueError('Fresh output required')
    out.mkdir(parents=True)
    source=json.loads(Path(a.envelope).read_text(encoding='utf-8'))
    epsilon=source['probe_contract']['epsilon_m']
    distance=source['probe_contract']['max_distance_m']
    axes={x['revit_element_id']:x for x in json.loads(Path(a.axes).read_text(encoding='utf-8'))}
    directions=json.loads(Path(a.directions).read_text(encoding='utf-8'))
    plan={x['id']:x for x in directions['elements']}
    packed=np.load(a.walls); points=packed['vertices'][packed['triangles']]
    triangle_ids=packed['revit_ids']
    zmin=points[:,:,2].min(axis=1); zmax=points[:,:,2].max(axis=1)
    caches={}; records=[]; targets=[]
    for plane in source['candidate_planes']:
        eid=plane['revit_element_id']; decision=plan[eid]
        axis=np.array(axes[eid]['principal_unoriented_axis'],dtype=float); axis/=np.linalg.norm(axis)
        n=np.array(plane['normal']); n[2]=0; n/=np.linalg.norm(n)
        t=np.array([-n[1],n[0],0.])
        measured=np.concatenate([np.array(tri['points_m']) for tri in plane['triangles']])
        d=float(np.median(measured@n))
        planarity_error=float(np.max(abs(measured@n-d)))
        if planarity_error>.002: raise ValueError('Source plane requires separate nonplanar handling: '+str((eid,plane['plane_key'],planarity_error)))
        normals=decision.get('normals', [decision['normal']] if decision.get('normal') is not None else [])
        if not normals:
            continue
        principal=abs(float(n@axis))>.99999
        if principal and max(np.dot(n,np.array(v)/np.linalg.norm(v)) for v in normals)<.99999:
            continue
        if not principal and not decision.get('include_returns',False): continue
        original=profile_of(plane,t)
        raw=profile_of(plane,t,a.profile_precision_m)
        protected_holes=[]
        for part in polygonal_parts(original):
            for ring in part.interiors:
                hole=Polygon(ring)
                uncertainty=hole.length*a.profile_precision_m/2**.5+np.pi*a.profile_precision_m**2
                if hole.area>uncertainty:
                    # A resolved original opening may move within the stated
                    # source precision, but must never become filled surface.
                    intrusion=raw.intersection(hole.buffer(-a.profile_precision_m)).area
                    if intrusion>1e-10:raise ValueError('Resolved source opening was filled by projection precision: '+str(eid))
                    protected_holes.append({'area_m2':hole.area,'precision_intrusion_m2':intrusion})
        if raw.is_empty: continue
        u0,z0,u1,z1=raw.bounds
        # Cached broad phase is keyed by the measured direction. Bounds include
        # source numerical noise but do not snap the modeled coordinates.
        key=tuple(np.round(n,5))
        if key not in caches:
            dn=points@n; ut=points@t
            caches[key]=(dn.min(axis=1),dn.max(axis=1),ut.min(axis=1),ut.max(axis=1))
        dn0,dn1,ut0,ut1=caches[key]
        mask=(dn1>=d+epsilon)&(dn0<=d+epsilon+distance)&(ut1>=u0)&(ut0<=u1)&(zmax>=z0)&(zmin<=z1)
        silhouettes=[]; blocker_ids=set(); projected_contacts=defaultdict(list)
        for index in np.flatnonzero(mask):
            poly=clip(list(points[index]),n,d+epsilon,True)
            if len(poly)<3: continue
            poly=clip(poly,n,d+epsilon+distance,False)
            if len(poly)<3: continue
            verts=np.array(poly); uv=np.column_stack((verts@t,verts[:,2])); silhouette=Polygon(uv)
            if silhouette.area<=1e-10:
                projected_contacts[int(triangle_ids[index])].append(LineString(uv.tolist()+[uv[0].tolist()]))
                continue
            if not silhouette.is_valid: raise ValueError('Invalid source blocker polygon')
            if silhouette.intersects(raw):
                silhouettes.append(silhouette); blocker_ids.add(int(triangle_ids[index]))
        original_occlusion=shapely.union_all(silhouettes) if silhouettes else Polygon()
        occlusion=(shapely.union_all(silhouettes,grid_size=a.profile_precision_m) if a.profile_precision_m else original_occlusion) if silhouettes else Polygon()
        exposed_full=shapely.difference(raw,occlusion,grid_size=a.profile_precision_m) if a.profile_precision_m else raw.difference(occlusion)
        exposed=shapely.union_all(polygonal_parts(exposed_full))
        record={'plane_key':plane['plane_key'],'revit_element_id':eid,'type':plane['revit_type'],
         'normal':n.tolist(),'tangent':t.tolist(),'plane_d_m':d,'direction_basis':decision['basis'],
         'raw_area_m2':raw.area,'exposed_area_m2':exposed.area,
         'vertical_basis_source_deviation_m':planarity_error,
         'profile_precision_m':a.profile_precision_m,
         'max_projected_source_vertex_motion_m':float(np.max(np.linalg.norm(np.column_stack((measured@t,measured[:,2]))-np.rint(np.column_stack((measured@t,measured[:,2]))/a.profile_precision_m)*a.profile_precision_m,axis=1))) if a.profile_precision_m else 0.,
         'original_source_profile':mapping(original),'protected_resolved_source_openings':protected_holes,
         'removed_area_m2':raw.area-exposed.area,'blocker_ids':sorted(blocker_ids),
         'source_profile':mapping(raw),'exposed_profile':mapping(exposed),'status':'covered' if exposed.area<1e-8 else 'pending'}
        if exposed_full.geom_type=='GeometryCollection': record['non_areal_residue']=mapping(exposed_full)
        # Check the exact silhouette against independent native visibility probes.
        sample_mismatches=0; sample_total=0; boundary_uncertain=0; numeric_uncertain=[]
        for triangle in plane['triangles']:
            for sample in triangle['samples']:
                point=np.array(sample['position_m']); uv=shapely.Point(float(point@t),float(point[2]))
                if raw.boundary.distance(uv)<.0001: continue
                if exposed.area>1e-8 and exposed.boundary.distance(uv)<.0001:
                    boundary_uncertain+=1
                    continue
                actual=exposed.covers(uv)
                expected=sample['forward_hit_id'] is None
                sample_total+=1; sample_mismatches+=actual!=expected
                if actual!=expected and a.profile_precision_m:
                    boundary_distance=(original_occlusion.boundary.distance(uv) if not original_occlusion.is_empty else float('inf'))
                    contacts=projected_contacts.get(sample['forward_hit_id'],[])
                    contact_distance=min((contact.distance(uv) for contact in contacts),default=float('inf'))
                    if min(boundary_distance,contact_distance)<=a.profile_precision_m:
                        numeric_uncertain.append({'position_m':point.tolist(),'native_forward_hit_id':sample['forward_hit_id'],
                            'normalized_exposed':bool(actual),'native_clear':bool(expected),
                            'original_occlusion_boundary_distance_m':float(boundary_distance) if np.isfinite(boundary_distance) else None,
                            'projected_degenerate_contact_distance_m':float(contact_distance) if np.isfinite(contact_distance) else None,
                            'reason':'Original geometric boundary/contact within explicit projection precision; native probe and canonical horizontal plane disagree; acceptance pending'})
        record['sample_total']=sample_total; record['sample_mismatches']=sample_mismatches
        record['boundary_uncertain_samples']=boundary_uncertain
        record['numeric_uncertain_samples']=numeric_uncertain
        record['strict_sample_mismatches']=sample_mismatches-len(numeric_uncertain)
        if sample_mismatches:
            record['status']='visibility_discrepancy' if record['strict_sample_mismatches'] else 'probe_numeric_uncertain'
        if exposed.area>=1e-8:
            targets.append((record,exposed))
        records.append(record)
    (out/'profile-checkpoint.json').write_text(json.dumps({'planes':records},ensure_ascii=False),encoding='utf-8')
    if a.profiles_only:
        print(json.dumps({'planes':len(records),'profile_checkpoint':str(out/'profile-checkpoint.json')}))
        return
    vertices=[]; faces=[]; groups=[]; owner_ids=[]; face_normals=[]
    # Coplanar source layers are unioned before meshing, removing duplicate faces.
    coplanar=defaultdict(list)
    for record,shape in targets:
        if record['status']=='visibility_discrepancy': continue
        key=tuple(np.round(record['normal'],5))+(round(record['plane_d_m'],4),)
        coplanar[key].append((record,shape))
    batches=[]
    for entries in coplanar.values():
        # Profiles from slightly different measured normals have distinct UV
        # frames. Project the real planes into one frame before any union;
        # unioning their numeric UV pairs directly invents sliver geometry.
        representative=entries[0][0]
        representative_t=np.array(representative['tangent'])
        common=[]
        for record,profile in entries:
            source_t=np.array(record['tangent']);source_n=np.array(record['normal'])
            profile=affine_transform(profile,[float(source_t@representative_t),0,0,1,
                float(source_n@representative_t)*record['plane_d_m'],0])
            common.append((record,profile))
        entries=common
        combined=(shapely.union_all([profile for _,profile in entries],grid_size=a.profile_precision_m)
                  if a.profile_precision_m else shapely.union_all([profile for _,profile in entries]))
        if a.profile_precision_m:
            # A grid may remove an entire isolated small feature. Preserve such
            # measured features in the common physical frame; precision is not
            # permission to silently delete source components.
            original_combined=shapely.union_all([profile for _,profile in entries])
            omitted=[part for part in polygonal_parts(original_combined)
                     if part.area>1e-10 and part.intersection(combined).area<=0]
            if omitted:
                combined=shapely.union_all([combined,*omitted])
                for record,_ in entries:
                    record['coplanar_precision_restored_components']=[{'area_m2':part.area,'profile':mapping(part)} for part in omitted]
        parts=list(combined.geoms) if combined.geom_type=='MultiPolygon' else [combined]
        for part in parts: batches.append((entries,part))
    for entries,combined in batches:
        representative=entries[0][0]
        relevant=[(r,shape) for r,shape in entries if shape.intersects(combined)]
        parts=[combined]
        try:
            result=rebuild_profile(parts,representative['normal'],representative['tangent'],representative['plane_d_m'])
        except ValueError as error:
            try:
                result=rebuild_irregular(parts,representative['normal'],representative['tangent'],representative['plane_d_m'],contour_simplification_m=a.contour_simplification_m)
                result['qa']['regular_route_rejection']=str(error)
            except ValueError as fallback_error:
                try:
                    # Keep a source component whose topology cannot survive a
                    # second grid operation. This exact route still enforces
                    # convexity, holes, coverage and source intersections.
                    result=rebuild_exact_irregular(parts,representative['normal'],representative['tangent'],representative['plane_d_m'],contour_simplification_m=a.contour_simplification_m)
                    result['qa']['regular_route_rejection']=str(error)
                    result['qa']['normalized_route_rejection']=str(fallback_error)
                except ValueError as exact_error:
                    for record,_ in relevant: record.setdefault('component_results',[]).append({'status':'unsupported_profile','error':str(exact_error),'normalization_error':str(fallback_error),'regular_error':str(error),'profile':mapping(combined)})
                    continue
        smallest=min(Polygon(np.column_stack((np.array([result['vertices_m'][v] for v in face])@representative['tangent'],np.array([result['vertices_m'][v] for v in face])[:,2]))).area for face in result['faces'])
        if smallest<1e-10:
            for record,_ in relevant: record.setdefault('component_results',[]).append({'status':'unsupported_numeric_profile','error':'Near-zero quad area '+str(smallest),'profile':mapping(combined)})
            continue
        offset=len(vertices); start=len(faces); vertices.extend(result['vertices_m'])
        faces.extend([[v+offset for v in f] for f in result['faces']])
        ids=sorted(set(r['revit_element_id'] for r,_ in relevant))
        for record,_ in relevant: record.setdefault('component_results',[]).append({'status':'modeled','area_m2':combined.area})
        groups.append({'source_ids':ids,'source_plane_keys':[r['plane_key'] for r,_ in entries],
          'normal':representative['normal'],'face_start':start,'face_count':len(result['faces']),
          'source_types':{str(r['revit_element_id']):r['type'] for r,_ in entries},
          'qa':result['qa'],'exposed_profile':mapping(combined)})
        face_sources=[]
        for face in result['faces']:
            xyz=np.array([result['vertices_m'][v] for v in face])
            poly=Polygon(np.column_stack((xyz@representative['tangent'],xyz[:,2])))
            contributing=sorted(set(r['revit_element_id'] for r,shape in entries if poly.intersection(shape.buffer(.00005)).area>poly.area*.01))
            if not contributing: raise ValueError('Output face lost source provenance: '+str((ids,poly.area,poly.wkt)))
            face_sources.append(contributing)
            owner_ids.append(contributing[0] if len(contributing)==1 else 0)
        groups[-1]['face_source_ids']=face_sources
        face_normals.extend([representative['normal']]*len(result['faces']))
    for record in records:
        if record.get('component_results'):
            states=[x['status'] for x in record['component_results']]
            record['status']=('modeled_probe_numeric_uncertain' if record.get('numeric_uncertain_samples') else 'modeled') if all(s=='modeled' for s in states) else 'partial_profile' if 'modeled' in states else 'unsupported_profile'
    mesh={'scope':'Measured selected exterior facade surfaces WITHOUT Shell; source coverage and seams require review',
      'vertices_m':vertices,'faces':faces,'owner_ids':owner_ids,'face_normals':face_normals,'groups':groups,
      'source_hashes':{name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in
         [('envelope',a.envelope),('walls',a.walls),('axes',a.axes),('directions',a.directions)]},'delivery_passed':False}
    (out/'body-mesh.json').write_text(json.dumps(mesh,ensure_ascii=False),encoding='utf-8')
    summary={'planes':len(records),'status_counts':dict(Counter(r['status'] for r in records)),
      'modeled_coplanar_groups':len(groups),'quads':len(faces),'vertices':len(vertices),
      'source_selected_ids':len(plan),'pending_direction_ids':[x['id'] for x in directions['elements'] if not x.get('normals', [x['normal']] if x.get('normal') is not None else []) and not x.get('excluded',False)],
      'modeled_union_area_m2':sum(shapely.geometry.shape(g['exposed_profile']).area for g in groups),
      'scope':mesh['scope'],'delivery_passed':False}
    (out/'composition.json').write_text(json.dumps({'summary':summary,'planes':records},ensure_ascii=False),encoding='utf-8')
    print(json.dumps(summary))


if __name__=='__main__': main()

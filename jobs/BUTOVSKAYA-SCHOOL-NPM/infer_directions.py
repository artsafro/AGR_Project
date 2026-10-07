"""Read-only wall direction proposals from actual floor/roof triangle footprints.

No global building-center, bounding-box contour, or clear-area direction heuristics.
Requires explicit measured triangle inputs; keeps undecidable cases unresolved.
"""
import argparse
import json
import hashlib
from collections import defaultdict, Counter
from pathlib import Path

import numpy as np
from shapely.geometry import Point, Polygon, mapping
from shapely.ops import unary_union
from shapely import set_precision


def self_test(output):
    """Three scoped synthetic cases; these do not establish school acceptance."""
    from shapely.ops import triangulate
    root=Path(output)
    if root.exists(): raise RuntimeError('Fresh self-test output directory required')
    root.mkdir(parents=True)
    floor=Polygon([(0,0),(10,0),(10,10),(0,10)],holes=[[(4,4),(4,6),(6,6),(6,4)]])
    triangles=[{'source_polygon_index':i,'points_m':[[x,y,0.] for x,y in list(t.exterior.coords)[:-1]]}
               for i,t in enumerate(triangulate(floor)) if floor.covers(t)]
    footprints={'units':'metres','source_reference':'SYNTHETIC_NEGATIVE_CASE',
                'elements':[{'revit_element_id':-101,'revit_type':'Synthetic courtyard floor','triangles':triangles}]}
    planes=[]
    for eid,x,ys in [(-201,10,(2,8)),(-202,4,(4.2,5.8)),(-203,2,(2,8))]:
        a=[x,ys[0],.6]; b=[x,ys[1],.6]; c=[x,ys[1],4.]; d=[x,ys[0],4.]
        planes.append({'revit_element_id':eid,'normal':[1,0,0],'area_m2':(ys[1]-ys[0])*3.4,
                       'triangles':[{'points_m':[a,b,c]},{'points_m':[a,c,d]}]})
    inputs={'footprints':footprints,'envelope':{'candidate_planes':planes},
            'directions':{'elements':[{'id':x['revit_element_id'],'normals':[]} for x in planes]}}
    paths={}
    for name,data in inputs.items():
        paths[name]=root/(name+'.json'); paths[name].write_text(json.dumps(data),encoding='utf-8')
    result=main(['--footprints',str(paths['footprints']),'--envelope',str(paths['envelope']),
                 '--directions',str(paths['directions']),'--output',str(root/'result'),'--write-proposed-plan'])
    rows={r['id']:r for r in result}
    assert rows[-201]['normals']==[[1.,0.,0.]],'External wall direction failed'
    assert rows[-202]['normals']==[[1.,0.,0.]],'Courtyard direction failed'
    assert rows[-203]['normals']==[],'Interior wall must remain unknown'
    stored=json.loads((root/'result/footprints.json').read_text(encoding='utf-8'))
    assert len(stored['footprints'][0]['union']['coordinates'])==2,'Courtyard hole lost'
    proposal=json.loads((root/'result/proposed-direction-plan.json').read_text(encoding='utf-8'))
    assert proposal['proposal_only'] is True and len(proposal['elements'])==3
    receipt={'synthetic':True,'cases':3,'passed':True,'case_names':['external_direction','courtyard_direction_and_preserved_hole','interior_remains_unknown'],
             'school_acceptance':False}
    (root/'self-test.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt))


def main(argv=None):
    parser=argparse.ArgumentParser()
    for name in ('footprints','envelope','directions'):
        parser.add_argument('--'+name)
    parser.add_argument('--output',required=True)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--write-proposed-plan',action='store_true',help='Write proposal-only copy preserving prior IDs and established directions')
    args=parser.parse_args(argv)
    if args.self_test:
        if any(getattr(args,x) for x in ('footprints','envelope','directions')):
            parser.error('--self-test cannot use external source inputs')
        self_test(args.output)
        return
    if not all(getattr(args,x) for x in ('footprints','envelope','directions')):
        parser.error('--footprints, --envelope and --directions are required outside --self-test')
    target=Path(args.output)
    if target.exists(): raise RuntimeError('Fresh output directory required')
    floors=json.loads(Path(args.footprints).read_text(encoding='utf-8'))
    if floors.get('units')!='metres': raise RuntimeError('Explicit metre unit contract required')
    envelope=json.loads(Path(args.envelope).read_text(encoding='utf-8'))
    plan=json.loads(Path(args.directions).read_text(encoding='utf-8'))
    input_bindings={name:{'path':str(Path(getattr(args,name)).resolve()),
                          'sha256':hashlib.sha256(Path(getattr(args,name)).read_bytes()).hexdigest()}
                    for name in ('footprints','envelope','directions')}
    input_bindings['script']={'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    input_ids=[x['id'] for x in plan['elements']]
    if len(set(input_ids))!=len(input_ids): raise RuntimeError('Duplicate explicit direction IDs')
    grid=.00005; level_grid=.05
    strata=defaultdict(lambda:defaultdict(list)); source_elevations=defaultdict(list)
    skipped=Counter()
    for element in floors['elements']:
        eid=int(element['revit_element_id'])
        for tri in element['triangles']:
            points=np.asarray(tri['points_m'],dtype=np.float64)
            n=np.cross(points[1]-points[0],points[2]-points[0]); length=np.linalg.norm(n)
            if length<1e-10: skipped['degenerate']+=1; continue
            n/=length
            # This route deliberately requires measured horizontal supporting faces.
            if abs(n[2])<.99999 or np.ptp(points[:,2])>.002:
                skipped['nonhorizontal']+=1; continue
            z=float(np.mean(points[:,2])); key=round(z/level_grid)*level_grid
            polygon=set_precision(Polygon(points[:,:2]),grid)
            if polygon.is_empty: skipped['collapsed_projected_triangle']+=1; continue
            strata[key][eid].append(polygon); source_elevations[key].append(z)
    footprints={z:{eid:unary_union(ps) for eid,ps in elements.items()} for z,elements in strata.items()}
    union={z:unary_union(list(elements.values())) for z,elements in footprints.items()}
    planes=defaultdict(list)
    for q in envelope['candidate_planes']: planes[q['revit_element_id']].append(q)
    receipts=[]
    offsets=[.1,.25,.5,1.]
    barycentrics=np.array([[1/3,1/3,1/3],[.6,.2,.2],[.2,.6,.2],[.2,.2,.6]])
    for element in plan['elements']:
        if element.get('normals'): continue
        eid=element['id']; ps=planes[eid]
        if not ps:
            receipts.append({'id':eid,'normals':[],'reason':'No measured vertical wall planes'}); continue
        totals=defaultdict(float)
        for q in ps:
            n=np.asarray(q['normal']); sign=1 if n[0]>1e-6 or (abs(n[0])<=1e-6 and n[1]>0) else -1
            totals[tuple(np.round(n*sign,4))]+=q['area_m2']
        axis=np.asarray(max(totals,key=totals.get),dtype=np.float64); axis/=np.linalg.norm(axis)
        candidates=[q for q in ps if np.dot(q['normal'],axis)>.9999]
        if not candidates:
            receipts.append({'id':eid,'normals':[],'reason':'No measured positive-axis wall face'}); continue
        source_points=np.concatenate([barycentrics @ np.asarray(tri['points_m']) for q in candidates for tri in q['triangles']])
        allpts=np.concatenate([np.asarray(tri['points_m']) for q in candidates for tri in q['triangles']])
        wall_base=float(min(allpts[:,2])); wall_top=float(max(allpts[:,2]))
        tangent=np.array([-axis[1],axis[0],0.])
        source_points=source_points[np.argsort(source_points@tangent)]
        source_points=source_points[np.unique(np.linspace(0,len(source_points)-1,min(15,len(source_points))).astype(int))]
        # Physical base support: nearest actual horizontal face not over1.25m away.
        support_levels=[z for z in footprints if wall_base-1.25<=float(np.median(source_elevations[z]))<=wall_base+.25]
        proximity={z:sum(union[z].distance(Point(point[:2]))<=1.05 for point in source_points) for z in support_levels}
        support_levels=[z for z in support_levels if proximity[z]>=3 and proximity[z]/len(source_points)>=.25]
        if not support_levels:
            receipts.append({'id':eid,'normals':[],'wall_z_range_m':[wall_base,wall_top],'reason':'No horizontal floor/roof support within1.25m of measured wall base'}); continue
        minimum=min(abs(float(np.median(source_elevations[z]))-wall_base) for z in support_levels)
        support_levels=[z for z in support_levels if abs(float(np.median(source_elevations[z]))-wall_base)<=minimum+.25]
        probes=[]; robust_point_signs=[]; offset_signs=defaultdict(list)
        for index,point in enumerate(source_points):
            decisions=[]
            for z in support_levels:
                poly=union[z]
                for offset in offsets:
                    xy_plus=point[:2]+axis[:2]*offset; xy_minus=point[:2]-axis[:2]*offset
                    plus,minus=Point(xy_plus),Point(xy_minus)
                    clearance=min(plus.distance(poly.boundary),minus.distance(poly.boundary))
                    inside_plus=poly.contains(plus); inside_minus=poly.contains(minus)
                    # Near a measured footprint boundary is deliberately uninformative.
                    sign=1 if not inside_plus and inside_minus else -1 if inside_plus and not inside_minus else 0
                    if clearance<.005: sign=0
                    if sign: decisions.append(sign); offset_signs[offset].append(sign)
                    interior=minus if sign==1 else plus if sign==-1 else None
                    interior_ids=[i for i,p in footprints[z].items() if interior is not None and p.covers(interior)]
                    plus_ids=[i for i,p in footprints[z].items() if p.covers(plus)]
                    minus_ids=[i for i,p in footprints[z].items() if p.covers(minus)]
                    probes.append({'wall_sample_index':index,'source_wall_point_m':point.tolist(),'support_z_m':float(np.median(source_elevations[z])),
                                   'support_level_bucket_m':z,'offset_m':offset,'plus_xy_m':xy_plus.tolist(),'minus_xy_m':xy_minus.tolist(),
                                   'plus_inside':inside_plus,'minus_inside':inside_minus,'boundary_clearance_m':clearance,
                                   'inferred_sign':sign,'support_interior_ids':interior_ids,
                                   'plus_support_ids':plus_ids,'minus_support_ids':minus_ids})
            if len(decisions)>=2 and max(Counter(decisions).values())/len(decisions)>=.9:
                robust_point_signs.append(Counter(decisions).most_common(1)[0][0])
        counts=Counter(robust_point_signs); preferred=counts.most_common(1)[0][0] if counts else 0
        offset_consensus=sum(bool(v) and Counter(v).get(preferred,0)/len(v)>=.9 for v in offset_signs.values())
        resolved=len(robust_point_signs)>=3 and counts.get(preferred,0)/len(robust_point_signs)>=.9 and offset_consensus>=3
        receipts.append({'id':eid,'normals':[(axis*preferred).tolist()] if resolved else [],
                         'wall_z_range_m':[wall_base,wall_top],'support_level_buckets_m':support_levels,
                         'local_support_proximity_sample_counts':proximity,
                         'status':'proposed_by_actual_floor_footprint_consensus' if resolved else 'unknown',
                         'basis':'Measured triangle footprint union, actual source wall points, both normal sides at4 offsets; at least3 source locations and3 offsets agree with90percent consensus.',
                         'reason':None if resolved else 'Insufficient or contradictory physical footprint side evidence',
                         'robust_point_sign_counts':dict(counts),'offset_consensus_count':offset_consensus,'probes':probes})
    target.mkdir(parents=True)
    artifact={'grid_m':grid,'level_bucket_m':level_grid,'source':floors.get('source_reference'),'skipped_triangles':dict(skipped),
              'footprints':[{'level_bucket_m':z,'source_z_values_m':source_elevations[z],
                             'by_id':{eid:mapping(poly) for eid,poly in elements.items()},'union':mapping(union[z])} for z,elements in footprints.items()]}
    (target/'footprints.json').write_text(json.dumps(artifact),encoding='utf-8')
    (target/'direction-receipts.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
    manifest={'proposal_only':True,'input_bindings':input_bindings,'support_source_reference_sha256_claim':floors.get('source_sha256'),
              'source_geometry_acceptance':False,'input_element_count':len(input_ids),'input_unknown_count':len(receipts),
              'proposed_count':sum(bool(x['normals']) for x in receipts),'unknown_ids':[x['id'] for x in receipts if not x['normals']]}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    if args.write_proposed_plan:
        by_id={x['id']:x for x in receipts}
        for element in plan['elements']:
            if element.get('normals') or element['id'] not in by_id: continue
            receipt=by_id[element['id']]
            element['normals']=receipt['normals']
            element['footprint_direction_receipt']='direction-receipts.json'
            element['status']=receipt.get('status','unknown')
            element['basis']=receipt.get('basis',receipt.get('reason'))
            element['reason']=receipt.get('reason')
        assert [x['id'] for x in plan['elements']]==input_ids
        plan['proposal_only']=True
        plan['footprint_input_bindings']=input_bindings
        plan['source_geometry_acceptance']=False
        plan['unresolved_ids']=[x['id'] for x in plan['elements'] if not x.get('normals')]
        plan['status_counts']=dict(Counter(x.get('status','unspecified') for x in plan['elements']))
        (target/'proposed-direction-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'input_unknowns':len(receipts),'proposed':sum(bool(x['normals']) for x in receipts),'unknown_ids':[x['id'] for x in receipts if not x['normals']]}))
    return receipts


if __name__=='__main__': main()

"""Refine source attribution without changing any modeled vertex or quad."""
import argparse, json, hashlib
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon, shape
from shapely.affinity import affine_transform

p=argparse.ArgumentParser();p.add_argument('--mesh',required=True);p.add_argument('--composition',required=True);p.add_argument('--output',required=True)
a=p.parse_args();out=Path(a.output).resolve()
if out.exists():raise ValueError('Fresh output required')
data=json.loads(Path(a.mesh).read_text(encoding='utf-8'))
records={r['plane_key']:r for r in json.loads(Path(a.composition).read_text(encoding='utf-8'))['planes']}
coordinates=np.array(data['vertices_m']);changed=0;buffered=0
for group in data['groups']:
    normal=np.array(group['normal']);t=np.array([-normal[1],normal[0],0.])
    sources={}
    for key in group['source_plane_keys']:
        record=records[key];old_t=np.array(record['tangent']);old_n=np.array(record['normal'])
        transformed=affine_transform(shape(record['exposed_profile']),[float(old_t@t),0,0,1,float(old_n@t)*record['plane_d_m'],0])
        sources.setdefault(record['revit_element_id'],[]).append(transformed)
    sources={eid:shapely.union_all(parts) for eid,parts in sources.items()}
    ids_per_face=[];areas_per_face=[];bases=[]
    for local_index,fi in enumerate(range(group['face_start'],group['face_start']+group['face_count'])):
        xyz=coordinates[data['faces'][fi]];poly=Polygon(np.column_stack((xyz@t,xyz[:,2])))
        areas={eid:float(poly.intersection(profile).area) for eid,profile in sources.items()}
        positive={eid:area for eid,area in areas.items() if area>0}
        basis='positive exact projected intersection; all portions retained'
        if not positive:
            positive={eid:0. for eid,profile in sources.items() if poly.intersection(profile.buffer(.000075)).area>0}
            basis='within explicit source normalization tolerance only; semantic acceptance pending';buffered+=1
        if not positive:raise ValueError('No source attribution within measured tolerance')
        ids=sorted(positive)
        changed+=ids!=group['face_source_ids'][local_index]
        ids_per_face.append(ids);areas_per_face.append({str(eid):area for eid,area in positive.items()});bases.append(basis)
        data['owner_ids'][fi]=ids[0] if len(ids)==1 else 0
    group['face_source_ids']=ids_per_face
    group['face_source_intersection_areas_m2']=areas_per_face
    group['face_attribution_basis']=bases
data['source_hashes']['geometry_before_attribution']=hashlib.sha256(Path(a.mesh).read_bytes()).hexdigest()
data['source_hashes']['composition_before_attribution']=hashlib.sha256(Path(a.composition).read_bytes()).hexdigest()
out.mkdir(parents=True)
(out/'body-mesh.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
original=json.loads(Path(a.mesh).read_text(encoding='utf-8'))
receipt={'vertices_unchanged':original['vertices_m']==data['vertices_m'],'faces_unchanged':original['faces']==data['faces'],
         'face_attributions_changed':changed,'buffered_only_faces':buffered,'delivery_passed':False}
(out/'attribution-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))

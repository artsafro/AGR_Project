"""Read actual saved Blender coordinates and original face/vertex mappings."""
import argparse,json,sys,hashlib
from pathlib import Path
import bpy
import numpy as np

p=argparse.ArgumentParser();p.add_argument('--blend',required=True);p.add_argument('--mesh-source',required=True);p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if not bpy.app.background:raise RuntimeError('Background-only readback')
blend=Path(a.blend).resolve();out=Path(a.output).resolve()
if out.exists():raise ValueError('Fresh output required')
digest=hashlib.sha256(blend.read_bytes()).hexdigest()
source=json.loads(Path(a.mesh_source).read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(blend))
vertices=[None]*len(source['vertices_m']);faces=[None]*len(source['faces']);normals=[None]*len(faces)
element_ids=[None]*len(faces);group_indices=[None]*len(faces)
for obj in bpy.context.scene.objects:
    if obj.type!='MESH':continue
    mesh=obj.data;ids=[v.value for v in mesh.attributes['source_vertex_index'].data]
    face_ids=[f.value for f in mesh.attributes['source_face_index'].data]
    matrix=np.array(obj.matrix_world,dtype=float)
    xyz=np.array([list(v.co) for v in mesh.vertices])@matrix[:3,:3].T+matrix[:3,3]
    for index,point in zip(ids,xyz):
        if vertices[index] is not None:raise ValueError('Duplicate source vertex mapping')
        vertices[index]=point.tolist()
    for face,index in zip(mesh.polygons,face_ids):
        if faces[index] is not None:raise ValueError('Duplicate source face mapping')
        faces[index]=[ids[v] for v in face.vertices]
        n=matrix[:3,:3]@np.array(face.normal);normals[index]=(n/np.linalg.norm(n)).tolist()
        element_ids[index]=int(mesh.attributes['revit_element_id'].data[face.index].value)
        group_indices[index]=int(mesh.attributes['source_group_index'].data[face.index].value)
if any(v is None for v in vertices) or any(f is None for f in faces):raise ValueError('Missing source mapping')
if faces!=source['faces']:raise ValueError('Native face mismatch')
registry=json.loads(bpy.data.objects['BODY_S1_without_Shell']['source_group_registry'])
expected_groups=[None]*len(faces)
for gi,group in enumerate(source['groups']):
    for fi in range(group['face_start'],group['face_start']+group['face_count']):expected_groups[fi]=gi
if element_ids!=source['owner_ids'] or group_indices!=expected_groups or registry!=source['groups']:
    raise ValueError('Native source attribution/group registry mismatch')
if hashlib.sha256(blend.read_bytes()).hexdigest()!=digest:raise ValueError('Master altered')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({'vertices_m':vertices,'faces':faces,'face_normals':normals,
 'revit_element_ids':element_ids,'source_group_indices':group_indices,'source_group_registry':registry,
 'saved_master':str(blend),'master_sha256':digest,'source_mesh_sha256':hashlib.sha256(Path(a.mesh_source).read_bytes()).hexdigest(),'read_only':True}),encoding='utf-8')
print(json.dumps({'vertices':len(vertices),'faces':len(faces),'master_sha256':digest}))

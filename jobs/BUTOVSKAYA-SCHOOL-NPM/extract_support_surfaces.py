"""Read actual support floor/roof triangles for exterior-direction investigation."""
import argparse,json,sys,hashlib
from pathlib import Path
import bpy,numpy as np

p=argparse.ArgumentParser()
for key in ['reference','inventory','output']:p.add_argument('--'+key,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if not bpy.app.background:raise RuntimeError('Background read-only')
reference=Path(a.reference).resolve();out=Path(a.output).resolve()
if out.exists():raise ValueError('Fresh output required')
inventory=json.loads(Path(a.inventory).read_text(encoding='utf-8'))
selected={int(o['revit_metadata']['elementId']):o['revit_metadata'] for o in inventory['objects'] if o.get('revit_metadata',{}).get('category') in ['Перекрытия','Крыши']}
digest=hashlib.sha256(reference.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(reference));elements=[]
for obj in bpy.context.scene.objects:
    eid=int(obj.get('revit_element_id',-1))
    if obj.type!='MESH' or eid not in selected:continue
    matrix=np.array(obj.matrix_world,dtype=float)
    pts=np.array([list(v.co) for v in obj.data.vertices])@matrix[:3,:3].T+matrix[:3,3]
    obj.data.calc_loop_triangles();triangles=[]
    for index,tri in enumerate(obj.data.loop_triangles):
        xyz=pts[list(tri.vertices)];normal=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);size=np.linalg.norm(normal)
        if size<1e-12:continue
        normal/=size
        if abs(normal[2])<.1:continue
        triangles.append({'source_polygon_index':index,'points_m':xyz.tolist(),'normal':normal.tolist(),'area_m2':float(size/2)})
    if triangles:elements.append({'revit_element_id':eid,'revit_type':selected[eid]['type'],'category':selected[eid]['category'],'source_object':obj.name,'triangles':triangles})
if hashlib.sha256(reference.read_bytes()).hexdigest()!=digest:raise ValueError('Source changed')
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'source_reference':str(reference),'source_sha256':digest,'units':'metres','elements':elements,'limitations':['Measured projected support surfaces inform direction only; do not constitute BODY geometry. Sloped triangles retain original normals and world coordinates.']},ensure_ascii=False),encoding='utf-8')
print(json.dumps({'elements':len(elements),'triangles':sum(len(e['triangles']) for e in elements)}))

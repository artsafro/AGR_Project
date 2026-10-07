"""Read-only source wall plane inventory in a separate background Blender."""
import argparse, json, sys
from pathlib import Path
from collections import defaultdict
import bpy
from mathutils import Vector

a=argparse.ArgumentParser()
a.add_argument('--reference',required=True)
a.add_argument('--output',required=True)
args=a.parse_args(sys.argv[sys.argv.index('--')+1:])
if not bpy.app.background: raise RuntimeError('Separate background Blender required; live use forbidden')
p=Path(args.output); p.mkdir(parents=True,exist_ok=True)
if (p/'panels.json').exists(): raise RuntimeError('Output already exists')
bpy.ops.wm.open_mainfile(filepath=args.reference)
panels=[]
for o in bpy.context.scene.objects:
    if o.type!='MESH': continue
    # Source importer assigns canonical metadata; no name-only ID recovery here.
    source_type=o.get('revit_type','')
    if not source_type.startswith('НР_Ут 150_НФС 100'): continue
    vertices=[o.matrix_world@v.co for v in o.data.vertices]
    groups=defaultdict(list)
    for f in o.data.polygons:
        pts=[vertices[i] for i in f.vertices]
        normal=(pts[1]-pts[0]).cross(pts[2]-pts[0])
        if normal.length<1e-10: continue
        normal.normalize()
        if abs(normal.z)>1e-5: continue
        d=normal.dot(pts[0])
        key=tuple(round(x,5) for x in normal)+ (round(d,4),)
        groups[key].append((f,pts,normal,d))
    for values in groups.values():
        area=sum(f.area for f,_,_,_ in values)*abs(o.matrix_world.to_3x3().determinant())**(2/3)
        if area<5: continue
        normal=values[0][2]; d=values[0][3]
        tangent=Vector((-normal.y,normal.x,0))
        polygons=[[ [v.dot(tangent),v.z] for v in pts] for _,pts,_,_ in values]
        panels.append({'source_object':o.name,'revit_element_id':int(o['revit_element_id']),
          'revit_type':source_type,'normal':list(normal),'plane_d_m':d,
          'tangent':list(tangent),'material_indices':[f.material_index for f,_,_,_ in values],
          'polygons_2d_m':polygons,'source_area_m2_approx':area,
          'material_names':[m.name if m else None for m in o.data.materials]})
(p/'panels.json').write_text(json.dumps(panels,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'panels':len(panels),'source_objects':len(set(x['source_object'] for x in panels))}))

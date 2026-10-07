"""Render measured Revit wall solids with the BODY preview's exact cameras.

Read-only native comparison: keeps source thickness, openings and transforms.
The selected walls include unresolved candidates; this is not exterior acceptance.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

p=argparse.ArgumentParser()
for name in ('body','reference','directions','output'):p.add_argument('--'+name,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if not bpy.app.background:raise RuntimeError('Read-only background process required')
paths={name:Path(getattr(a,name)).resolve() for name in ('body','reference','directions')}
hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths.items()}
out=Path(a.output).resolve()
if out.exists():raise ValueError('Fresh output required')
out.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(paths['body']))
points=np.array([tuple(o.matrix_world@v.co) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices])
center=Vector((points.min(axis=0)+points.max(axis=0))/2)
extent=float(np.linalg.norm(points.max(axis=0)-points.min(axis=0)))
ids={str(e['id']) for e in json.loads(paths['directions'].read_text(encoding='utf-8'))['elements']}
bpy.ops.wm.open_mainfile(filepath=str(paths['reference']))
selected=[]
for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    keep=str(o.get('revit_element_id','')) in ids
    o.hide_render=not keep
    if keep:selected.append(o);o.color=(.36,.58,.73,1)
if {str(o['revit_element_id']) for o in selected}!=ids:raise ValueError('Selected source wall IDs missing')
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='OBJECT'
scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD'
scene.world=bpy.data.worlds.new('Transient_comparison_world');scene.world.color=(.93,.94,.96)
camera_data=bpy.data.cameras.new('Transient_comparison_camera')
camera=bpy.data.objects.new('Transient_comparison_camera',camera_data);scene.collection.objects.link(camera)
camera_data.type='ORTHO';scene.camera=camera
scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
cameras={}
for name,direction in [('SE',(1,-1,.65)),('NW',(-1,1,.65))]:
    unit=Vector(direction).normalized();camera.location=center+unit*extent*2
    camera.rotation_euler=(-unit).to_track_quat('-Z','Y').to_euler()
    rotation=camera.rotation_euler.to_quaternion()
    right=np.array(rotation@Vector((1,0,0)));up=np.array(rotation@Vector((0,1,0)))
    camera_data.ortho_scale=max(float(np.ptp(points@right)),float(np.ptp(points@up))*1.5)*1.12
    cameras[name]={'location':list(camera.location),'rotation_euler':list(camera.rotation_euler),'ortho_scale':camera_data.ortho_scale}
    scene.render.filepath=str(out/('REVIT_SELECTED_WALLS_'+name+'.png'));bpy.ops.render.render(write_still=True)
if hashes!={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths.items()}:raise ValueError('Preview changed an input')
(out/'comparison-receipt.json').write_text(json.dumps({'inputs':{k:str(v) for k,v in paths.items()},'sha256':hashes,
    'selected_source_ids':len(ids),'source_meshes':len(selected),'cameras':cameras,'inputs_unchanged':True,
    'scope':'Selected original Revit wall solids; compare with BODY_SE/NW_wire.png from native master build. Includes unresolved wall candidates; windows/roof are later stages.',
    'visual_accepted':False,'delivery_passed':False},indent=2),encoding='utf-8')

"""Read a saved BODY and render fitting cameras without resaving its geometry."""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

p=argparse.ArgumentParser();p.add_argument('--blend',required=True);p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if not bpy.app.background:raise RuntimeError('Background-only preview')
source=Path(a.blend).resolve();out=Path(a.output).resolve()
if out.exists():raise ValueError('Fresh output required')
out.mkdir(parents=True);digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=np.array([tuple(o.matrix_world@v.co) for o in objects for v in o.data.vertices])
center=Vector((points.min(axis=0)+points.max(axis=0))/2);radius=float(np.linalg.norm(points.max(axis=0)-points.min(axis=0)))
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='OBJECT'
scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('Transient_preview_world');scene.world.color=(.93,.94,.96)
curve=bpy.data.curves.new('Transient_wire_NOT_master','CURVE');curve.dimensions='3D';curve.bevel_depth=.008;curve.bevel_resolution=0
for o in objects:
    for edge in o.data.edges:
        spline=curve.splines.new('POLY');spline.points.add(1)
        for point,index in zip(spline.points,edge.vertices):point.co=(*(o.matrix_world@o.data.vertices[index].co),1)
wire=bpy.data.objects.new('Transient_wire',curve);scene.collection.objects.link(wire);wire.color=(.07,.10,.14,1)
camera_data=bpy.data.cameras.new('Transient_camera');camera=bpy.data.objects.new('Transient_camera',camera_data);scene.collection.objects.link(camera)
camera_data.type='ORTHO';scene.camera=camera
scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
for name,direction in [('SE',(1,-1,.65)),('NW',(-1,1,.65)),('NE',(1,1,.65)),('SW',(-1,-1,.65))]:
    unit=Vector(direction).normalized();camera.location=center+unit*radius*2
    rotation=(-unit).to_track_quat('-Z','Y');camera.rotation_euler=rotation.to_euler()
    right=np.array(rotation@Vector((1,0,0)));up=np.array(rotation@Vector((0,1,0)))
    width=float(np.ptp(points@right));height=float(np.ptp(points@up))
    camera_data.ortho_scale=max(width,height*1.5)*1.12
    scene.render.filepath=str(out/('BODY_'+name+'_wire.png'));bpy.ops.render.render(write_still=True)
if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:raise ValueError('Read-only preview altered master')
(out/'preview-receipt.json').write_text(json.dumps({'source_blend':str(source),'source_sha256':digest,'master_unchanged':True,'views':['SE','NW','NE','SW'],'visual_accepted':False},indent=2),encoding='utf-8')

"""Build/read back a measured single exterior surface, then render its wire grid."""
import argparse, json, sys, hashlib, re
from pathlib import Path
from collections import Counter
import bpy
import numpy as np
from mathutils import Vector

p=argparse.ArgumentParser(); p.add_argument('--mesh',required=True); p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]); out=Path(a.output).resolve()
if not bpy.app.background: raise RuntimeError('Separate background Blender required; live use forbidden')
out.mkdir(parents=True,exist_ok=True)
version=re.search(r'v\d+$',out.name)
if not version: raise ValueError('Output directory must end with vNNN')
blend=out/('BUTOVSKAYA_BODY_EAST_PANEL_'+version.group()+'.blend')
if blend.exists(): raise RuntimeError('Refuse overwrite')
source=Path(a.mesh).resolve(); data=json.loads(source.read_text(encoding='utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
collection=bpy.data.collections.new('01_BODY_exterior_pilot'); scene.collection.children.link(collection)
mesh=bpy.data.meshes.new('BODY_quad_surface'); mesh.from_pydata(data['vertices_m'],[],data['faces']); mesh.update()
mesh.attributes.new('revit_element_id','INT','FACE').data.foreach_set('value',[data['source']['revit_element_id']]*len(mesh.polygons))
mesh.attributes.new('source_material_index','INT','FACE').data.foreach_set('value',[0]*len(mesh.polygons))
o=bpy.data.objects.new('BODY_EAST_PANEL_source_'+str(data['source']['revit_element_id']),mesh); collection.objects.link(o)
o['revit_element_id']=data['source']['revit_element_id']; o['scope']=data['scope']; o['source_mesh_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
o['stage']='S1 exterior surface WITHOUT thickness'; o['material_status']='source names retained as metadata; shader not accepted'
o['source_material_names']=json.dumps(data['source']['material_names'],ensure_ascii=False)
o.show_wire=True; o.show_all_edges=True; o.color=(0.68,0.70,0.74,1)
scene['source_coordinate_system']='Revit internal metres preserved, no arbitrary project repositioning'
scene['delivery_passed']=False
bpy.context.view_layer.objects.active=o; o.select_set(True)
center=sum((v.co for v in mesh.vertices),Vector())/len(mesh.vertices)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_location=center
            area.spaces.active.region_3d.view_distance=35
            area.spaces.active.region_3d.view_rotation=(Vector(data['source']['normal'])*-1).to_track_quat('-Z','Y')
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.wm.open_mainfile(filepath=str(blend))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH'); mesh=o.data
counts=Counter(len(f.vertices) for f in mesh.polygons)
coords=[list(v.co) for v in mesh.vertices]
faces=[list(f.vertices) for f in mesh.polygons]
norm=Vector(data['source']['normal'])
qa={'blend':str(blend),'source_mesh_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'vertex_count':len(coords),'face_sizes':dict(counts),'zero_area_faces':sum(f.area<1e-10 for f in mesh.polygons),
 'wrong_normals':sum(f.normal.dot(norm)<0.99999 for f in mesh.polygons),
 'max_coordinate_readback_error_m':float(np.linalg.norm(np.array(coords,dtype=np.float64)-np.array(data['vertices_m'],dtype=np.float64),axis=1).max()),
 'faces_match':faces==data['faces'],'unique_positions':len(set(tuple(v) for v in coords)),
 'mesh_validate_changed':mesh.validate(clean_customdata=False),'visual_acceptance':'pending','delivery_passed':False}
if counts!={4:len(faces)} or qa['zero_area_faces'] or qa['wrong_normals'] or not qa['faces_match'] or qa['mesh_validate_changed'] or qa['max_coordinate_readback_error_m']>0.002:
    raise ValueError(qa)
qa['blend_sha256']=hashlib.sha256(blend.read_bytes()).hexdigest()
(out/'panel-readback.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
# Preview is a separate scene state in this background process; saved master stays untouched.
scene=bpy.context.scene; scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'; scene.display.shading.color_type='OBJECT'
scene.display.shading.show_shadows=False; scene.display.shading.show_cavity=False
scene.display.shading.background_type='WORLD'; scene.world=bpy.data.worlds.new('PreviewWorld'); scene.world.color=(0.95,0.95,0.95)
edges=bpy.data.curves.new('Preview_grid_not_model','CURVE'); edges.dimensions='3D'; edges.bevel_depth=.009; edges.bevel_resolution=0
for e in mesh.edges:
    spline=edges.splines.new('POLY'); spline.points.add(1)
    for point,index in zip(spline.points,e.vertices):
        v=mesh.vertices[index].co+norm*.004; point.co=(*v,1)
wire=bpy.data.objects.new('Preview_edges_only',edges); scene.collection.objects.link(wire); wire.color=(.06,.08,.12,1)
cam_data=bpy.data.cameras.new('Preview_camera'); camera=bpy.data.objects.new('Preview_camera',cam_data); scene.collection.objects.link(camera)
camera.location=center+norm*80; camera.rotation_euler=(-norm).to_track_quat('-Z','Y').to_euler(); cam_data.type='ORTHO'
t=Vector(data['source']['tangent']); width=max(v.co.dot(t) for v in mesh.vertices)-min(v.co.dot(t) for v in mesh.vertices)
height=max(v.co.z for v in mesh.vertices)-min(v.co.z for v in mesh.vertices)
cam_data.ortho_scale=max(width,height*1.6)*1.12
camera.location=norm*(data['source']['plane_d_m']+80)+t*((max(v.co.dot(t) for v in mesh.vertices)+min(v.co.dot(t) for v in mesh.vertices))/2)+Vector((0,0,(max(v.co.z for v in mesh.vertices)+min(v.co.z for v in mesh.vertices))/2))
scene.camera=camera; scene.render.resolution_x=1600; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.render.filepath=str(out/'BODY_EAST_PANEL_wire.png'); bpy.ops.render.render(write_still=True)
print(json.dumps(qa))

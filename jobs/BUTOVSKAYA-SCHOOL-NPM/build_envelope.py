"""Save a separate measured BODY stage and verify native Blender readback."""
import argparse, json, sys, hashlib
from pathlib import Path
from collections import Counter, defaultdict
import bpy
import numpy as np
from mathutils import Vector, Matrix


p=argparse.ArgumentParser()
p.add_argument('--mesh',required=True); p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if not bpy.app.background: raise RuntimeError('Separate background process required')
out=Path(a.output).resolve()
if out.exists(): raise ValueError('Fresh output required')
out.mkdir(parents=True)
source=Path(a.mesh).resolve(); data=json.loads(source.read_text(encoding='utf-8'))
if not data['faces']: raise ValueError('Empty BODY')
if not all('face_source_intersection_areas_m2' in group and 'face_attribution_basis' in group for group in data['groups']):
    raise ValueError('Run refine_provenance before native master creation')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'
body=bpy.data.collections.new('01_BODY_measured_facade_surfaces'); scene.collection.children.link(body)
group_indices=[0]*len(data['faces'])
for index,group in enumerate(data['groups']):
    for face in range(group['face_start'],group['face_start']+group['face_count']): group_indices[face]=index
obj=bpy.data.objects.new('BODY_S1_without_Shell',None); body.objects.link(obj)
obj['source_group_registry']=json.dumps(data['groups'],ensure_ascii=False)
obj['scope']=data['scope']; obj['stage']='S1 WITHOUT thickness; coverage and junction verification pending'
obj['mesh_input_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
obj['material_status']='Neutral preview only; source finish IDs are metadata, UV pending'
scene['delivery_passed']=False; scene['visual_accepted']=False
scene['source_coordinates']='Revit internal metres retained'
coords=np.array(data['vertices_m']); low=coords.min(axis=0); high=coords.max(axis=0)
center=Vector((low+high)/2); extent=float(np.linalg.norm(high-low))
# World-space float32 vertices rotate normals of small diagonal quads. Keep
# measured planes in local XY and retain the world placement in object matrices.
# Every projection and native world-coordinate displacement is measured below.
families=defaultdict(list)
for index,n in enumerate(data['face_normals']): families[tuple(np.round(n,5))].append(index)
projection_error=0.
for family_index,(key,face_indices) in enumerate(families.items()):
    n=np.array(key,dtype=float); n/=np.linalg.norm(n)
    t=np.array([-n[1],n[0],0.]); basis=np.column_stack((t,[0,0,1],n))
    used=sorted(set(v for fi in face_indices for v in data['faces'][fi]))
    lookup={v:i for i,v in enumerate(used)}
    local=(coords[used]-np.array(center))@basis
    groups_here=defaultdict(set)
    for fi in face_indices:
        groups_here[group_indices[fi]].update(lookup[v] for v in data['faces'][fi])
    for indices in groups_here.values():
        indices=sorted(indices); depth=float(np.mean(local[indices,2]))
        projection_error=max(projection_error,float(np.max(abs(local[indices,2]-depth))))
        local[indices,2]=depth
    if projection_error>.002: raise ValueError('Orientation-family projection exceeds measured contour tolerance')
    mesh=bpy.data.meshes.new('BODY_local_plane_family_'+str(family_index))
    mesh.from_pydata(local.tolist(),[],[[lookup[v] for v in data['faces'][fi]] for fi in face_indices]); mesh.update()
    part=bpy.data.objects.new(mesh.name,mesh); body.objects.link(part); part.parent=obj
    matrix=np.eye(4); matrix[:3,:3]=basis; matrix[:3,3]=np.array(center)
    part.matrix_world=Matrix(matrix.tolist())
    for name,domain,values in [('revit_element_id','FACE',[data['owner_ids'][fi] for fi in face_indices]),
                               ('source_group_index','FACE',[group_indices[fi] for fi in face_indices]),
                               ('source_face_index','FACE',face_indices),('source_vertex_index','POINT',used)]:
        mesh.attributes.new(name,'INT',domain).data.foreach_set('value',values)
    part.show_wire=True; part.show_all_edges=True; part.color=(.62,.68,.75,1)
bpy.context.view_layer.objects.active=obj; obj.select_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            region=area.spaces.active.region_3d
            region.view_location=center; region.view_distance=extent
            region.view_rotation=Vector((1,-1,.7)).to_track_quat('Z','Y')
blend=out/'BUTOVSKAYA_BODY_FACADES.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.wm.open_mainfile(filepath=str(blend))
saved=np.zeros_like(coords); faces=[None]*len(data['faces']); ids=[None]*len(faces); groups_saved=[None]*len(faces)
face_sizes=Counter(); wrong=0; zero=0; validated=False; objects=[]
for part in bpy.context.scene.objects:
    if part.type!='MESH': continue
    objects.append(part); mesh=part.data
    source_vertices=[x.value for x in mesh.attributes['source_vertex_index'].data]
    matrix=np.array(part.matrix_world,dtype=float)
    world=np.array([list(v.co) for v in mesh.vertices])@matrix[:3,:3].T+matrix[:3,3]
    saved[source_vertices]=world
    source_faces=[x.value for x in mesh.attributes['source_face_index'].data]
    for f,fi in zip(mesh.polygons,source_faces):
        faces[fi]=[source_vertices[v] for v in f.vertices]
        face_sizes[len(f.vertices)]+=1; zero+=f.area<1e-10
        normal=matrix[:3,:3]@np.array(f.normal); normal/=np.linalg.norm(normal)
        wrong+=int(normal@np.array(data['face_normals'][fi])<.99999)
        ids[fi]=mesh.attributes['revit_element_id'].data[f.index].value
        groups_saved[fi]=mesh.attributes['source_group_index'].data[f.index].value
    validated|=mesh.validate(clean_customdata=False)
face_sizes=dict(face_sizes)
error=float(np.linalg.norm(saved-coords,axis=1).max())
qa={'blend':str(blend),'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
    'face_sizes':face_sizes,'vertices':len(saved),'faces_match':faces==data['faces'],
    'zero_area_faces':int(zero),'wrong_normals':wrong,'orientation_objects':len(objects),
    'local_plane_projection_max_deviation_m':projection_error,
    'max_coordinate_readback_error_m':error,
    'source_ids_match':ids==data['owner_ids'],
    'source_registry_match':json.loads(bpy.data.objects['BODY_S1_without_Shell']['source_group_registry'])==data['groups'],
    'group_indices_match':groups_saved==group_indices,
    'mesh_validate_changed':validated,
    'scope':data['scope'],'visual_accepted':False,'delivery_passed':False}
(out/'native-readback.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
if face_sizes!={4:len(faces)} or not qa['faces_match'] or not qa['source_ids_match'] or not qa['source_registry_match'] or not qa['group_indices_match'] or wrong or qa['zero_area_faces'] or error>.002 or qa['mesh_validate_changed']: raise ValueError(qa)
# Rendering adds only temporary cameras and grid curves after the master was saved.
scene=bpy.context.scene; scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'; scene.display.shading.color_type='OBJECT'
scene.display.shading.show_shadows=False; scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD'; scene.world=bpy.data.worlds.new('PreviewWorld'); scene.world.color=(.93,.94,.96)
curves=bpy.data.curves.new('Preview_edges_NOT_saved_geometry','CURVE'); curves.dimensions='3D'; curves.bevel_depth=.008; curves.bevel_resolution=0
for part in objects:
    for edge in part.data.edges:
        spline=curves.splines.new('POLY'); spline.points.add(1)
        for point,index in zip(spline.points,edge.vertices): point.co=(*(part.matrix_world@part.data.vertices[index].co),1)
wire=bpy.data.objects.new('Preview_edges',curves); scene.collection.objects.link(wire); wire.color=(.07,.10,.14,1)
camera_data=bpy.data.cameras.new('Preview_camera'); camera=bpy.data.objects.new('Preview_camera',camera_data); scene.collection.objects.link(camera)
camera_data.type='ORTHO'; scene.camera=camera
scene.render.resolution_x=1800; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
for name,direction in [('SE',(1,-1,.65)),('NW',(-1,1,.65)),('NE',(1,1,.65)),('SW',(-1,-1,.65))]:
    unit=Vector(direction).normalized(); camera.location=center+unit*extent*2
    camera.rotation_euler=(-unit).to_track_quat('-Z','Y').to_euler()
    rotation=camera.rotation_euler.to_quaternion()
    right=np.array(rotation@Vector((1,0,0))); up=np.array(rotation@Vector((0,1,0)))
    camera_data.ortho_scale=max(float(np.ptp(saved@right)),float(np.ptp(saved@up))*1.5)*1.12
    scene.render.filepath=str(out/('BODY_'+name+'_wire.png')); bpy.ops.render.render(write_still=True)
print(json.dumps(qa))

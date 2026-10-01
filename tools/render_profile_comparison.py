"""Isolated native renders of editable snapshot and actual reimport, same cameras."""
from pathlib import Path
import json
import sys
import math
import bpy
from mathutils import Vector

if not bpy.app.background:
    raise RuntimeError('Background-only comparison')
cfg=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf-8'))
out=Path(cfg['output_dir']);out.mkdir(parents=True,exist_ok=True)
if (out/'render-evidence.json').exists():
    raise FileExistsError(out/'render-evidence.json')
camera_parameters=None
evidence={'scope':'Native source/reimport renders, no visual approval implied','renders':[]}
for label in ('source','reimport'):
    if label=='source':
        bpy.ops.wm.open_mainfile(filepath=cfg['blend'],load_ui=False)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=cfg['fbx'],use_image_search=False)
    scene=bpy.context.scene
    meshes=[o for o in scene.objects if o.type=='MESH']
    points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    minimum=Vector([min(p[i] for p in points) for i in range(3)])
    maximum=Vector([max(p[i] for p in points) for i in range(3)])
    if camera_parameters is None:
        center=(minimum+maximum)/2
        extent=max(maximum-minimum)
        camera_parameters=(center,extent)
    center,extent=camera_parameters
    for obj in list(scene.objects):
        if obj.type in {'CAMERA','LIGHT'}:
            bpy.data.objects.remove(obj,do_unlink=True)
    for obj in meshes:
        obj.hide_render=False
    world=bpy.data.worlds.new('DT_CompareWorld');scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.65,0.65,0.65,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.6
    light_data=bpy.data.lights.new('DT_CompareSun','SUN');light_data.energy=2.0
    sun=bpy.data.objects.new('DT_CompareSun',light_data);scene.collection.objects.link(sun)
    sun.rotation_euler=(math.radians(25),math.radians(-25),math.radians(-25))
    cam_data=bpy.data.cameras.new('DT_CompareCamera');cam_data.type='ORTHO';cam_data.ortho_scale=extent*1.15
    cam=bpy.data.objects.new('DT_CompareCamera',cam_data);scene.collection.objects.link(cam);scene.camera=cam
    scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.render.resolution_x=1400;scene.render.resolution_y=600;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    for view,offset in [('front',(0,-1,0.07)),('oblique',(0.65,-1,0.35))]:
        target=out/f'{label}-{view}.png'
        if target.exists():
            raise FileExistsError(target)
        cam.location=center+Vector(offset)*extent*2
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(target)
        bpy.ops.render.render(write_still=True)
        evidence['renders'].append({'label':label,'view':view,'path':str(target),'camera_world':[list(r) for r in cam.matrix_world]})
(out/'render-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print('PROFILE_COMPARISON_RENDERED',len(evidence['renders']))

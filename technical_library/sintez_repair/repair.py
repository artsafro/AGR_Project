"""Case-bound SINTEZ FBX repair and independent saved-package readback.

Run only in a new background Blender process. No addon code/assets are bundled.
"""
from array import array
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys
import zipfile


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_name(name):
    require(name and name not in ('.', '..') and '/' not in name and '\\' not in name and ':' not in name, 'Unsafe output name')
    return name


def empty_output(path, protected):
    path = Path(path).resolve()
    for source in protected:
        source = Path(source).resolve()
        require(path != source and path not in source.parents and source not in path.parents, 'Output overlaps protected input')
    require(not path.exists(), 'Output must be a NEW directory; existing outputs are protected')
    return path


def addon_digest(root):
    root = Path(root)
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob('*') if p.is_file() and p.suffix in ('.py', '.csv', '.toml', '.json', '.geojson')):
        h.update(path.relative_to(root).as_posix().encode() + b'\0')
        h.update(bytes.fromhex(sha(path)))
    return h.hexdigest()


def geometry_signature(bpy):
    result = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        h = hashlib.sha256()
        for collection, prop, typ, n in [(obj.data.vertices, 'co', 'f', 3), (obj.data.loops, 'vertex_index', 'i', 1), (obj.data.polygons, 'loop_total', 'i', 1), (obj.data.polygons, 'material_index', 'i', 1)]:
            values = array(typ, [0]) * (len(collection) * n)
            collection.foreach_get(prop, values)
            h.update(values.tobytes())
        for uv in obj.data.uv_layers:
            values = array('f', [0]) * (len(uv.data) * 2)
            uv.data.foreach_get('uv', values)
            h.update(values.tobytes())
        h.update(repr([list(row) for row in obj.matrix_world]).encode())
        result[obj.name] = {'hash': h.hexdigest(), 'verts': len(obj.data.vertices), 'faces': len(obj.data.polygons), 'materials': [m.name if m else None for m in obj.data.materials]}
    return result


def packed_textures(bpy):
    result = {}
    for image in bpy.data.images:
        require(image.packed_file is not None, 'Image must contain packed bytes: ' + image.name)
        # Saved Blender images are lazy; pixel access proves decoding, not only presence.
        require(len(image.pixels) > 0 and image.has_data, 'Packed image does not decode: ' + image.name)
        name = safe_name(image.name + '.png')
        require(name not in result, 'Duplicate packed image name')
        result[name] = bytes(image.packed_file.data)
    return result


def load_addon(bpy, root, dependencies, config):
    require(tuple(bpy.app.version[:2]) == tuple(config['blender_version']), 'Unverified Blender version')
    root = Path(root).resolve()
    require(root.name == 'sintez_agr_checker', 'Expected installed addon directory')
    require(addon_digest(root) == config['addon_digest'], 'Addon differs from pinned source and requirements')
    sys.path.insert(0, str(root.parent))
    sys.path.insert(0, str(Path(dependencies).resolve()))
    addon = importlib.import_module('sintez_agr_checker')
    for cls in addon.classes[:8]:
        bpy.utils.register_class(cls)
    bpy.types.Scene.agr_scene_properties = bpy.props.PointerProperty(type=addon.properties.AGRCheckerProperties)
    return addon


def check_snapshot(bpy, config):
    require(geometry_signature(bpy) == config['geometry'], 'Geometry, UV, transform or materials differ from approved snapshot')
    textures = packed_textures(bpy)
    require({k: hashlib.sha256(v).hexdigest() for k, v in textures.items()} == config['texture_hashes'], 'Packed textures differ from pinned snapshot')
    return textures


def save_new_blend(bpy, input_file, output, expected_source_sha256):
    # Check again after export: concurrent source drift cannot receive success.
    require(sha(input_file) == expected_source_sha256, 'Snapshot changed during repair')
    bpy.context.scene.agr_scene_properties.path = str(output)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'repaired.blend'))


def repair(bpy, config, input_file, output):
    require(sha(input_file) == config['snapshot_sha256'], 'Snapshot hash mismatch')
    bpy.ops.wm.open_mainfile(filepath=str(input_file))
    textures = check_snapshot(bpy, config)
    collections = [bpy.data.collections.get(name) for name in config['source_collections']]
    require(all(collections), 'Missing source FBX collection')
    require(len({o.name for c in collections for o in c.objects}) == len(config['geometry']), 'Collection coverage mismatch')
    output.mkdir(parents=True)
    package = output / config['package']
    maps = package / 'maps'
    maps.mkdir(parents=True)
    for image in bpy.data.images:
        name = safe_name(image.name + '.png')
        (maps / name).write_bytes(textures[name])
        image.filepath = str(maps / name)
    from sintez_agr_checker.scripts.model_exporter.export_models import LOW_POLY_SETTINGS
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    hidden = {obj.name: obj.hide_get() for obj in bpy.data.objects}
    try:
        for collection, name in zip(collections, config['fbx_names']):
            collection.name = name
            for obj in bpy.data.objects:
                obj.hide_set(False)
                obj.select_set(False)
            for obj in collection.objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = next(iter(collection.objects))
            settings = dict(LOW_POLY_SETTINGS, use_selection=True, use_visible=False, use_active_collection=False)
            require('FINISHED' in bpy.ops.export_scene.fbx(filepath=str(package / name), **settings), 'FBX export failed')
    finally:
        for obj in bpy.data.objects:
            obj.select_set(obj in selected)
            obj.hide_set(hidden[obj.name])
        bpy.context.view_layer.objects.active = active
    check_snapshot(bpy, config)
    archive = output / (config['package'] + '.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for name in config['fbx_names']:
            z.write(package / name, name)
    save_new_blend(bpy, input_file, output, config['snapshot_sha256'])
    receipt = {'input_sha256': sha(input_file), 'blend_sha256': sha(output / 'repaired.blend'), 'archive_sha256': sha(archive), 'geometry_unchanged': True, 'textures_unchanged': True, 'native_package_check': 'pending in separate process', 'manual_checks': '28 pending', 'signature': 'pending', 'visual_acceptance': 'pending'}
    (output / 'repair.json').write_text(json.dumps(receipt, indent=2), encoding='utf8')


def readback(bpy, config, blend, package_root, output):
    receipt = json.loads((package_root / 'repair.json').read_text(encoding='utf8'))
    require(sha(blend) == receipt['blend_sha256'], 'Saved blend changed after repair')
    archive = package_root / (config['package'] + '.zip')
    require(sha(archive) == receipt['archive_sha256'], 'ZIP changed after repair')
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None and sorted(z.namelist()) == sorted(config['fbx_names']), 'Invalid ZIP contents')
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    check_snapshot(bpy, config)
    # Native checker imports a separate scene in THIS background process only.
    from sintez_agr_checker.scripts import check_highpoly_lowpoly as checker
    class Reporter:
        def report(self, *args):
            print(args)
    bpy.context.scene.agr_scene_properties.path = str(package_root)
    lp, hp, project = checker.run(Reporter(), config['project'], str(package_root))
    require(lp is not None and len(lp) == config['expected_native_groups'], 'Native lowpoly check coverage changed')
    errors = [{'rule': key, 'errors': check.error_list} for key, values in lp.items() for check in values if check.error_list]
    check_snapshot(bpy, config)  # Exact native import equivalence, not only counts.
    require(not errors, 'Native checker found errors: ' + repr(errors))
    output.mkdir(parents=True)
    report = {'saved_blend_sha256': sha(blend), 'archive_sha256': sha(archive), 'saved_geometry_matches_snapshot': True, 'native_import_geometry_matches_snapshot': True, 'native_import_packed_textures_match': True, 'native_errors': errors, 'native_check_groups': len(lp), 'historical_auto_checks': '44/44; current native groups are not UI counters', 'manual_checks': '28 pending', 'signature': 'pending', 'visual_acceptance': 'pending', 'delivery': False}
    (output / 'native-readback.json').write_text(json.dumps(report, indent=2), encoding='utf8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['repair', 'readback'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--addon', type=Path, required=True)
    parser.add_argument('--dependencies', type=Path, required=True)
    parser.add_argument('--package-root', type=Path)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding='utf8'))
    for name in [config['package'], *config['source_collections'], *config['fbx_names']]:
        safe_name(name)
    require(len(config['source_collections']) == len(config['fbx_names']) and len(set(config['fbx_names'])) == len(config['fbx_names']), 'Invalid collection mapping')
    protected = [args.input, args.config, args.addon, args.dependencies]
    if args.package_root:
        protected.append(args.package_root)
    output = empty_output(args.output, protected)
    import bpy
    load_addon(bpy, args.addon, args.dependencies, config)
    if args.stage == 'repair':
        repair(bpy, config, args.input.resolve(), output)
    else:
        require(args.package_root is not None, 'readback requires --package-root')
        readback(bpy, config, args.input.resolve(), args.package_root.resolve(), output)


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:])

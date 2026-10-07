"""Compare actual imported wall triangle geometry across two Revit exports."""
import argparse,json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
import bpy
import numpy as np

def signatures(blend,inventory):
    records=json.loads(Path(inventory).read_text(encoding='utf-8'))['objects']
    ids={int(r['revit_metadata']['elementId']) for r in records if r.get('revit_metadata',{}).get('category')=='Стены'}
    bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
    result={}
    for obj in bpy.context.scene.objects:
        eid=int(obj.get('revit_element_id',-1))
        if obj.type!='MESH' or eid not in ids:continue
        if eid in result:raise ValueError('Nonunique wall source ID')
        matrix=np.array(obj.matrix_world,dtype=float)
        pts=np.array([list(v.co) for v in obj.data.vertices])@matrix[:3,:3].T+matrix[:3,3]
        obj.data.calc_loop_triangles()
        tris=pts[np.array([list(t.vertices) for t in obj.data.loop_triangles])]
        quantized=np.rint(tris/.000001).astype(np.int64)
        for triangle in quantized:triangle[:]=triangle[np.lexsort(triangle.T[::-1])]
        rows=quantized.reshape(-1,9);rows=rows[np.lexsort(rows.T[::-1])]
        result[eid]={'triangles':len(rows),'sha256_1um_triangle_geometry':hashlib.sha256(rows.tobytes()).hexdigest()}
    return result

p=argparse.ArgumentParser()
for key in ['old','old-inventory','fresh','fresh-inventory','selection','output']:p.add_argument('--'+key,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if not bpy.app.background:raise RuntimeError('Background read-only')
out=Path(a.output).resolve()
if out.exists():raise ValueError('Fresh output required')
old=signatures(a.old,a.old_inventory);fresh=signatures(a.fresh,a.fresh_inventory)
selected={e['id'] for e in json.loads(Path(a.selection).read_text(encoding='utf-8'))['elements']}
missing=sorted(set(old)-set(fresh));added=sorted(set(fresh)-set(old))
changed=sorted(eid for eid in set(old)&set(fresh) if old[eid]!=fresh[eid])
receipt={'verified_current_revit':not missing and not changed,
 'document':'БУТОВСКАЯ_СОШ1000_АР_В3_ВИЗАМ_2025','checked_at':datetime.now(timezone.utc).isoformat(),
 'old_wall_ids':len(old),'fresh_wall_ids':len(fresh),'matched_wall_ids':len(set(old)&set(fresh))-len(changed),
 'missing_wall_ids':missing,'new_wall_ids':added,'changed_wall_ids':changed,
 'selected_missing_or_changed_ids':sorted(selected&set(missing+changed)),
 'comparison':'Entire per-ID triangle geometry canonicalized to 1um; vertex/triangle ordering ignored, not bbox comparison',
 'old_reference_sha256':hashlib.sha256(Path(a.old).read_bytes()).hexdigest(),
 'fresh_reference_sha256':hashlib.sha256(Path(a.fresh).read_bytes()).hexdigest(),
 'limitations':['Live snapshot at export time; no original RVT save. Part/exterior-direction ambiguity remains. Additional fresh wall IDs require review.'],
 'wall_geometry':{'old':old,'fresh':fresh}}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(receipt,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='wall_geometry'},ensure_ascii=True))

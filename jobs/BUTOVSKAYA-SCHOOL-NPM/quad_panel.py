"""Rebuild one measured rectilinear facade plane with opening-aligned quads.

Run with project Python (NumPy/Shapely), not Blender. No source changes.
"""
import argparse, json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon, box

p=argparse.ArgumentParser()
p.add_argument('--panels',required=True)
p.add_argument('--element-id',required=True,type=int)
p.add_argument('--normal-x',required=True,type=float)
p.add_argument('--output',required=True)
p.add_argument('--rail-cluster-m',type=float,default=0)
a=p.parse_args()
out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
if (out/'panel-mesh.json').exists(): raise RuntimeError('Refuse overwrite')
panels=json.loads(Path(a.panels).read_text(encoding='utf-8'))
found=[x for x in panels if x['revit_element_id']==a.element_id and x['normal'][0]*a.normal_x>0.99999]
if len(found)!=1: raise ValueError(f'Expected one exterior plane, found {len(found)}')
s=found[0]
areas=[]
for coords in s['polygons_2d_m']:
    poly=Polygon(coords)
    if not poly.is_valid: raise ValueError('Invalid source face')
    if poly.area>1e-12: areas.append(poly)
shape=shapely.union_all(areas)
if not shape.is_valid or shape.geom_type!='Polygon': raise ValueError('One connected wall profile required')
raw=shape
# FBX coordinate noise is grouped within 0.05mm; recorded against raw contour.
shape=shapely.set_precision(shape,0.00005).simplify(0.000001,preserve_topology=True)
rings=[list(shape.exterior.coords)]+[list(x.coords) for x in shape.interiors]
for ring in rings:
    for u,v in zip(ring,ring[1:]):
        if min(abs(u[0]-v[0]),abs(u[1]-v[1]))>1e-8:
            raise ValueError('Sloped contour: this rectilinear route cannot preserve it')
axes=[sorted(set(v[i] for ring in rings for v in ring)) for i in range(2)]
if max(map(len,axes))>400: raise ValueError('Unexpected excessive boundary complexity')
grid=None
if a.rail_cluster_m:
    # Group redundant near cuts; interpolate rails only through solid regions.
    # All active source boundary coordinates are constrained, never snapped to
    # another opening. Incompatible constraints retain their separate cuts.
    groups=[]
    for axis in axes:
        g=[]
        for value in axis:
            if not g or value-g[-1][0]>a.rail_cluster_m: g.append([value])
            else: g[-1].append(value)
        groups.append(g)
    segments=[(u,v) for ring in rings for u,v in zip(ring,ring[1:])]
    for attempt in range(20):
        constraints=[{},{}]; conflicts=[set(),set()]
        for i,gu in enumerate(groups[0]):
            for j,gv in enumerate(groups[1]):
                for axis,group,cross in ((0,gu,gv),(1,gv,gu)):
                    other=1-axis
                    choices=set()
                    for u,v in segments:
                        if abs(u[axis]-v[axis])<1e-9 and any(abs(u[axis]-q)<1e-9 for q in group):
                            lo,hi=sorted((u[other],v[other]))
                            if hi>=cross[0]-1e-9 and lo<=cross[-1]+1e-9: choices.add(u[axis])
                    if len(choices)>1: conflicts[axis].add(i if axis==0 else j)
                    elif choices: constraints[axis][i,j]=next(iter(choices))
        if not any(conflicts): break
        for axis in (0,1):
            groups[axis]=[part for k,g in enumerate(groups[axis]) for part in ([[q] for q in g] if k in conflicts[axis] else [g])]
    else: raise ValueError('Local rail constraints did not converge')
    nx,nz=map(len,groups)
    grid=np.empty((nx,nz,2))
    for i in range(nx):
        for j in range(nz):
            for axis in (0,1):
                if (i,j) in constraints[axis]: value=constraints[axis][i,j]
                else:
                    line=[(k[1-axis],v) for k,v in constraints[axis].items() if k[axis]==(i if axis==0 else j)]
                    if line:
                        line.sort(); value=float(np.interp(j if axis==0 else i,[q for q,_ in line],[v for _,v in line]))
                    else: value=float(np.mean(groups[axis][i if axis==0 else j]))
                grid[i,j,axis]=value
else:
    grid=np.array([[[u,v] for v in axes[1]] for u in axes[0]])
vertices=[]; faces=[]; lookup={}; cells=[]
n=np.array(s['normal']); tangent=np.array(s['tangent']); origin=n*s['plane_d_m']
for i in range(grid.shape[0]-1):
    for j in range(grid.shape[1]-1):
        corners=[tuple(grid[ii,jj]) for ii,jj in ((i,j),(i+1,j),(i+1,j+1),(i,j+1))]
        cell=Polygon(corners)
        if not cell.is_valid or cell.area<1e-10: raise ValueError('Invalid transition quad')
        vectors=np.roll(np.array(corners),-1,axis=0)-corners
        turns=vectors[:,0]*np.roll(vectors[:,1],-1)-vectors[:,1]*np.roll(vectors[:,0],-1)
        if not np.all(turns>1e-10): raise ValueError('Transition quad must be strictly convex')
        area=cell.intersection(shape).area
        if area<1e-12: continue
        if abs(area-cell.area)>1e-8: raise ValueError('Partial cell would approximate source')
        cells.append(cell)
        face=[]
        for uv in corners:
            if uv not in lookup:
                lookup[uv]=len(vertices)
                vertices.append((origin+tangent*uv[0]+np.array([0,0,uv[1]])).tolist())
            face.append(lookup[uv])
        faces.append(face)
rebuilt=shapely.union_all(cells)
distance=float(shapely.hausdorff_distance(raw.boundary,rebuilt.boundary))
sym=float(raw.symmetric_difference(rebuilt).area)
if distance>0.002: raise ValueError('Source contour error exceeds 2mm')
edges={}
for f in faces:
    for i,j in zip(f,f[1:]+f[:1]):
        k=tuple(sorted((i,j))); edges[k]=edges.get(k,0)+1
if max(edges.values())>2: raise ValueError('Nonmanifold surface')
result={'scope':'Single measured exterior wall surface only; no Shell/windows/whole-building claim',
 'source':s,'vertices_m':vertices,'faces':faces,
 'qa':{'quads':len(faces),'source_opening_loops':len(shape.interiors),
       'contour_hausdorff_m':distance,'symmetric_difference_m2':sym,
       'boundary_edges':sum(c==1 for c in edges.values()),'max_edge_face_count':max(edges.values()),
       'coordinate_precision_m':0.00005,'min_grid_span_m':min(np.diff(x).min() for x in axes),
       'cut_style':'local constrained rails' if a.rail_cluster_m else 'coordinate grid',
       'min_edge_length_m':min(np.linalg.norm(np.array(vertices[i])-vertices[j]) for i,j in edges),
       'visual_acceptance':'pending','delivery_passed':False}}
(out/'panel-mesh.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
print(json.dumps(result['qa']))

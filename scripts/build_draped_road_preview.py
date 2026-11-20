#!/usr/bin/env python3
"""Build a NEW terrain-following road OBJ from the validated fused-road preview OBJ.

Never changes source OBJ, map, existing fused road asset or buildings.
Each source triangle is subdivided for smoother landscape contact. Height values
are aligned against the *current preview landscape* (535.5 m, centred at 0)
and NOT considered surveyed elevations. Edit preview alignment only after QA.

Usage:
  py -3 scripts/build_draped_road_preview.py
Requires: pillow, numpy (already installed during elevation pilot).
"""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image

ROOT=Path(r'E:\code\ChesterWorldUnreal\pilot\9th_Kerlin\fast_pass')
TERRAIN=Path(r'E:\ChesterWorld\Reports\UnrealTerrainPilot')
OUT=Path(r'E:\ChesterWorld\Reports\UnrealRoadTerrainPilot')
# Current ACTUAL landscape bounds after centered at -26775 and scale 50
# (536ish-meter pilot rather than exact 512 m DEM footprint).
MIN_X=MIN_Y=-26775.0
MAX_X=MAX_Y=26775.0
TERRAIN_Z_MIN_CM=-4.57
TERRAIN_Z_MAX_CM=2329.54
ROAD_CLEARANCE_CM=8.0
MAX_TRI_EDGE_CM=800.0
MAX_SUBDIV=22

def choose_source():
    files=list(ROOT.rglob('*.obj'))
    if not files:
        raise SystemExit('No fused-road OBJ found under '+str(ROOT))
    matches=[p for p in files if 'fused' in p.name.lower() and 'building' not in p.name.lower()]
    if not matches:
        raise SystemExit('No fused road OBJ among '+str([p.name for p in files]))
    # Prefer the corrected file and do not accidentally use our own output.
    matches.sort(key=lambda p:(0 if any(t in p.name.lower() for t in ('fixed','up','correct')) else 1,len(p.name)))
    print('Road source:',matches[0])
    return matches[0]

def read_obj(path):
    vertices=[];triangles=[]
    for line in path.open(encoding='utf-8',errors='replace'):
        if line.startswith('v '):
            parts=line.split()
            vertices.append(tuple(float(v) for v in parts[1:4]))
        elif line.startswith('f '):
            inds=[]
            for token in line.split()[1:]:
                i=int(token.split('/')[0])
                inds.append(i-1 if i>0 else len(vertices)+i)
            for j in range(1,len(inds)-1):
                triangles.append((inds[0],inds[j],inds[j+1]))
    if not vertices or not triangles:
        raise RuntimeError('No usable OBJ triangles in '+str(path))
    if not all(0<=i<len(vertices) for f in triangles for i in f):
        raise RuntimeError('Invalid OBJ vertex indices')
    return np.asarray(vertices,dtype=np.float64),triangles

def main():
    src=choose_source()
    vertices,faces=read_obj(src)
    dimensions=np.ptp(vertices[:,:2],axis=0)
    print('Road OBJ XY dimensions:',dimensions.tolist())
    if not (40000<dimensions[0]<65000 and 40000<dimensions[1]<65000):
        raise RuntimeError('Unexpected OBJ coordinates. Expected 550m-wide, centimeter-based road OBJ. No output written.')
    heightmaps=list(TERRAIN.glob('9th_Kerlin_513x513_ELEVATION_PREVIEW*.png'))
    if not heightmaps:
        raise RuntimeError('Missing original 513x513 uint16 terrain preview.')
    height=np.array(Image.open(heightmaps[0]),dtype=np.float64)
    if height.shape != (513,513):
        raise RuntimeError('Unexpected heightmap dimensions: '+str(height.shape))
    def ground(x,y):
        col=max(0.0,min(512.0,(x-MIN_X)/(MAX_X-MIN_X)*512.0))
        row=max(0.0,min(512.0,(MAX_Y-y)/(MAX_Y-MIN_Y)*512.0))
        c0=int(col);r0=int(row);c1=min(512,c0+1);r1=min(512,r0+1)
        u=col-c0;v=row-r0
        raw=(height[r0,c0]*(1-u)*(1-v)+height[r0,c1]*u*(1-v)+
             height[r1,c0]*(1-u)*v+height[r1,c1]*u*v)/65535.0
        return TERRAIN_Z_MIN_CM+(TERRAIN_Z_MAX_CM-TERRAIN_Z_MIN_CM)*raw+ROAD_CLEARANCE_CM
    OUT.mkdir(parents=True,exist_ok=True)
    dest=OUT/'Chester_9thKerlin_Roads_Draped_PREVIEW.obj'
    count=0
    with dest.open('w',encoding='utf-8') as output:
        output.write('# PREVIEW ONLY. GIS vertical datum/terrain orientation UNVERIFIED.\n')
        output.write('o CW_ROADS_DRAPED_PREVIEW\n')
        for tri in faces:
            a,b,c=[vertices[i] for i in tri]
            # vertex density for grade changes; cap avoids pathological mesh growth.
            side=max(np.linalg.norm(a[:2]-b[:2]),np.linalg.norm(a[:2]-c[:2]),np.linalg.norm(b[:2]-c[:2]))
            subdivisions=max(1,min(MAX_SUBDIV,math.ceil(side/MAX_TRI_EDGE_CM)))
            if subdivisions==MAX_SUBDIV and side/MAX_TRI_EDGE_CM>MAX_SUBDIV:
                raise RuntimeError('Triangle too long for drape; source geometry requires further subdivision.')
            grid={}
            for i in range(subdivisions+1):
                for j in range(subdivisions+1-i):
                    p=a+(b-a)*(i/subdivisions)+(c-a)*(j/subdivisions)
                    grid[i,j]=(float(p[0]),float(p[1]),ground(float(p[0]),float(p[1])))
            # Uniform subdivision; independent triangle vertices intentional in preview.
            def emit(p1,p2,p3):
                nonlocal count
                points=(p1,p2,p3)
                start=count*3+1
                for x,y,z in points:
                    output.write(f'v {x:.3f} {y:.3f} {z:.3f}\n')
                output.write(f'f {start} {start+1} {start+2}\n')
                count+=1
            for i in range(subdivisions):
                for j in range(subdivisions-i):
                    emit(grid[i,j],grid[i+1,j],grid[i,j+1])
                    if i+j < subdivisions-1:
                        emit(grid[i+1,j],grid[i+1,j+1],grid[i,j+1])
    report={
        'source_road_obj':str(src),'road_source_triangles':len(faces),'new_preview_triangles':count,
        'output_obj':str(dest),'landscape_bounds_cm':[MIN_X,MIN_Y,MAX_X,MAX_Y],
        'source_heightmap':str(heightmaps[0]),'terrain_z_range_cm':[TERRAIN_Z_MIN_CM,TERRAIN_Z_MAX_CM],
        'clearance_cm':ROAD_CLEARANCE_CM,'subdivision_max_edge_cm':MAX_TRI_EDGE_CM,
        'status':'visual_preview_only',
        'warnings':['Not verified: vertical datum, source elevation units or north-south orientation.',
                    'Road extents exceed current 535.5m landscape footprint; border sections are clamped to edge height.',
                    'Does not merge lanes, correct junction topology, grade bridges or provide proven vehicle collision.',
                    'Old flat roads must be hidden for visual inspection, but kept until driving verified.']
    }
    (OUT/'draped_roads_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('CW_DRAPED_ROADS_DONE',count,'triangles')
    print(dest)
if __name__=='__main__':
    main()

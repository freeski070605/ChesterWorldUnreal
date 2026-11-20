#!/usr/bin/env python3
"""Generate Chester 9th/Kerlin building shell preview from Delaware County GIS.

Local dependencies: py -3 -m pip install shapely pyproj numpy pillow
Reads original footprints and terrain preview from E:. Does not alter either.
Heights are explicitly estimated unless source includes usable height/levels.
This pilot does not validate the DEM vertical datum, orientation, or road grade.
"""
import json, math
from pathlib import Path
from collections import Counter
from pyproj import Transformer
from shapely.geometry import shape, box, Polygon, MultiPolygon
from shapely.ops import transform, triangulate
import numpy as np
from PIL import Image

BASE = Path(r'E:\ChesterWorld\Data')
GEO = BASE / '01_Buildings' / 'delco_buildings.geojson'
REPORT = Path(r'E:\ChesterWorld\Reports\UnrealBuildingPilot')
PNG = Path(r'E:\ChesterWorld\Reports\UnrealTerrainPilot\9th_Kerlin_513x513_ELEVATION_PREVIEW_NOT_ENGINE_SCALED.png')
META = Path(r'E:\ChesterWorld\Reports\UnrealTerrainPilot\terrain_9th_kerlin_report.json')
ANCHOR_E, ANCHOR_N = 468226.1739083406, 4410988.22069396
CLIP_HALF_M = 255.0
DEFAULT_HEIGHT_M = 8.0

def polys(geom):
    if isinstance(geom, Polygon): return [geom]
    if isinstance(geom, MultiPolygon): return list(geom.geoms)
    return []

def height_m(props):
    for field in ['height','HEIGHT','building:height','HEIGHT_M','height_m']:
        val=props.get(field)
        if val is None: continue
        try:
            h=float(str(val).lower().replace('m','').strip())
            if 2.0 <= h <= 90.0: return h, 'source:'+field
        except ValueError: pass
    for field in ['building:levels','levels','LEVELS','stories']:
        try:
            levels=float(props.get(field))
            if 1<=levels<=20: return levels*3.1,'estimated_levels:'+field
        except (ValueError,TypeError): pass
    return DEFAULT_HEIGHT_M,'estimated_default'

def main():
    if not GEO.is_file(): raise SystemExit('Missing source footprints: '+str(GEO))
    if not PNG.is_file() or not META.is_file(): raise SystemExit('Missing terrain preview/report. Do terrain step first.')
    meta=json.loads(META.read_text(encoding='utf-8'))
    if meta.get('elevation_min_raw') is None: raise SystemExit('Terrain report lacks elevation range')
    z_min, z_max = -4.57, 2329.54
    img=np.asarray(Image.open(PNG),dtype=np.float64)
    if img.ndim!=2: raise SystemExit('Heightmap must be 16-bit grayscale')
    source=json.loads(GEO.read_text(encoding='utf-8-sig'))
    source_crs=((source.get('crs') or {}).get('properties') or {}).get('name','EPSG:4326')
    transformer=Transformer.from_crs(source_crs,'EPSG:32618',always_xy=True)
    def to_local(x,y,z=None):
        e,n=transformer.transform(x,y)
        return e-ANCHOR_E,n-ANCHOR_N
    def terrain_z(x,y):
        # PREVIEW ONLY. Map 535.5m landscape to original DEM pixel range.
        xx=(x+267.75)/535.5*(img.shape[1]-1)
        yy=(267.75-y)/535.5*(img.shape[0]-1)
        xx=max(0,min(img.shape[1]-1,xx)); yy=max(0,min(img.shape[0]-1,yy))
        x0=int(xx);y0=int(yy);x1=min(x0+1,img.shape[1]-1);y1=min(y0+1,img.shape[0]-1)
        tx=xx-x0;ty=yy-y0
        val=(img[y0,x0]*(1-tx)*(1-ty)+img[y0,x1]*tx*(1-ty)+img[y1,x0]*(1-tx)*ty+img[y1,x1]*tx*ty)/65535
        return z_min+(z_max-z_min)*val
    vertices=[];faces=[];stats=Counter();shape_count=0
    clip=box(-CLIP_HALF_M,-CLIP_HALF_M,CLIP_HALF_M,CLIP_HALF_M)
    for f in source.get('features',[]):
        g=f.get('geometry')
        if not g or g.get('type') not in ('Polygon','MultiPolygon'):continue
        try: local=transform(to_local,shape(g)).intersection(clip)
        except Exception:stats['invalid_geometry']+=1;continue
        if local.is_empty:continue
        props=f.get('properties') or {}
        h,htype=height_m(props)
        for poly in polys(local):
            if poly.area<8.0:continue
            if not poly.is_valid:poly=poly.buffer(0)
            if poly.is_empty:continue
            bottom=terrain_z(poly.centroid.x,poly.centroid.y)
            top=bottom+h*100
            for t in triangulate(poly):
                if not poly.covers(t.representative_point()):continue
                pts=list(t.exterior.coords)[:3];ix=[]
                for x,y in pts:
                    vertices.append((x*100,y*100,top));ix.append(len(vertices))
                faces.append(tuple(ix))
            for ring in [poly.exterior,*poly.interiors]:
                coords=list(ring.coords)
                for (x1,y1),(x2,y2) in zip(coords,coords[1:]):
                    if math.hypot(x2-x1,y2-y1)<0.02:continue
                    z1=terrain_z(x1,y1)-20;z2=terrain_z(x2,y2)-20
                    ids=[]
                    for xyz in [(x1*100,y1*100,z1),(x2*100,y2*100,z2),(x2*100,y2*100,top),(x1*100,y1*100,top)]:
                        vertices.append(xyz);ids.append(len(vertices))
                    faces.extend([(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])])
            shape_count+=1;stats[htype]+=1
    REPORT.mkdir(parents=True,exist_ok=True)
    obj=REPORT/'Chester_9thKerlin_BuildingShells_PREVIEW.obj'
    with obj.open('w',encoding='utf-8') as out:
        out.write('# Chester World buildings in UE centimeters: estimates, preview only\n')
        out.write('o CW_BUILDING_SHELLS_PREVIEW\n')
        for x,y,z in vertices:out.write(f'v {x:.3f} {y:.3f} {z:.3f}\n')
        for indices in faces:out.write('f '+' '.join(str(k) for k in indices)+'\n')
    report={'source':str(GEO),'source_crs':source_crs,'heightmap':str(PNG),'heightmap_shape':list(img.shape),'count_building_shells':shape_count,'triangles':len(faces),'height_sources':dict(stats),'terrain_bounds_cm':[-26775,-26775,26775,26775],'height_preview_cm_range':[z_min,z_max],'warnings':['Visual pilot only: vertical datum and PNG north-south orientation unverified.','Buildings are untextured massing shells, not accurate building elevations.','Some clipped shells at tile boundary may have artificial edge walls.','Building height estimates must be replaced using observations or trusted height data.','Road mesh remains at diagnostic Z; building placement does not fix road elevation.']}
    (REPORT/'building_pilot_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('CW_BUILDINGS_DONE',shape_count,'shells',len(faces),'triangles')
    print(obj)
    print(REPORT/'building_pilot_report.json')
    if not shape_count: raise SystemExit('WARNING: zero footprints imported: check CRS and data geometry')
if __name__=='__main__':main()

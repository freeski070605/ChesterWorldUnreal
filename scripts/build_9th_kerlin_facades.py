#!/usr/bin/env python3
"""Build NON-DESTRUCTIVE 9th/Kerlin facade panels from footprint geometry.

These are procedural *visual placeholders*, not surveyed facade observations.
Generates two OBJ files (windows, doors) compatible with CleanupV2 building
shell coordinates. It does NOT modify or regenerate the working shell mesh.

Run: py -3 scripts/build_9th_kerlin_facades.py
Requires: shapely, pyproj, numpy, pillow.
"""
from pathlib import Path
import json
import math
from collections import Counter
import numpy as np
from PIL import Image
from pyproj import Transformer
from shapely.geometry import Polygon, MultiPolygon, box, shape
from shapely.geometry.polygon import orient
from shapely.ops import transform

ROOT=Path(r"E:\ChesterWorld\Data")
FOOTPRINTS=ROOT/"01_Buildings"/"delco_buildings.geojson"
HEIGHTMAP=Path(r"E:\ChesterWorld\Reports\UnrealTerrainPilot\9th_Kerlin_513x513_ELEVATION_PREVIEW_NOT_ENGINE_SCALED.png")
OUTPUT=Path(r"E:\ChesterWorld\Reports\UnrealFacadePilot")
E0,N0=468226.1739083406,4410988.22069396
BOUND=255.0

def buildings(g):
    if isinstance(g,Polygon): return [g]
    if isinstance(g,MultiPolygon): return list(g.geoms)
    return []

def height(props):
    for key in ("height","HEIGHT","building:height","HEIGHT_M","height_m"):
        if props.get(key) is not None:
            try:
                n=float(str(props[key]).strip().lower().replace("m",""))
                if 2<=n<=90:return n
            except (ValueError,TypeError): pass
    for key in ("building:levels","levels","LEVELS","stories"):
        try:
            n=float(props.get(key))
            if 1<=n<=20:return n*3.1
        except (ValueError,TypeError):pass
    return 8.0

class OBJ:
    def __init__(self):self.vertices=[];self.faces=[]
    def quad(self,p1,p2,p3,p4):
        start=len(self.vertices)+1
        self.vertices.extend((p1,p2,p3,p4))
        self.faces.extend(((start,start+1,start+2),(start,start+2,start+3)))
    def write(self,path):
        with path.open("w",encoding="utf-8") as out:
            out.write("# ChesterWorld procedural facade detail; coordinates in Unreal cm\n")
            out.write("o CW_FACADE_DETAIL_PREVIEW\n")
            for x,y,z in self.vertices:out.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
            for f in self.faces:out.write("f "+" ".join(map(str,f))+"\n")

def main():
    if not FOOTPRINTS.is_file() or not HEIGHTMAP.is_file():
        raise SystemExit("Missing GIS building source or heightmap.")
    img=np.asarray(Image.open(HEIGHTMAP),dtype=np.float64)
    if img.shape != (513,513):raise SystemExit("Unexpected terrain preview image")
    source=json.loads(FOOTPRINTS.read_text(encoding="utf-8-sig"))
    crs=((source.get("crs") or {}).get("properties") or {}).get("name","EPSG:4326")
    projection=Transformer.from_crs(crs,"EPSG:32618",always_xy=True)
    def local(x,y,z=None):
        east,north=projection.transform(x,y)
        return east-E0,north-N0
    def surface_z(x,y):
        # Match CleanupV2 BUILDING mesh's original z; landscape now sits lower.
        col=max(0,min(512,(x+267.75)/535.5*512))
        row=max(0,min(512,(267.75-y)/535.5*512))
        c0=int(col);r0=int(row);c1=min(512,c0+1);r1=min(512,r0+1)
        u=col-c0;v=row-r0
        fraction=(img[r0,c0]*(1-u)*(1-v)+img[r0,c1]*u*(1-v)+img[r1,c0]*(1-u)*v+img[r1,c1]*u*v)/65535.
        return -4.57+(2329.54+4.57)*fraction
    windows=OBJ();doors=OBJ();counts=Counter()
    tile=box(-BOUND,-BOUND,BOUND,BOUND)
    for feature in source.get("features",[]):
        g=feature.get("geometry")
        if not g or g.get("type") not in ("Polygon","MultiPolygon"):continue
        try:geom=transform(local,shape(g)).intersection(tile)
        except Exception:counts["bad_geometries"]+=1;continue
        if geom.is_empty:continue
        for polygon in buildings(geom):
            if not polygon.is_valid:polygon=polygon.buffer(0)
            if not isinstance(polygon,Polygon) or polygon.is_empty or polygon.area<8:continue
            ring=list(orient(polygon,sign=1).exterior.coords)
            h=height(feature.get("properties") or {})
            z0=surface_z(polygon.centroid.x,polygon.centroid.y)
            ztop=z0+100*h
            # Find a viable wall for one door, based on longest wall, not known entrance.
            edges=[]
            for (x1,y1),(x2,y2) in zip(ring,ring[1:]):
                length=math.hypot(x2-x1,y2-y1)
                if length<2.8:continue
                # Clip-generated border faces aren't trustworthy facades.
                mid=((x1+x2)/2,(y1+y2)/2)
                if abs(mid[0])>253 or abs(mid[1])>253:continue
                edges.append((length,x1,y1,x2,y2))
            if not edges:continue
            door_edge=max(range(len(edges)),key=lambda idx:edges[idx][0])
            for edge_idx,(length,x1,y1,x2,y2) in enumerate(edges):
                # outward normal for CCW ring = right-hand normal
                dx=(x2-x1)/length;dy=(y2-y1)/length
                nx,ny=dy,-dx
                def panel(mesh,center,width,bottom,top,offset=12):
                    if bottom>=top:return
                    # A vertical floating panel, 12cm in front of opaque shell.
                    # Bottom/top Z in cm, coordinates X/Y meters.
                    xa=x1+dx*(center-width/2)+nx*(offset/100)
                    ya=y1+dy*(center-width/2)+ny*(offset/100)
                    xb=x1+dx*(center+width/2)+nx*(offset/100)
                    yb=y1+dy*(center+width/2)+ny*(offset/100)
                    mesh.quad((xa*100,ya*100,bottom),(xb*100,yb*100,bottom),
                              (xb*100,yb*100,top),(xa*100,ya*100,top))
                if edge_idx==door_edge and length>=3.3:
                    panel(doors,length/2,1.05,z0+12,min(z0+225,ztop-30))
                    counts["doors"]+=1
                # Small windows for each inferred floor; purely decorative.
                floors=max(1,min(5,int(round(h/3.0))))
                per_floor=max(1,min(6,int(length/3.0)))
                for floor in range(floors):
                    sill=z0+float(floor)*300+110
                    top=min(sill+120,ztop-35)
                    if top-sill<65:continue
                    for slot in range(per_floor):
                        center=length*(slot+0.5)/per_floor
                        if edge_idx==door_edge and floor==0 and abs(center-length/2)<1.4:
                            continue
                        width=min(1.0,length/per_floor*0.52)
                        panel(windows,center,width,sill,top)
                        counts["windows"]+=1
            counts["buildings"]+=1
    OUTPUT.mkdir(parents=True,exist_ok=True)
    for filename,obj in [("Chester_9thKerlin_Windows_PREVIEW.obj",windows),
                          ("Chester_9thKerlin_Doors_PREVIEW.obj",doors)]:
        if not obj.faces:raise SystemExit(f"No detail geometry produced: {filename}")
        obj.write(OUTPUT/filename)
    report={
        "status":"procedural_visual_preview_NOT_surveyed",
        "source":str(FOOTPRINTS),"source_crs":crs,
        "counts":dict(counts),"output_dir":str(OUTPUT),
        "coordinates":"same local XYZ in cm as CW_BUILDINGS_CLEANUP_V2 actor at origin",
        "vertical_reference":"matches original building shell generation, NOT adjusted to new Landscape Z=832",
        "warnings":[
            "Doors placed on longest eligible wall: NOT verified real entrances",
            "Windows are geometric overlays on opaque walls, not real openings",
            "Heights and floor counts are placeholders unless recorded by source data",
            "No pavement or collision changes; validate structure-to-road height visually"
        ]
    }
    (OUTPUT/"facade_preview_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("CW_FACADE_PREVIEW_DONE",dict(counts))
    print(OUTPUT)
if __name__=="__main__":main()

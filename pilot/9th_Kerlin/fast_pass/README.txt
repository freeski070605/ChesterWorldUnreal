CHESTERWORLD UNREAL — FAST ROAD-SURFACE PASS / 9TH & KERLIN

This package is a REAL generated, fused horizontal road polygon mesh from the supplied neighborhood_roads.json. Not a complete city or accurate terrain.

CONFIRMED:
- 112 source records -> 110 road features included (2 Amtrak rail segments excluded).
- Source roads buffered to estimated widths; overlapping road surfaces unioned into one mesh.
- 382 triangles, 7 disconnected polygon components, ~58,230 square meters of preview pavement.
- Local origin: (-75.37141354422802, 39.84831809369421), EPSG:32618.
- Unreal coordinates in centimeters X=east Y=north, at provisional Z=+100 cm.

WARNINGS:
- This is a VISUAL PREVIEW, not a playable driving road system.
- No terrain data, verified road elevations, bridges, intersections topology, collision, or vehicle controls.
- A mesh union does not prove roads are connected for navigation.
- Full city cannot be built from this 550-meter clipped source alone.

SETUP (in PowerShell):
$dest = 'E:\code\ChesterWorldUnreal\pilot\9th_Kerlin\fast_pass'
New-Item -ItemType Directory -Force $dest | Out-Null
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\ChesterWorld_9th_Kerlin_Fused_Roads.zip" -DestinationPath $dest -Force

IN UNREAL:
1. Save existing preview and create NEW Empty Level: L_9thKerlin_FusedPreview.
2. Python Editor Script Plugin enabled.
3. Python console command:
py "E:/code/ChesterWorldUnreal/pilot/9th_Kerlin/fast_pass/import_fused_roads_unreal.py"
4. Select CW_FUSED_ROADS_9TH_KERLIN_FLAT_PREVIEW in Outliner, press F, inspect in Top and Perspective.
5. Save this preview level when ready. If automatic OBJ import fails, use Content Browser > Import on the OBJ, then drag its static mesh into the level at XYZ 0,0,0.

NEXT: QA remaining disconnected source gaps, verify terrain/elevation CRS and vertical datum, then build collision and vehicle test with proper road heights.

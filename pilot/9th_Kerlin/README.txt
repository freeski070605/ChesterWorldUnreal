ChesterWorld Unreal | 9th & Kerlin NEIGHBORHOOD road preview (horizontal only)

This is not a terrain / final road mesh. Road widths are dataset estimates.
The geometry uses the regional roads source ONLY, not simultaneous county overlay.
112 road features and 127 small straight pavement strips are selected in a square 550 m across.
These strips are intentionally flat at Unreal Z=0, no elevation, intersection merging or grading.
Road centerline continuity, parallel carriageways, road class, and bridges still require visual QA.

SETUP:
1. Extract this ZIP so the files are located at:
   E:\code\ChesterWorldUnreal\pilot\9th_Kerlin\neighborhood_roads.json
   E:\code\ChesterWorldUnreal\pilot\9th_Kerlin\import_neighborhood_unreal.py
2. In Unreal 5.7, enable Python Editor Script Plugin and restart if required.
3. Create a NEW Empty Level: L_9thKerlin_NeighborhoodPreview (do not overwrite previous).
4. In Python Console run:
   py "E:/code/ChesterWorldUnreal/pilot/9th_Kerlin/import_neighborhood_unreal.py"
5. Select one CW_ROAD_PILOT actor, press F to focus, switch Top view.
6. Save the new preview level only after inspecting it.

NEXT: attach verified terrain elevation and QA intersections before any final road materials.

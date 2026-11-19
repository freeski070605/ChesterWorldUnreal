ChesterWorld 9th & Kerlin — fixed fused-road mesh

ROOT CAUSE: All 382 faces in original OBJ were clockwise as viewed from above,
meaning their normals pointed DOWN. Unreal hides the top side by default.
This corrected OBJ reverses each triangle's winding. Same vertices, same
horizontal position and same provisional Z=+100 cm; no geography altered.

1. Close Unreal Editor before copying only if you prefer; otherwise leave it open.
2. Extract BOTH files from this ZIP to:
   E:\code\ChesterWorldUnreal\pilot\9th_Kerlin\fast_pass\
3. In Unreal open the level containing your fused road actor.
4. Run in Python Console:
   py "E:/code/ChesterWorldUnreal/pilot/9th_Kerlin/fast_pass/fix_fused_roads_unreal.py"
5. Select CW_FUSED_ROADS_9TH_KERLIN_FLAT_PREVIEW, press F, view in Perspective/Lit.
6. Open the new Static Mesh asset and ensure triangles are visible.
7. Save the level after you see the road geometry.

This changes only the displayed mesh on the fused actor and places the fixed
mesh into a new asset; it does not delete old road actors or assets.
Provisional flat surfaces; no verified elevation, collision or driving yet.

# Neighborhood road pilot preview

The neighborhood horizontal road surface preview is derived from the user-supplied `9th_Kerlin_Geometry_Audit_v2.zip` and is distributed in the chat as `ChesterWorld_9th_Kerlin_Neighborhood_Preview.zip`.

- 112 retained regional road features and 127 visible segment strips in a local 550 m square centered on the provisional 9th/Kerlin source node.
- Source: `18_StreetSystemV3/regional_motor_roads_v3.geojson`, clipped and projected EPSG:4326 → EPSG:32618, local origin `-75.37141354422802, 39.84831809369421`, 1 meter = 100 Unreal cm.
- Original county road layer is not drawn simultaneously, avoiding a predictable overlay.
- The demo is **flat, unsurveyed and explicitly provisional**. Road widths are generated estimates and junctions are not merged. No grade-separated geometry is resolved.
- Do not deploy it to the real citywide level or interpret it as verified street elevations.

## Install from supplied ZIP
Unzip `neighborhood_roads.json` and `import_neighborhood_unreal.py` to `E:\\code\\ChesterWorldUnreal\\pilot\\9th_Kerlin\\`, then create a **new empty level** `L_9thKerlin_NeighborhoodPreview`.

In Unreal 5.7's Python console with Python Editor Script Plugin enabled:

```
py "E:/code/ChesterWorldUnreal/pilot/9th_Kerlin/import_neighborhood_unreal.py"
```

Inspect Top and Perspective views before saving the preview. No existing road actors will be deleted and re-running on an already imported level errors out to avoid duplicates. Next milestone is elevation sourcing and intersection/bridge QA.

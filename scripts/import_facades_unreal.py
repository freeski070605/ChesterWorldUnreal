"""UE 5.7: import non-destructive facade overlays into copy of CleanupV2 level.

Run in Unreal Python console:
py "E:/code/ChesterWorldUnreal/scripts/import_facades_unreal.py"
Doesn't touch roads/terrain/buildings/car or collision. Save test level manually.
"""
from pathlib import Path
import unreal

SOURCE=Path(r"E:\ChesterWorld\Reports\UnrealFacadePilot")
DEST="/Game/ChesterWorld/Generated/9thKerlinFacades"
ITEMS=[
    ("Chester_9thKerlin_Windows_PREVIEW.obj","CW_WINDOWS_PREVIEW",(0.06,0.11,0.14)),
    ("Chester_9thKerlin_Doors_PREVIEW.obj","CW_DOORS_PREVIEW",(0.18,0.11,0.08)),
]
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
existing={a.get_actor_label() for a in sub.get_all_level_actors()}
if any(label in existing for _,label,_ in ITEMS):
    raise RuntimeError("Facade actor already present. Refusing duplicate import.")
if not all((SOURCE/name).is_file() for name,_,_ in ITEMS):
    raise RuntimeError("Facade preview OBJ(s) missing. Run build_9th_kerlin_facades.py first.")

def colored_material(label,rgb):
    path=DEST+"/"+label
    asset=unreal.load_asset(path)
    if asset:return asset
    asset=unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        label, DEST, unreal.Material, unreal.MaterialFactoryNew()
    )
    lib=unreal.MaterialEditingLibrary
    color=lib.create_material_expression(asset,unreal.MaterialExpressionConstant3Vector,-350,0)
    color.set_editor_property("constant",unreal.LinearColor(rgb[0],rgb[1],rgb[2],1))
    lib.connect_material_property(color,"",unreal.MaterialProperty.MP_BASE_COLOR)
    rough=lib.create_material_expression(asset,unreal.MaterialExpressionConstant,-350,180)
    rough.set_editor_property("r",0.65)
    lib.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS)
    lib.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset

for filename,label,rgb in ITEMS:
    task=unreal.AssetImportTask()
    task.set_editor_property("filename",str(SOURCE/filename))
    task.set_editor_property("destination_path",DEST)
    task.set_editor_property("automated",True)
    task.set_editor_property("replace_existing",False)
    task.set_editor_property("save",True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths=list(task.get_editor_property("imported_object_paths"))
    asset=next((a for p in paths if isinstance((a:=unreal.load_asset(p)),unreal.StaticMesh)),None)
    if not asset:raise RuntimeError("OBJ did not import as StaticMesh: "+str(paths))
    actor=sub.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
    if not actor:raise RuntimeError("Could not spawn actor "+label)
    actor.set_actor_label(label)
    actor.set_actor_location(unreal.Vector(0,0,0),False,False)
    component=actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(asset)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    try:
        component.set_material(0,colored_material("M_"+label,rgb))
    except Exception as exc:
        unreal.log_warning("Material setup needs manual assignment for "+label+": "+str(exc))
    print("CW_FACADE_IMPORT_OK",label,asset.get_path_name())
unreal.log_warning("CW_FACADE_PREVIEW_DONE: placeholder windows/doors imported. NO real entrance/window survey claimed. Save level after inspection.")

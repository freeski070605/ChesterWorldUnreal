"""ChesterWorld UE 5.7 — non-destructive visual cleanup pass.

Open a COPY of the GradeTest level, e.g. L_ChesterWorld_9thKerlin_CleanupV2.
Imports the new building OBJ and applies separate asphalt/building preview materials.
Does not delete old buildings, roads, or terrain; hides OLD building actors only
inside the current level for comparison. It does not touch vehicle assets.
"""
from pathlib import Path
import unreal

SOURCE=Path(r'E:\ChesterWorld\Reports\UnrealBuildingPilot\CleanupV2\Chester_9thKerlin_BuildingShells_CLEANUP_V2.obj')
ASSET_DIR='/Game/ChesterWorld/Generated/9thKerlinCleanupV2'
NEW_LABEL='CW_BUILDINGS_CLEANUP_V2'
OLD_LABEL='CW_BUILDING_SHELLS_PREVIEW'
ROAD_LABEL='CW_DRAPED_ROADS_PREVIEW'
if not SOURCE.exists():
    raise RuntimeError('Missing building v2 OBJ. Run scripts/build_9th_kerlin_buildings_cleanup.py first.')
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors=sub.get_all_level_actors()
if any(a.get_actor_label()==NEW_LABEL for a in all_actors):
    raise RuntimeError('V2 building actor already present. Refusing duplicate.')

task=unreal.AssetImportTask()
task.set_editor_property('filename',str(SOURCE))
task.set_editor_property('destination_path',ASSET_DIR)
task.set_editor_property('automated',True)
task.set_editor_property('replace_existing',False)
task.set_editor_property('save',True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths=list(task.get_editor_property('imported_object_paths'))
mesh=next((v for p in paths if isinstance((v:=unreal.load_asset(p)),unreal.StaticMesh)),None)
if not mesh:
    raise RuntimeError('OBJ import did not create Static Mesh: '+str(paths))
spawned=sub.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
if not spawned:raise RuntimeError('Failed spawning building actor')
spawned.set_actor_label(NEW_LABEL)
spawned.set_actor_location(unreal.Vector(0,0,0),False,False)
spawned.set_actor_scale3d(unreal.Vector(1,1,1))
component=spawned.get_component_by_class(unreal.StaticMeshComponent)
component.set_static_mesh(mesh)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

def preview_material(asset_name, rgb):
    path=ASSET_DIR+'/'+asset_name
    existing=unreal.load_asset(path)
    if existing:return existing
    material=unreal.AssetToolsHelpers.get_asset_tools().create_asset(asset_name,ASSET_DIR,unreal.Material,unreal.MaterialFactoryNew())
    if not material:raise RuntimeError('Unable to create '+asset_name)
    editor=unreal.MaterialEditingLibrary
    col=editor.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-350,0)
    col.set_editor_property('constant',unreal.LinearColor(*rgb,1.0))
    editor.connect_material_property(col,'',unreal.MaterialProperty.MP_BASE_COLOR)
    rough=editor.create_material_expression(material,unreal.MaterialExpressionConstant,-350,180)
    rough.set_editor_property('r',0.92)
    editor.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    editor.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material

try:
    wall=preview_material('M_CW_BuildingStone_Preview',(0.43,0.36,0.30))
    pavement=preview_material('M_CW_Asphalt_Preview',(0.11,0.12,0.13))
    component.set_material(0,wall)
    road_actors=[a for a in all_actors if a.get_actor_label()==ROAD_LABEL]
    for road in road_actors:
        smc=road.get_component_by_class(unreal.StaticMeshComponent)
        if smc:smc.set_material(0,pavement)
except Exception as exc:
    unreal.log_warning('CW cleanup material step incomplete; geometry remains imported. Error: '+str(exc))

for a in all_actors:
    if a.get_actor_label()==OLD_LABEL:
        a.set_is_temporarily_hidden_in_editor(True)
        # Also hide during play in this copy; safe because existing actor preserved.
        a.set_actor_hidden_in_game(True)

unreal.log_warning('CW_BUILDINGS_CLEANUP_V2_DONE: New building actor created. Visual preview ONLY; ground datum, terrain orientation and road driving require validation. Save the test level after inspection.')
print('CW_BUILDINGS_CLEANUP_V2_DONE')

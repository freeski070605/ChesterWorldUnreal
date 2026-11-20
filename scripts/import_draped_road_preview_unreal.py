"""UE 5.7: non-destructive terrain-draped road preview import.

Open a COPY of the combined terrain/buildings map before running.
Spawns a distinct preview actor, never deletes or reassigns existing roads.
The new mesh has no collision until specifically verified.
"""
from pathlib import Path
import unreal

SOURCE=Path(r'E:\ChesterWorld\Reports\UnrealRoadTerrainPilot\Chester_9thKerlin_Roads_Draped_PREVIEW.obj')
ASSET_DIR='/Game/ChesterWorld/Generated/9thKerlinRoadGrade'
LABEL='CW_DRAPED_ROADS_PREVIEW'
if not SOURCE.is_file():
    raise RuntimeError('Draped OBJ missing: '+str(SOURCE))
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if any(a.get_actor_label()==LABEL for a in actors.get_all_level_actors()):
    raise RuntimeError('Draped preview already present; do not duplicate.')
task=unreal.AssetImportTask()
task.set_editor_property('filename',str(SOURCE))
task.set_editor_property('destination_path',ASSET_DIR)
task.set_editor_property('automated',True)
task.set_editor_property('save',True)
task.set_editor_property('replace_existing',False)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths=list(task.get_editor_property('imported_object_paths'))
mesh=next((m for p in paths if isinstance((m:=unreal.load_asset(p)),unreal.StaticMesh)),None)
if mesh is None:
    raise RuntimeError('Could not load road StaticMesh from '+str(paths))
actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
if not actor:
    raise RuntimeError('Unreal did not spawn actor.')
actor.set_actor_label(LABEL)
actor.set_actor_location(unreal.Vector(0,0,0),False,False)
actor.set_actor_scale3d(unreal.Vector(1,1,1))
component=actor.get_component_by_class(unreal.StaticMeshComponent)
component.set_static_mesh(mesh)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
print('CW_DRAPED_ROADS_IMPORTED',mesh.get_path_name())
unreal.log_warning('Draped roads are a visual-only grade preview: current landscape not surveyed. Do not drive on these until collision and elevations are validated. Keep original flat roads.')

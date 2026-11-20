"""UE 5.7 building-shell preview importer. Run only in a COPY of V1 integration level.
Run from Unreal Python Console:
py "E:/code/ChesterWorldUnreal/scripts/import_building_shells_unreal.py"
Does not modify existing road mesh, landscape, or car. Save manually after inspection.
"""
from pathlib import Path
import unreal

SOURCE=Path(r'E:\ChesterWorld\Reports\UnrealBuildingPilot\Chester_9thKerlin_BuildingShells_PREVIEW.obj')
DESTINATION='/Game/ChesterWorld/Generated/9thKerlinBuildings'
LABEL='CW_BUILDING_SHELLS_PREVIEW'
if not SOURCE.is_file():
    raise RuntimeError('Building OBJ missing; run local generator first: '+str(SOURCE))
subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if any(a.get_actor_label()==LABEL for a in subsystem.get_all_level_actors()):
    raise RuntimeError('Preview building actor already exists. No duplicate import performed.')
task=unreal.AssetImportTask()
task.set_editor_property('filename',str(SOURCE))
task.set_editor_property('destination_path',DESTINATION)
task.set_editor_property('automated',True)
task.set_editor_property('replace_existing',False)
task.set_editor_property('save',True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths=list(task.get_editor_property('imported_object_paths'))
mesh=None
for path in paths:
    candidate=unreal.load_asset(path)
    if isinstance(candidate,unreal.StaticMesh):
        mesh=candidate
        break
if mesh is None:
    mesh=unreal.load_asset(DESTINATION+'/Chester_9thKerlin_BuildingShells_PREVIEW')
if not isinstance(mesh,unreal.StaticMesh):
    raise RuntimeError('OBJ failed to import as StaticMesh; inspect Output Log. Paths: '+str(paths))
if hasattr(mesh,'get_num_triangles') and mesh.get_num_triangles(0)<=0:
    raise RuntimeError('Building mesh has no triangles. Refusing to spawn.')
actor=subsystem.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
if actor is None:
    raise RuntimeError('Could not spawn building actor')
actor.set_actor_label(LABEL)
component=actor.get_component_by_class(unreal.StaticMeshComponent)
component.set_static_mesh(mesh)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
actor.set_actor_scale3d(unreal.Vector(1,1,1))
unreal.log_warning('CW_BUILDINGS_IMPORTED: Estimated-height shells. DEM datum/orientation unverified; visual preview only.')
print('CW_BUILDINGS_IMPORTED:',mesh.get_path_name())

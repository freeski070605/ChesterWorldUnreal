"""Unreal 5.7 Editor Python: import upward-facing fused road mesh and replace blank mesh.

Run in your current road preview level. No actors are deleted and no level is saved.
Uses separate _UP static mesh asset so the old asset remains available.
"""
from pathlib import Path
import unreal

ROOT = Path(r'E:\code\ChesterWorldUnreal\pilot\9th_Kerlin\fast_pass')
SOURCE = ROOT / 'Chester_9th_Kerlin_FusedRoads_UP.obj'
ASSET_PATH = '/Game/ChesterWorld/Generated/9thKerlin'
LABEL = 'CW_FUSED_ROADS_9TH_KERLIN_FLAT_PREVIEW'

if not SOURCE.is_file():
    raise RuntimeError('Missing fixed OBJ at: ' + str(SOURCE))

actors = [a for a in unreal.EditorLevelLibrary.get_all_level_actors()
          if a.get_actor_label() == LABEL]
if len(actors) != 1:
    raise RuntimeError('Expected one fused road actor; found %d' % len(actors))

# Distinct filename/asset path avoids reusing the previous possibly-empty asset.
task = unreal.AssetImportTask()
task.set_editor_property('filename', str(SOURCE))
task.set_editor_property('destination_path', ASSET_PATH)
task.set_editor_property('automated', True)
task.set_editor_property('replace_existing', False)
task.set_editor_property('save', True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = list(task.get_editor_property('imported_object_paths'))
mesh = None
for p in paths:
    asset = unreal.load_asset(p)
    if isinstance(asset, unreal.StaticMesh):
        mesh = asset
        break
if mesh is None:
    # Asset may exist already on a repeated run.
    mesh = unreal.load_asset(ASSET_PATH + '/Chester_9th_Kerlin_FusedRoads_UP')
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError('Fixed OBJ failed to import as a StaticMesh. See Output Log. Imported: %s' % paths)

# Ensure there are triangles before touching the actor's current asset.
try:
    triangle_count = mesh.get_num_triangles(0)
    print('Fixed mesh triangle count:', triangle_count)
    if triangle_count <= 0:
        raise RuntimeError('Imported mesh has zero triangles; refusing to replace current mesh.')
except AttributeError:
    unreal.log_warning('Unable to query mesh triangle count; visually verify asset in Static Mesh Editor.')

component = actors[0].get_component_by_class(unreal.StaticMeshComponent)
if component is None:
    raise RuntimeError('Selected fused road actor has no StaticMeshComponent')
component.set_static_mesh(mesh)
actors[0].set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, False)
actors[0].set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
print('ChesterWorld fixed mesh assigned:', mesh.get_path_name())
unreal.log_warning('Fixed road faces now point UP; switch to Perspective/Lit and press F on the fused road actor. Save manually after confirmation.')

"""UE 5.7 Editor: import fused 9th & Kerlin road mesh into CURRENT LEVEL.

Open a NEW empty level first. Run in Unreal Python console:
py "E:/code/ChesterWorldUnreal/pilot/9th_Kerlin/fast_pass/import_fused_roads_unreal.py"

NO automatic deletion or saving of current level; no collision or landscape.
"""
from pathlib import Path
import unreal

ROOT = Path(r'E:\code\ChesterWorldUnreal\pilot\9th_Kerlin\fast_pass')
SOURCE = ROOT / 'Chester_9th_Kerlin_FusedRoads.obj'
ASSET_DIR = '/Game/ChesterWorld/Generated/9thKerlin'
ACTOR_LABEL = 'CW_FUSED_ROADS_9TH_KERLIN_FLAT_PREVIEW'

if not SOURCE.exists():
    raise RuntimeError('Missing OBJ at ' + str(SOURCE))

actors = unreal.EditorLevelLibrary.get_all_level_actors()
if any(a.get_actor_label() == ACTOR_LABEL for a in actors):
    raise RuntimeError('Preview actor already exists; use a NEW level or inspect it manually.')

# The editor's import pipeline infers the importer for the .obj file.
task = unreal.AssetImportTask()
task.set_editor_property('filename', str(SOURCE))
task.set_editor_property('destination_path', ASSET_DIR)
task.set_editor_property('automated', True)
task.set_editor_property('replace_existing', False)
task.set_editor_property('save', True)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
asset_tools.import_asset_tasks([task])
imported = list(task.get_editor_property('imported_object_paths'))
if not imported:
    raise RuntimeError('OBJ import returned no assets. Use Content Browser > Import on the OBJ and inspect Output Log.')

mesh = next((unreal.load_asset(p) for p in imported if isinstance(unreal.load_asset(p), unreal.StaticMesh)), None)
if mesh is None:
    raise RuntimeError('Imported assets were not StaticMesh: ' + repr(imported))

actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
    mesh, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0)
)
if actor is None:
    raise RuntimeError('Static mesh imported but actor spawn failed')
actor.set_actor_label(ACTOR_LABEL)
# Default collision on this imported OBJ is not guaranteed. Preview only.
unreal.log_warning('ChesterWorld: fused horizontal road preview imported. 110 features, 7 disconnected polygon components, 382 triangles. Z is arbitrary. No verified collision, grading or terrain.')
unreal.log_warning('Select ' + ACTOR_LABEL + ', press F, inspect Top/Perspective, save preview as a NEW level if correct.')

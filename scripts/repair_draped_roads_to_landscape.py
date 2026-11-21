"""Rebuild ChesterWorld draped road collision against the CURRENT Unreal Landscape.

Run with L_ChesterWorld_9thKerlin_FacadesV1 open and Play stopped:
  py "E:/code/ChesterWorldUnreal/scripts/repair_draped_roads_to_landscape.py"

Uses the existing road OBJ's exact XY triangles but samples the *actual Landscape
heightfield collision* at each vertex. Imports a NEW mesh asset and switches only
CW_DRAPED_ROADS_PREVIEW to it after successful import. The old mesh asset is retained.
Never moves the Landscape, car or buildings. No asset/level auto-save.
"""
from pathlib import Path
import statistics
import unreal

SOURCE = Path(r"E:\ChesterWorld\Reports\UnrealRoadTerrainPilot\Chester_9thKerlin_Roads_Draped_PREVIEW.obj")
OUTPUT = SOURCE.with_name("Chester_9thKerlin_Roads_LandscapeAligned_V2.obj")
DEST = "/Game/ChesterWorld/Generated/9thKerlinRoadGrade/LandscapeAlignedV2"
ROAD_LABEL = "CW_DRAPED_ROADS_PREVIEW"
CLEARANCE_CM = 8.0
START_Z, END_Z = 100000.0, -100000.0

if not SOURCE.is_file():
    raise RuntimeError("Missing draped road OBJ: " + str(SOURCE))

actors_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = list(actors_subsystem.get_all_level_actors())
road_candidates = [a for a in actors if a.get_actor_label() == ROAD_LABEL]
landscapes = [a for a in actors if isinstance(a, unreal.Landscape)]
if len(road_candidates) != 1 or len(landscapes) != 1:
    raise RuntimeError("Expected exactly one draped road actor and one Landscape; "
                       f"found {len(road_candidates)} road(s), {len(landscapes)} Landscape(s)")
road = road_candidates[0]
landscape = landscapes[0]
road_comp = road.get_component_by_class(unreal.StaticMeshComponent)
previous_mesh = road_comp.get_editor_property("static_mesh")
if previous_mesh is None:
    raise RuntimeError("Road actor has no existing mesh. Aborting.")
if (abs(road.get_actor_location().x) > 0.01 or
    abs(road.get_actor_location().y) > 0.01 or
    abs(road.get_actor_location().z) > 0.01):
    raise RuntimeError("Road actor transform is no longer zero; refusing unverified import.")

world = unreal.EditorLevelLibrary.get_editor_world()
ignored = [a for a in actors if a != landscape]

# Unreal 5.7 line_trace_single returns HitResult; to_tuple()[0] is blocking-hit,
# and to_tuple()[5] is impact_point, as verified with this exact project.
cache = {}
samples = []
def surface_z(x, y):
    # The original draped OBJ slightly exceeds the 535.5m Landscape footprint.
    # Match the old preview's edge-clamp behavior; never abort on border roads.
    sample_x = max(-26750.0, min(26750.0, x))
    sample_y = max(-26750.0, min(26750.0, y))
    key = (round(sample_x, 3), round(sample_y, 3))
    if key in cache:
        return cache[key]
    result = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(sample_x, sample_y, START_Z),
        unreal.Vector(sample_x, sample_y, END_Z),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
        ignored, unreal.DrawDebugTrace.NONE, True
    )
    value = result.to_tuple()
    if not value[0]:
        raise RuntimeError(f"Landscape collision missing at x={x:.2f} y={y:.2f}. "
                           "Source road extends beyond terrain; no partial mesh imported.")
    if value[9] != landscape:
        raise RuntimeError(f"Trace hit wrong actor {value[9]} at {sample_x:.2f},{sample_y:.2f}")
    z = float(value[5].z)
    cache[key] = z
    return z

# Preserve original triangle winding, topology and XY exactly.
# Stage into memory first to avoid partially-written output on a missed trace.
output_lines = []
vertices = 0
triangles = 0
for line in SOURCE.open("r", encoding="utf-8", errors="replace"):
    if line.startswith("v "):
        parts = line.split()
        if len(parts) < 4:
            raise RuntimeError("Malformed OBJ vertex")
        x, y, old_z = map(float, parts[1:4])
        z = surface_z(x, y) + CLEARANCE_CM
        if len(samples) < 200000:
            samples.append(z - old_z)
        output_lines.append(f"v {x:.3f} {y:.3f} {z:.3f}\n")
        vertices += 1
    else:
        output_lines.append(line)
        if line.startswith("f "):
            triangles += 1

if vertices < 3 or triangles < 1:
    raise RuntimeError("Unexpected empty road mesh.")
OUTPUT.write_text("".join(output_lines), encoding="utf-8")
print("CW_ROAD_REPAIR_GEOMETRY:", vertices, "vertices", triangles, "triangles",
      "landscape heights sampled", len(cache))
print("CW_ROAD_REPAIR_Z_DELTA_CM:", round(min(samples), 2),
      "to", round(max(samples), 2), "median", round(statistics.median(samples), 2))
print("CW_ROAD_REPAIR_OUTPUT:", OUTPUT)

task = unreal.AssetImportTask()
task.set_editor_property("filename", str(OUTPUT))
task.set_editor_property("destination_path", DEST)
task.set_editor_property("automated", True)
task.set_editor_property("save", False)
task.set_editor_property("replace_existing", False)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths"))
mesh = next((obj for p in paths
             if isinstance((obj := unreal.load_asset(p)), unreal.StaticMesh)), None)
if mesh is None:
    raise RuntimeError("Import failed; original road actor and mesh untouched: " + str(paths))

flag = unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
mesh_editor_cls = getattr(unreal, "StaticMeshEditorSubsystem", None)
set_collision = None
if mesh_editor_cls:
    mesh_editor = unreal.get_editor_subsystem(mesh_editor_cls)
    set_collision = getattr(mesh_editor, "set_collision_complexity", None)
if callable(set_collision):
    set_collision(mesh, flag)
else:
    body = mesh.get_editor_property("body_setup")
    if body is None:
        raise RuntimeError("New mesh imported but cannot configure complex collision; road actor unchanged.")
    body.set_editor_property("collision_trace_flag", flag)
    mesh.modify()

road_comp.set_static_mesh(mesh)
road_comp.set_collision_profile_name("BlockAll")
road_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
road_comp.set_editor_property("generate_overlap_events", False)
road_comp.modify()
road.modify()
print("CW_ROADS_REPLACED_WITH_LANDSCAPE_ALIGNED_MESH:", mesh.get_path_name())
print("CW_OLD_ROAD_MESH_RETAINED:", previous_mesh.get_path_name())
unreal.log_warning("Save the NEW mesh asset and level after inspection. "
                   "Original mesh retained. This restores terrain-following street collision, "
                   "not bridge grades; buildings may require separate height adjustment.")

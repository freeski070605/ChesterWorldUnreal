"""Measure actual draped-road Z against *Unreal Landscape collision*.

Run in current CleanupV2 level, with game NOT playing:
py "E:/code/ChesterWorldUnreal/scripts/audit_draped_road_ground.py"
Read-only. Prints measured signed road-ground height differences.
This avoids resampling the source PNG, which could disagree with imported Landscape.
"""
import math
from pathlib import Path
import unreal

SOURCE = Path(r"E:\ChesterWorld\Reports\UnrealRoadTerrainPilot\Chester_9thKerlin_Roads_Draped_PREVIEW.obj")
ROAD_LABEL = "CW_DRAPED_ROADS_PREVIEW"
TERRAIN_LABEL = "Landscape"
SAMPLE_MAX = 60
TRACE_START = 100000.0
TRACE_END = -100000.0

if not SOURCE.is_file():
    raise RuntimeError("Missing draped road OBJ: " + str(SOURCE))
subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = subs.get_all_level_actors()
roads = [a for a in actors if a.get_actor_label() == ROAD_LABEL]
terrains = [a for a in actors if isinstance(a, unreal.Landscape)]
if len(roads) != 1 or len(terrains) != 1:
    raise RuntimeError(f"Expected 1 draped road and 1 Landscape. Got {len(roads)} roads and {len(terrains)} landscapes.")
road = roads[0]
terrain = terrains[0]
world = unreal.EditorLevelLibrary.get_editor_world()
road_transform = road.get_actor_transform()
# Exclude other meshes so the collision trace reports the landscape.
ignored = [a for a in actors if a != terrain]
points = []
with SOURCE.open("r", encoding="utf-8", errors="replace") as f:
    for line in f:
        if line.startswith("v "):
            chunks = line.split()
            points.append((float(chunks[1]), float(chunks[2]), float(chunks[3])))
if len(points) < 3:
    raise RuntimeError("OBJ has fewer than three vertices")
# Sample across the file deterministically and eliminate duplicate XY locations.
stride = max(1, len(points) // (SAMPLE_MAX * 8))
sample_pts = []
seen = set()
for x, y, z in points[::stride]:
    key = (round(x / 150), round(y / 150))
    if key in seen:
        continue
    seen.add(key)
    sample_pts.append((x, y, z))
    if len(sample_pts) == SAMPLE_MAX:
        break
deltas = []
misses = 0
for x, y, z in sample_pts:
    p = road_transform.transform_location(unreal.Vector(x, y, z))
    start = unreal.Vector(p.x, p.y, TRACE_START)
    end = unreal.Vector(p.x, p.y, TRACE_END)
    # Assumes landscape blocks Visibility trace. If it does not, log misses.
    hit, result = unreal.SystemLibrary.line_trace_single(
        world, start, end,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        False, ignored,
        unreal.DrawDebugTrace.NONE, True
    )
    if not hit:
        misses += 1
        continue
    impact = result.get_editor_property("impact_point")
    delta = p.z - impact.z
    deltas.append(delta)
    unreal.log_warning(
        "CW_GROUND_SAMPLE XY=(%.1f,%.1f) roadZ=%.1f groundZ=%.1f road_minus_ground_cm=%+.1f"
        % (p.x, p.y, p.z, impact.z, delta)
    )
if not deltas:
    raise RuntimeError(
        "No Landscape collision hits. Do NOT adjust road position: check Landscape Visibility collision and World Partition cell loading."
    )
deltas.sort()
mid = deltas[len(deltas)//2]
msg = (
    "CW_GROUND_AUDIT_DONE samples=%d misses=%d min_cm=%+.1f median_cm=%+.1f max_cm=%+.1f "
    "positive=hovering negative=buried. Warning: source heights/vertical datum still unverified."
    % (len(deltas), misses, deltas[0], mid, deltas[-1])
)
print(msg)
unreal.log_warning(msg)

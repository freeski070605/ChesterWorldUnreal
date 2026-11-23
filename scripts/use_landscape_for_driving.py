"""ChesterWorld 9th/Kerlin: use Landscape collision for driving, roads for visuals.

After the aligned V2 import, in UE 5.7 editor Python console:
  py "E:/code/ChesterWorldUnreal/scripts/use_landscape_for_driving.py"

Only applies when ROAD and Landscape surfaces at the verified pilot XY are within 35 cm.
If they're not aligned, fails WITHOUT changing anything.
This is a diagnostic workaround for bad triangles/overlap in the generated
road collider; it does NOT alter the vehicle, heights, or mesh assets.
"""
import unreal

ROAD_LABEL = "CW_DRAPED_ROADS_PREVIEW"
SAMPLE_X = -6610.0
SAMPLE_Y = 2820.0  # previously verified road/Landscape collision location
MAX_GAP_CM = 35.0

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = list(sub.get_all_level_actors())
def unique(pred, name):
    found = [a for a in actors if pred(a)]
    if len(found) != 1:
        raise RuntimeError(f"Need exactly one {name}; found {len(found)}")
    return found[0]

road = unique(lambda a: a.get_actor_label() == ROAD_LABEL, ROAD_LABEL)
land = unique(lambda a: isinstance(a, unreal.Landscape), "Landscape")
road_comp = road.get_component_by_class(unreal.StaticMeshComponent)
if road_comp is None:
    raise RuntimeError("Road static mesh component not found")
land_comps = list(land.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent))
if not land_comps:
    raise RuntimeError("No LandscapeHeightfieldCollisionComponent found")

world = unreal.EditorLevelLibrary.get_editor_world()
def trace(target):
    ignored = [a for a in actors if a != target]
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(SAMPLE_X,SAMPLE_Y,100000),
        unreal.Vector(SAMPLE_X,SAMPLE_Y,-100000),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
        ignored, unreal.DrawDebugTrace.NONE, True
    ).to_tuple()
    if not hit[0] or hit[9] != target:
        raise RuntimeError(f"Missing collision for {target.get_actor_label()} at pilot sample XY")
    return float(hit[5].z)

road_z = trace(road)
land_z = trace(land)
gap = road_z - land_z
print(f"CW_DRIVE_SURFACES road={road_z:.2f} landscape={land_z:.2f} gap={gap:.2f} cm")
if abs(gap) > MAX_GAP_CM:
    raise RuntimeError(
        f"Road/Landscape gap {gap:.2f} cm exceeds {MAX_GAP_CM}; "
        "old draped roads still don't follow the Landscape. "
        "Run repair_draped_roads_to_landscape.py successfully first. "
        "NO collision settings changed."
    )

# With a road only 8cm above the heightfield, wheels can collide with the
# Landscape itself. Remove potentially unstable triangulated road contact.
for comp in land_comps:
    comp.set_collision_profile_name("BlockAll")
    comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    comp.modify()
road_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
road_comp.modify()
road.modify()
land.modify()
print("CW_LANDSCAPE_DRIVING_ENABLED",
      "road visual only; landscape is drivable; save level after driving test")

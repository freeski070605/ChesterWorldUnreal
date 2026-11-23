"""ChesterWorld 9th/Kerlin: use Landscape collision for driving, roads for visuals.

After the aligned V2 import, in UE 5.7 editor Python console:
  py "E:/code/ChesterWorldUnreal/scripts/use_landscape_for_driving.py"

At the verified pilot sample XY, shifts the road actor downward by the measured
excess clearance so its visual surface sits 8 cm above Landscape collision.
Safeguard: permits up to 250 cm correction for the measured original FacadesV1\nroad gap; refuses larger corrections. Other locations may differ.
This is a diagnostic workaround for bad triangles/overlap in the generated
road collider; it does NOT alter the vehicle, heights, or mesh assets.
"""
import unreal

ROAD_LABEL = "CW_DRAPED_ROADS_PREVIEW"
SAMPLE_X = -6610.0
SAMPLE_Y = 2820.0  # previously verified road/Landscape collision location
TARGET_CLEARANCE_CM = 8.0
MAX_ADJUSTMENT_CM = 250.0

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
adjustment = TARGET_CLEARANCE_CM - gap
if abs(adjustment) > MAX_ADJUSTMENT_CM:
    raise RuntimeError(
        f"Required road Z shift {adjustment:.2f} cm exceeds "
        f"{MAX_ADJUSTMENT_CM} cm safety limit. No changes made."
    )

# Apply visual height correction to road ACTOR, not vehicle or Landscape.
# This is a pilot workaround, calibrated at the verified sample XY.
# Check before-and-after with the same world collision traces.
old_location = road.get_actor_location()
if abs(adjustment) > 0.1:
    road.set_actor_location(
        unreal.Vector(old_location.x, old_location.y,
                      old_location.z + adjustment),
        False, False
    )
    corrected_z = trace(road)
    corrected_gap = corrected_z - land_z
    print(f"CW_ROAD_ALIGNED corrected_gap={corrected_gap:.2f} cm "
          f"road_actor_shift={adjustment:.2f} cm")
    if abs(corrected_gap - TARGET_CLEARANCE_CM) > 1.0:
        road.set_actor_location(old_location, False, False)
        raise RuntimeError(
            "Road height correction did not produce expected collision height. "
            "Road location restored; no collision changes made."
        )
else:
    print("CW_ROAD_ALREADY_ALIGNED")

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
      "road visual aligned at pilot XY; Landscape is drivable; save level after driving test")

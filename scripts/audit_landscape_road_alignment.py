"""Read-only ChesterWorld road/landscape bounds and vertical contact audit.

Run from Unreal Editor's Python console in L_ChesterWorld_9thKerlin_V1.
It does NOT move, edit, or save actors. Outputs to Unreal Output Log.
"""
import unreal

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
roads = [a for a in actors if a.get_actor_label().startswith("CW_FUSED_ROADS")]
terrains = [a for a in actors if isinstance(a, unreal.Landscape)]
if len(roads) != 1 or len(terrains) != 1:
    raise RuntimeError(f"Expected one fused road and one Landscape. Found roads={len(roads)}, landscapes={len(terrains)}")

road, terrain = roads[0], terrains[0]

def bbox(a):
    origin, extent = a.get_actor_bounds(False)
    center = a.get_actor_location()
    return {
        "name":a.get_actor_label(),
        "location_cm": (round(center.x,2),round(center.y,2),round(center.z,2)),
        "bounds_min_cm": (round(origin.x-extent.x,2),round(origin.y-extent.y,2),round(origin.z-extent.z,2)),
        "bounds_max_cm": (round(origin.x+extent.x,2),round(origin.y+extent.y,2),round(origin.z+extent.z,2)),
        "bounds_center_cm": (round(origin.x,2),round(origin.y,2),round(origin.z,2)),
        "extent_cm": (round(extent.x,2),round(extent.y,2),round(extent.z,2))
    }

rb, tb = bbox(road),bbox(terrain)
unreal.log_warning("CW_ALIGNMENT_ROADS " + str(rb))
unreal.log_warning("CW_ALIGNMENT_TERRAIN " + str(tb))
ro = road.get_actor_bounds(False)[0]
to = terrain.get_actor_bounds(False)[0]
unreal.log_warning("CW_ALIGNMENT_DELTA_ROAD_TO_TERRAIN_CENTER_CM " +
    str((round(to.x-ro.x,2),round(to.y-ro.y,2),round(to.z-ro.z,2))))

# Collision traces against terrain only. No changes to the world.
world = unreal.EditorLevelLibrary.get_editor_world()
if not world:
    raise RuntimeError("No editor world available")

for name,offset in [("source_origin", (0,0)),("north_50m",(0,5000)),
                    ("south_50m",(0,-5000)),("east_50m",(5000,0)),
                    ("west_50m",(-5000,0))]:
    x,y = offset
    try:
        hits = unreal.SystemLibrary.line_trace_multi(
            world,unreal.Vector(x,y,200000),unreal.Vector(x,y,-200000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[road],unreal.DrawDebugTrace.NONE,
            True,unreal.LinearColor(1,0,0,1),unreal.LinearColor(0,1,0,1),0)
        valid = [h for h in hits if h.get_editor_property("hit_object_handle") == terrain]
        # The hit API varies across engine builds. Print all actors hit instead.
        items=[]
        for h in hits:
            a=h.get_editor_property("hit_object_handle")
            label=a.get_actor_label() if a and hasattr(a,"get_actor_label") else str(a)
            loc=h.get_editor_property("impact_point")
            items.append((label,round(loc.z,2)))
        unreal.log_warning(f"CW_TERRAIN_TRACE {name} XY=({x},{y}) hits={items}")
    except Exception as exc:
        unreal.log_warning(f"CW_TERRAIN_TRACE {name}: trace unavailable ({exc})")
print("CW_ALIGNMENT_AUDIT_DONE - inspect Output Log for CW_ALIGNMENT_ and CW_TERRAIN_TRACE")

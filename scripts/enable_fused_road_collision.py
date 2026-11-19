"""ChesterWorld 9th/Kerlin: add physics collision to the existing fused road preview.

Run in Unreal Editor 5.7 Python console on L_9thKerlin_FusedPreview:
  py "E:/code/ChesterWorldUnreal/scripts/enable_fused_road_collision.py"

IMPORTANT: This alters the imported StaticMesh ASSET collision settings (shared between
levels) and the preview actor, but does not save the level. Save after testing.
All roads remain flat at provisional Z=+100cm. No terrain or bridge grades.
Complex-as-simple can be appropriate for a static road test mesh, not for physics-
simulated moving road geometry. A proper heightfield / drivable vehicle is separate.
"""
import unreal

LABEL = "CW_FUSED_ROADS_9TH_KERLIN_FLAT_PREVIEW"
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
matches = [a for a in all_actors if a.get_actor_label() == LABEL]
if len(matches) != 1:
    raise RuntimeError(
        "Expected one %s actor in current level; found %d. Open the fused preview level."
        % (LABEL, len(matches))
    )
actor = matches[0]
component = actor.get_component_by_class(unreal.StaticMeshComponent)
if not component:
    raise RuntimeError("Fused road actor has no StaticMeshComponent")
mesh = component.get_editor_property("static_mesh")
if not mesh:
    raise RuntimeError("No static mesh assigned to fused road actor")

trace_flag = getattr(unreal.CollisionTraceFlag, "CTF_USE_COMPLEX_AS_SIMPLE", None)
if trace_flag is None:
    raise RuntimeError("The installed Unreal Python API does not expose complex-as-simple.")

# Favor the official editor subsystem when present; fall back to BodySetup property.
changed = False
subsystem_class = getattr(unreal, "StaticMeshEditorSubsystem", None)
if subsystem_class:
    subsystem = unreal.get_editor_subsystem(subsystem_class)
    method = getattr(subsystem, "set_collision_complexity", None)
    if method:
        method(mesh, trace_flag)
        changed = True

if not changed:
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup is None:
        raise RuntimeError("Could not access StaticMesh BodySetup. Use Static Mesh Editor -> Collision Complexity -> Use Complex Collision As Simple.")
    body_setup.set_editor_property("collision_trace_flag", trace_flag)
    mesh.modify()
    changed = True

component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
component.set_collision_profile_name("BlockAll")
component.set_editor_property("generate_overlap_events", False)
component.modify()
actor.modify()

# Save the modified mesh asset without implicitly saving the level.
asset_path = mesh.get_path_name().split(".")[0]
if not unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False):
    unreal.log_warning("Unable to save road mesh asset automatically; save it in Content Browser.")
unreal.log_warning(
    "CW road collision enabled on static preview mesh. "
    "Test by dropping a physics-enabled object or vehicle onto the surface. "
    "Road Z is UNSURVEYED, intersections unverified; avoid finalizing the world."
)
print("CHESTERWORLD_COLLISION_READY:", asset_path, "level:", actor.get_actor_label())

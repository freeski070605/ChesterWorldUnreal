"""Enable Chaos vehicle road contact on the DRAPED preview road mesh.

Run in an intentionally saved COPY of L_ChesterWorld_9thKerlin_FacadesV1:
  py "E:/code/ChesterWorldUnreal/scripts/enable_draped_road_collision.py"

This modifies the currently assigned StaticMesh ASSET's collision mode (shared
by instances of that asset) and this actor's collision; does NOT reposition
roads or landscape, add a vehicle, or change any vehicle Blueprints.
The terrain visual alignment is provisional; verify wheel contact afterwards.
"""
import unreal

LABEL = "CW_DRAPED_ROADS_PREVIEW"
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
matches = [a for a in sub.get_all_level_actors() if a.get_actor_label() == LABEL]
if len(matches) != 1:
    raise RuntimeError(f"Expected exactly one {LABEL}, found {len(matches)}")
actor = matches[0]
component = actor.get_component_by_class(unreal.StaticMeshComponent)
if not component:
    raise RuntimeError("Road actor lacks StaticMeshComponent")
mesh = component.get_editor_property("static_mesh")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Road actor lacks valid StaticMesh")

flag = unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
editor_class = getattr(unreal, "StaticMeshEditorSubsystem", None)
configured = False
if editor_class:
    subsystem = unreal.get_editor_subsystem(editor_class)
    method = getattr(subsystem, "set_collision_complexity", None)
    if method is not None:
        method(mesh, flag)
        configured = True
if not configured:
    body = mesh.get_editor_property("body_setup")
    if body is None:
        raise RuntimeError(
            "No BodySetup exposed. Open road mesh asset > Details > Collision "
            "> Collision Complexity > Use Complex Collision As Simple."
        )
    body.set_editor_property("collision_trace_flag", flag)
    mesh.modify()

component.set_collision_profile_name("BlockAll")
component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
component.set_editor_property("generate_overlap_events", False)
component.modify()
actor.modify()

asset_path = mesh.get_path_name().split(".")[0]
saved = unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
print("CW_DRAPED_ROAD_COLLISION_ENABLED", asset_path, "asset_saved=", saved)
unreal.log_warning(
    "CW DRAPED ROAD collision configured for static-road vehicle prototype. "
    "Preview grade/datum remain unverified. Save level manually after test."
)

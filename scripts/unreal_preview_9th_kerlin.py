"""UE 5.7 Editor-only preview: create thin centerline markers from local_streets.csv.

Run INSIDE Unreal Editor with Python Editor Script Plugin enabled.
Before running, create and save a NEW empty level: e.g. L_9thKerlin_HorizontalPreview.
This is not terrain, not a finished road surface, and Z=100 cm is arbitrary preview
height only. No map saving is performed by this script.

Change CSV_FILE if the ZIP was unpacked elsewhere.
"""
import csv
import math
from collections import defaultdict
from pathlib import Path

import unreal

CSV_FILE = Path(r"E:\code\ChesterWorldUnreal\pilot\9th_Kerlin\local_streets.csv")
ACTOR_PREFIX = "CW_PREVIEW_"  # Only delete actors using this explicit prefix.
PREVIEW_Z_CM = 100.0  # Arbitrary visual-only plane; NOT a surveyed grade.
PREVIEW_WIDTH_CM = 30.0  # Thin centerline indicators, NOT street widths.
PREVIEW_DEPTH_CM = 10.0

if not CSV_FILE.is_file():
    raise RuntimeError("Missing pilot CSV: " + str(CSV_FILE))

points = defaultdict(list)
with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
    for record in csv.DictReader(handle):
        source_id = int(record["source_index"])
        vertex_id = int(record["vertex"])
        east_cm = float(record["unreal_x_cm"])
        north_cm = float(record["unreal_y_cm"])
        points[source_id].append((vertex_id, east_cm, north_cm, record["road"]))

mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
if not mesh:
    raise RuntimeError("Engine Cube mesh unavailable")

actors = unreal.EditorLevelLibrary.get_all_level_actors()
existing = [a for a in actors if a.get_actor_label().startswith(ACTOR_PREFIX)]
if existing:
    raise RuntimeError(
        "Existing preview actors detected (%d). Remove them manually before rerunning "
        "to avoid unexpected edits." % len(existing)
    )

created = 0
for source_id, entries in sorted(points.items()):
    entries.sort(key=lambda p: p[0])
    for i in range(len(entries) - 1):
        _, x1, y1, name = entries[i]
        _, x2, y2, _ = entries[i + 1]
        dx, dy = x2 - x1, y2 - y1
        length_cm = math.hypot(dx, dy)
        if length_cm < 0.01:
            continue
        center = unreal.Vector((x1 + x2) / 2, (y1 + y2) / 2, PREVIEW_Z_CM)
        yaw = math.degrees(math.atan2(dy, dx))
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, center, unreal.Rotator(0.0, yaw, 0.0)
        )
        if actor is None:
            raise RuntimeError("Could not spawn actor for source %d" % source_id)
        actor.set_actor_label(f"{ACTOR_PREFIX}{name}_{source_id}_{i:02d}")
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        component.set_static_mesh(mesh)
        # Engine Cube is 100 cm per side.
        actor.set_actor_scale3d(unreal.Vector(
            length_cm / 100.0, PREVIEW_WIDTH_CM / 100.0, PREVIEW_DEPTH_CM / 100.0
        ))
        created += 1

unreal.log_warning(
    f"ChesterWorld: spawned {created} preview centerline segments from "
    f"{len(points)} road features. Z={PREVIEW_Z_CM} is NOT surveyed elevation. "
    "Review in a separate preview level, then save manually if desired."
)

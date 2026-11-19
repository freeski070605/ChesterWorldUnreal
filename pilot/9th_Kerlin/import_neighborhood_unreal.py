"""ChesterWorld Unreal 5.7 | neighborhood road-surface PREVIEW.

Run INSIDE Unreal Editor Python Console in a NEW, EMPTY preview level.
Uses only the regional source, 112 selected road features clipped to a 550m square.
No surveyed Z, grading, intersections, sidewalks, or duplicate-near-parallel QA.
The visible strips are rough full-width source estimates; not construction-ready.
"""
import json
import math
from pathlib import Path
import unreal

DATA = Path(r'E:\code\ChesterWorldUnreal\pilot\9th_Kerlin\neighborhood_roads.json')
PREFIX = 'CW_ROAD_PILOT_'
FLAT_Z_CM = 0.0  # NOT real ground height
THICKNESS_CM = 12.0

if not DATA.is_file():
    raise RuntimeError(f'Missing {DATA}. Copy the neighborhood_roads.json there.')
obj = json.loads(DATA.read_text(encoding='utf-8'))
roads = obj['roads']
if not roads or obj['metadata']['projection'] != 'EPSG:32618':
    raise RuntimeError('Unexpected geometry data or coordinate system')

existing = [a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()
            if a.get_actor_label().startswith(PREFIX)]
if existing:
    raise RuntimeError(f'{len(existing)} existing {PREFIX} actors. Use new empty level or remove those manually before retrying.')

cube = unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
if not cube:
    raise RuntimeError('Unreal Engine default Cube mesh missing')

count = 0
for road in roads:
    pts = road['points_cm']
    width = float(road['width_cm'])
    if not (200 <= width <= 3000):
        raise RuntimeError(f'Unexpected road width for {road["id"]}: {width}')
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        length = math.hypot(dx, dy)
        if length <= 1.0:
            continue
        yaw = math.degrees(math.atan2(dy, dx))
        location = unreal.Vector((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, FLAT_Z_CM)
        rotation = unreal.Rotator(0.0, yaw, 0.0)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
        if actor is None:
            raise RuntimeError(f'Failed spawning {road["id"]} segment {i}')
        actor.set_actor_label(f'{PREFIX}{road["name"]}_{road["source_index"]}_{i:02d}')
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        component.set_static_mesh(cube)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        actor.set_actor_scale3d(unreal.Vector(length / 100.0, width / 100.0, THICKNESS_CM / 100.0))
        count += 1

unreal.log_warning(f'ChesterWorld: spawned {count} flat ROAD PILOT strips from {len(roads)} road features. '
                   'All heights are placeholders. Existing world NOT saved automatically.')

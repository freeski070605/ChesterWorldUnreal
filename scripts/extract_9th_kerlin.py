#!/usr/bin/env python3
"""Extract *candidate* road geometry near the prior 9th/Kerlin service-road cluster.

Read-only source processing. Results are diagnostic GeoJSON in EPSG:4326,
NOT ready-made Unreal meshes or verified ground elevations.
"""
import json
import math
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

BASE = Path(r"E:\ChesterWorld\Data")
OUT = Path(r"E:\ChesterWorld\Reports")
SOURCES = [
    BASE / "18_StreetSystemV3" / "regional_motor_roads_v3.geojson",
    BASE / "02_Roads" / "delco_roads.geojson",
]
# Coordinates observed in previous audit's unnamed service roads.
# Approximate search seed only: NOT independently verified as 9th & Kerlin.
ANCHOR_LON, ANCHOR_LAT = -75.3720, 39.8481
RADIUS_METERS = 450
NAME_TERMS = ("9th", "kerlin", "concord")

def vertices(geometry):
    if not geometry:
        return []
    kind = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if kind == "LineString":
        return coords
    if kind == "MultiLineString":
        return [p for segment in coords for p in segment]
    return []

def distance_m(p):
    """Local equirectangular distance for filtering only, not projection."""
    dx = (p[0] - ANCHOR_LON) * 111320 * math.cos(math.radians(ANCHOR_LAT))
    dy = (p[1] - ANCHOR_LAT) * 111320
    return math.hypot(dx, dy)

def road_name(properties):
    for key in ("generator_name", "name", "NAME", "street_name", "STREET_NAME", "road_name", "ROAD_NAME", "FULLNAME", "FULL_NAME"):
        val = properties.get(key)
        if val:
            return str(val)
    return ""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "CANDIDATE_ONLY_NOT_IMPORT_READY",
        "anchor_lon_lat": [ANCHOR_LON, ANCHOR_LAT],
        "anchor_status": "inferred from prior service-road features, NOT separately verified as 9th/Kerlin",
        "radius_m": RADIUS_METERS,
        "source_summaries": [],
        "matches": [],
        "notes": [
            "No elevation information or vertical datum verified.",
            "Check real 9th/Kerlin intersection against a trusted georeferenced source before adopting an Unreal origin.",
            "Two source datasets may contain duplicate roads; do not merge or render both without de-duplication.",
            "Output remains EPSG:4326 in lon/lat degrees; do not use degrees as Unreal centimeters."
        ]
    }
    extracted = []
    for path in SOURCES:
        if not path.is_file():
            report["source_summaries"].append({"path": str(path), "status": "missing"})
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
            crs = (obj.get("crs") or {}).get("properties", {}).get("name")
            summary = {"path": str(path), "feature_count": len(obj.get("features", [])), "declared_crs": crs, "nearby": 0, "named_nearby": 0}
            if crs != "EPSG:4326":
                summary["status"] = "SKIPPED_UNEXPECTED_CRS"
                report["source_summaries"].append(summary)
                continue
            for index, feature in enumerate(obj.get("features", [])):
                verts = vertices(feature.get("geometry"))
                if not verts:
                    continue
                try:
                    min_dist = min(distance_m(p) for p in verts)
                except (TypeError, ValueError, IndexError):
                    continue
                if min_dist > RADIUS_METERS:
                    continue
                props = feature.get("properties") or {}
                name = road_name(props)
                is_target_name = any(term in name.lower() for term in NAME_TERMS)
                summary["nearby"] += 1
                summary["named_nearby"] += int(is_target_name)
                item_props = {
                    **props,
                    "_source_path": str(path),
                    "_source_index": index,
                    "_distance_to_seed_m": round(min_dist, 1),
                    "_candidate_target_name": is_target_name,
                }
                extracted.append({"type": "Feature", "geometry": feature["geometry"], "properties": item_props})
                report["matches"].append({"source": path.name, "index": index, "name": name, "distance_m": round(min_dist, 1), "target_name": is_target_name})
            report["source_summaries"].append(summary)
        except Exception as exc:
            report["source_summaries"].append({"path": str(path), "status": "error", "message": str(exc)})
    report_path = OUT / "9th_Kerlin_geometry_report_v2.json"
    geo_path = OUT / "9th_Kerlin_candidates_v2.geojson"
    zip_path = OUT / "9th_Kerlin_Geometry_Audit_v2.zip"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    geo_path.write_text(json.dumps({"type":"FeatureCollection", "name":"9th_Kerlin_candidates_v2", "crs":{"type":"name","properties":{"name":"EPSG:4326"}}, "features": extracted}, indent=2), encoding="utf-8")
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(report_path, report_path.name)
        archive.write(geo_path, geo_path.name)
    print("Road candidates:", len(extracted))
    for summary in report["source_summaries"]:
        print(summary)
    print("Created:", zip_path)
    print("WARNING: Seed point and elevation are unverified. Do not import to Unreal yet.")

if __name__ == "__main__":
    main()

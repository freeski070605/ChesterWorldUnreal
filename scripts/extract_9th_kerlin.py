#!/usr/bin/env python3
"""Read-only extraction of audited 9th/Kerlin road records from candidate source GeoJSON.

Usage:
  py -3 scripts/extract_9th_kerlin.py

WARNING: audit feature_index may refer to an upstream merged feature collection.
We test names and do not assert these are correct if source indexes differ.
No CRS conversion and no Unreal geometry conversion is performed.
"""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

BASE = Path(r"E:\ChesterWorld\Data")
OUT = Path(r"E:\ChesterWorld\Reports")
SOURCES = [
    BASE / "18_StreetSystemV3" / "regional_motor_roads_v3.geojson",
    BASE / "02_Roads" / "delco_roads.geojson",
]
# display ID: expected road name and audited feature index
RECORDS = [
    (1, 4166, "9th"), (2, 3447, "9th"), (3, 100, "Kerlin"),
    (4, 659, "Kerlin"), (5, 2152, "Concord"), (6, 3448, "9th"),
    (7, 2151, "Concord"), (8, 2437, "Concord"), (9, 539, "Kerlin"),
    (10, 4878, ""), (11, 4877, ""), (12, 4876, ""), (13, 5197, ""),
]

def get_name(feature):
    props = feature.get("properties") or {}
    for key in ("name", "NAME", "street_name", "STREET_NAME", "road_name", "ROAD_NAME", "FULLNAME", "FULL_NAME"):
        if props.get(key) is not None:
            return str(props[key])
    return ""

def run():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"warning": "Source feature_index compatibility is UNVERIFIED. Inspect coordinates, CRS and source properties before any Unreal import.", "source_candidates": [], "records": []}
    output = []
    for path in SOURCES:
        if not path.is_file():
            report["source_candidates"].append({"path": str(path), "status": "not_found"})
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
            feats = obj.get("features", [])
            crs = obj.get("crs")
            report["source_candidates"].append({"path": str(path), "status": "read", "feature_count": len(feats), "crs": crs, "bbox": obj.get("bbox")})
            for display_id, index, expected in RECORDS:
                if index >= len(feats):
                    report["records"].append({"source": str(path), "display_id": display_id, "index": index, "status": "index_out_of_range"})
                    continue
                feat = feats[index]
                name = get_name(feat)
                name_ok = (expected.lower() in name.lower()) if expected else True
                geometry = feat.get("geometry") or {}
                status = "candidate_name_match" if name_ok else "NAME_MISMATCH_VERIFY_INDEX"
                report["records"].append({"source": str(path), "display_id": display_id, "index": index, "expected": expected, "actual": name, "geometry_type": geometry.get("type"), "status": status})
                if name_ok and geometry.get("type") in ("LineString", "MultiLineString"):
                    output.append({
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": {**(feat.get("properties") or {}), "_audit_display_id": display_id, "_audit_feature_index": index, "_source_file": str(path)}
                    })
        except Exception as exc:
            report["source_candidates"].append({"path": str(path), "status": "ERROR", "detail": str(exc)})
    report_file = OUT / "9th_Kerlin_geometry_report.json"
    geo_file = OUT / "9th_Kerlin_candidates.geojson"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Source collections may have different CRS. Output is diagnostic ONLY, never import mixed coordinates.
    geo_file.write_text(json.dumps({"type": "FeatureCollection", "features": output}, indent=2), encoding="utf-8")
    zip_file = OUT / "9th_Kerlin_Geometry_Audit.zip"
    with ZipFile(zip_file, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(report_file, arcname=report_file.name)
        archive.write(geo_file, arcname=geo_file.name)
    print("Candidate features:", len(output))
    print("NOTE: candidate coordinates may have mixed CRS; do not import yet.")
    print("Created:", zip_file)

if __name__ == "__main__":
    run()

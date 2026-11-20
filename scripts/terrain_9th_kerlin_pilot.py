#!/usr/bin/env python3
"""ChesterWorld Unreal: inspect DEM candidates and extract an elevation pilot.

Reads Chester GIS source rasters. Writes a report and 513x513 normalized 16-bit
heightmap preview, with explicit scale metadata. It DOES NOT import to Unreal,
modify source GIS, or assert the vertical datum is correct.

Dependencies: pip install rasterio pyproj numpy pillow
Usage: py -3 scripts/terrain_9th_kerlin_pilot.py
"""
import json
import math
from pathlib import Path

try:
    import numpy as np
    import rasterio
    from rasterio.vrt import WarpedVRT
    from rasterio.enums import Resampling
    from rasterio.windows import from_bounds
    from pyproj import Transformer, CRS
    from PIL import Image
except ImportError as exc:
    raise SystemExit(
        f"Missing Python dependency: {exc}. Install via "
        "'py -3 -m pip install rasterio pyproj numpy pillow'."
    )

DATA = Path(r"E:\ChesterWorld\Data\09_RegionalTerrain")
OUT = Path(r"E:\ChesterWorld\Reports\UnrealTerrainPilot")
# Exact road intersection point from the source geometry (not a vertical survey).
LON, LAT = -75.37141354422802, 39.84831809369421
SIDE_METERS = 512
OUTPUT_SAMPLES = 513
NODATA_LIMIT = 0.005

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    anchor_e, anchor_n = Transformer.from_crs(4326, 32618, always_xy=True).transform(LON, LAT)
    half = SIDE_METERS / 2
    bounds = (anchor_e - half, anchor_n - half, anchor_e + half, anchor_n + half)
    report = {
        "status": "diagnostic_only_no_verified_vertical_datum",
        "origin_lon_lat": [LON, LAT],
        "origin_utm18n_m": [anchor_e, anchor_n],
        "extent_utm18n_m": list(bounds),
        "horizontal_crs": "EPSG:32618",
        "unreal_note": "1m = 100cm; landscape raw heightmap needs explicit Z scale and a verified vertical datum",
        "candidates": [],
        "chosen": None,
    }
    viable = []
    files = list(DATA.glob("chester_dem_*.tif")) + list(DATA.glob("regional_dem_*.tif"))
    for path in files:
        try:
            with rasterio.open(path) as ds:
                if ds.crs is None:
                    report["candidates"].append({"path":str(path),"status":"missing_crs"})
                    continue
                x, y = Transformer.from_crs(4326, ds.crs, always_xy=True).transform(LON, LAT)
                covered = ds.bounds.left <= x <= ds.bounds.right and ds.bounds.bottom <= y <= ds.bounds.top
                info = {
                    "path": str(path), "crs": ds.crs.to_string(),
                    "bounds": [ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top],
                    "dtype": ds.dtypes[0], "nodata": ds.nodata,
                    "resolution_native": list(ds.res), "covers_origin": covered,
                    "units": ds.units[0] if ds.units else None,
                    "vertical_datum": "UNVERIFIED",
                }
                report["candidates"].append(info)
                if covered:
                    # Prefer highest resolution in meters as determined by a reprojection estimate.
                    viable.append((path, abs(ds.res[0] * ds.res[1])))
        except Exception as exc:
            report["candidates"].append({"path":str(path),"status":"error","error":str(exc)})
    report_file = OUT / "terrain_9th_kerlin_report.json"
    if not viable:
        report["error"] = "No candidate source raster contains the GIS origin. Check source location and CRS."
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise SystemExit(f"No suitable DEM found; see {report_file}")
    # Selecting by native pixel footprint is only reliable when candidates share comparable CRS/units.
    # Prefer a Chester source tile over regional-generated tiles when both cover point, but document it.
    viable.sort(key=lambda item: (0 if item[0].name.startswith("chester_dem_") else 1, item[1]))
    path = viable[0][0]
    report["chosen"] = str(path)
    from rasterio.transform import from_bounds as bounds_transform
    dst_transform = bounds_transform(*bounds, OUTPUT_SAMPLES, OUTPUT_SAMPLES)
    with rasterio.open(path) as ds:
        with WarpedVRT(
            ds, crs="EPSG:32618", transform=dst_transform,
            width=OUTPUT_SAMPLES, height=OUTPUT_SAMPLES,
            resampling=Resampling.bilinear
        ) as vrt:
            data = vrt.read(1, masked=True).astype(np.float64)
    valid = np.isfinite(data.filled(np.nan)) & ~np.ma.getmaskarray(data)
    missing = 1 - float(valid.sum()) / valid.size
    report["nodata_fraction"] = round(missing, 6)
    if missing > NODATA_LIMIT:
        report["error"] = "DEM tile does not cover enough of 512m extent; mosaic required before heightmap."
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise SystemExit(f"Insufficient coverage ({missing:.1%}); see {report_file}")
    values = data.filled(np.nan)
    # Use an explicitly recorded conversion; keep 16-bit preview, not engine-calibrated heightmap.
    low = float(np.nanmin(values))
    high = float(np.nanmax(values))
    span = high - low
    if span <= 0:
        report["error"] = "DEM values have no range; invalid terrain."
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise SystemExit("No valid elevation range")
    normalized = np.clip((values - low) / span, 0, 1)
    height_u16 = np.round(normalized * 65535).astype(np.uint16)
    png = OUT / "9th_Kerlin_513x513_ELEVATION_PREVIEW_NOT_ENGINE_SCALED.png"
    Image.fromarray(height_u16, mode="I;16").save(png)
    report.update({
        "preview_png":str(png),
        "elevation_min_raw":low,
        "elevation_max_raw":high,
        "elevation_units":"AS_REPORTED_BY_SOURCE_NOT_VERIFIED",
        "heightmap_encoding":"uint16 = round((z-min)/(max-min)*65535)",
        "pixel_spacing_m":SIDE_METERS / (OUTPUT_SAMPLES - 1),
        "unreal_xy_scale_cm_per_vertex":100.0,
        "vertical_datum":"UNVERIFIED",
        "requires_review_before_import":[
            "Verify DEM elevation units and vertical datum against original metadata.",
            "Check raster alignment and whether chosen tile fully covers 512m square.",
            "Check road/terrain offsets and road crossing grade separation.",
            "Compute correct Unreal landscape Z scale before treating as true elevation."
        ]
    })
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Pilot heightmap preview:",png)
    print("Report:",report_file)
    print("Height min/max (RAW source units):",low,high)
    print("WARNING: NOT ready for elevation-accurate engine import until metadata verified.")

if __name__ == "__main__":
    main()

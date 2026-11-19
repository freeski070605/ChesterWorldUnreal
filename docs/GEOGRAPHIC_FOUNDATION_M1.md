# ChesterWorld Unreal — Geographic Foundation (Milestone 1)

Status: **planning / local editor setup required**. The GitHub repository has no `.uproject` as of 2026-11-18. Do not treat this document as evidence that a scene has been built.

## Goal
Build a geographically faithful, traversable proof-of-concept around **W 9th Street & Kerlin Street, Chester, PA**, using Unreal Engine 5.7, then scale the geographic foundation to all of Chester with World Partition.

## Source-of-truth rules
1. Use the original licensed/usable GIS data (elevation, street centerlines, orthophotos, building footprints) as geographic inputs. Do **not** treat Roblox-generated geometry as accurate source GIS.
2. Keep provenance, coordinate reference system (CRS), units, resolution, source date, and license beside each input. Never silently guess these values.
3. Preserve neighborhood layout, carriageways, bridge heights, ramps, water shorelines, and road connectivity. Flag uncertain geometry instead of inventing details.
4. Use local E: storage for bulky inputs and Unreal caches; do not commit proprietary imagery or purchased assets to this public repository.
5. Build a small playable area first, without abandoning the full-city goal.

## Immediate local steps (Windows)
1. Open **Epic Games Launcher > Unreal Engine > Library** and confirm Unreal Engine 5.7 is installed.
2. Open Unreal Engine, choose **Games > Third Person**, Blueprint (unless a C++ toolchain is already installed), desktop, starter content optional.
3. Create project named `ChesterWorldUnreal` at `E:\code\ChesterWorldUnreal` **only if Unreal allows using the existing repo directory safely**. Otherwise create it at `E:\UnrealProjects\ChesterWorldUnreal` and copy the Unreal project files into the cloned repo after inspecting for conflicts.
4. Launch the blank project and verify the default Third Person player can move. Save and close Unreal.
5. Inspect `git status` before staging; verify that `Saved/`, `Intermediate/`, `DerivedDataCache/`, `Binaries/`, and raw GIS datasets remain untracked.
6. Commit the initial `.uproject`, Config, Content, and project settings after validation. Do not commit generated caches.

## GIS audit before any coordinate conversion
Candidate legacy source location: `E:\ChesterWorld\Data\` (verify actual paths on the user's machine).
Create a source inventory table with:
- relative file path, data type, size, source/provenance, rights/license
- CRS/EPSG, native units and spatial extent
- elevation datum and vertical units (terrain)
- road geometry and grade separation metadata
- building footprint attributes and uniqueness
- imagery resolution, date and license

Stop importing until units and CRS are verified. Unreal uses centimeters; georeferenced coordinates must be transformed into an appropriate local frame and origin, not fed in unmodified as longitude/latitude.

## Acceptance checks: playable pilot
- Third Person project loads and character movement works in Editor.
- World Partition enabled for the geographic persistent world (and validated in editor).
- Verified terrain patch and road positions around 9th & Kerlin align with input GIS.
- A marked spawn is at the verified geographic intersection.
- A short road-driving test is possible with a vehicle when vehicle controls are added.
- No obvious floating roads, grass through roads, impossible slopes or incorrect bridge clearance in pilot.
- Document frame rate and RAM/VRAM usage on the Alienware RTX 3070 laptop.
- Check scene and assets are properly sourced before sharing.

## Later full-city passes
1. Citywide terrain and streets with streaming, water/shoreline and elevated roads
2. Building footprint shells and neighborhood block validation
3. Materials, details, storefronts and landmark modeling
4. Vehicles, pedestrians, traffic, interiors, economy and missions
5. Multiplayer after single-player scale/performance baseline is stable

## First report back
Record: Unreal project path, `.uproject` filename, whether project opens, screenshots of 9th & Kerlin once scene exists, GIS inventory, and current frame rate. Distinguish verified work from estimates.

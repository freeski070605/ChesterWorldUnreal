# ChesterWorldUnreal

Unreal Engine 5 development workspace for a geographically grounded, realistic recreation of Chester, Pennsylvania.

## Local workspace (Windows)

**Use the external E: drive, not C:**

```powershell
New-Item -ItemType Directory -Force E:\code | Out-Null
Set-Location E:\code
git clone https://github.com/freeski070605/ChesterWorldUnreal.git
Set-Location .\ChesterWorldUnreal
```

This repository is separate from the ChesterWorld Roblox game. Do not copy Roblox-generated tiles as the canonical geographic source. Reuse the GIS, elevation, road, parcel, building, and imagery source datasets wherever licensing and formats permit.

## Planned architecture

- Unreal Engine 5 project (created locally using Unreal Editor)
- World Partition and streaming
- Georeferenced terrain and GIS-derived streets
- Modular building and interior assets
- Gameplay systems in C++ and Blueprints
- Data validation and performance budgets

## Important

No Unreal .uproject has been created yet. Do not assume this is a runnable Unreal game. Keep large raw data, DerivedDataCache, Intermediate, Saved, and generated builds out of Git. Use Git LFS for approved large binary assets.

The repository is currently public; do not commit private files, paid assets, or restricted source imagery.

# ChesterWorld Unreal read-only local inventory
# Run from PowerShell. Produces a CSV report only; does not copy/import/delete data.
param(
  [string]$ProjectRoot = 'E:\UnrealProjects\ChesterWorldUnreal',
  [string]$LegacyDataRoot = 'E:\ChesterWorld\Data',
  [string]$OutputDirectory = "$env:USERPROFILE\Desktop"
)
$ErrorActionPreference = 'Stop'
$roots = @(
  @{ Kind = 'UnrealProject'; Path = $ProjectRoot },
  @{ Kind = 'LegacyGIS'; Path = $LegacyDataRoot }
)
$extensions = @('.uproject','.umap','.uasset','.tif','.tiff','.geotiff','.dem','.las','.laz','.asc','.png','.jpg','.jpeg','.gpkg','.shp','.shx','.dbf','.prj','.geojson','.json','.osm','.pbf','.csv','.fbx','.obj','.glb','.gltf','.xml','.vrt')
$rows = [System.Collections.Generic.List[object]]::new()
foreach ($root in $roots) {
  if (-not (Test-Path -LiteralPath $root.Path -PathType Container)) {
    Write-Warning "Missing root: $($root.Path)"
    continue
  }
  Write-Host "Scanning $($root.Kind): $($root.Path)"
  Get-ChildItem -LiteralPath $root.Path -File -Recurse -ErrorAction SilentlyContinue |
    Where-Object {
      $extensions -contains $_.Extension.ToLowerInvariant() -and
      $_.FullName -notmatch '\\(DerivedDataCache|Intermediate|Saved|Binaries|\.git)\\'
    } |
    ForEach-Object {
      $rows.Add([pscustomobject]@{
        category = $root.Kind
        full_path = $_.FullName
        extension = $_.Extension.ToLowerInvariant()
        size_mb = [math]::Round($_.Length / 1MB, 2)
        modified = $_.LastWriteTime.ToString('s')
      })
    }
}
if (-not (Test-Path -LiteralPath $OutputDirectory)) {
  throw "Output directory missing: $OutputDirectory"
}
$csv = Join-Path $OutputDirectory 'ChesterWorldUnreal_inventory.csv'
$rows | Export-Csv -LiteralPath $csv -NoTypeInformation -Encoding utf8
$uprojects = @($rows | Where-Object { $_.extension -eq '.uproject' })
Write-Host "Saved $($rows.Count) file records to: $csv"
Write-Host "Unreal project files found: $($uprojects.Count)"
$uprojects | ForEach-Object { Write-Host " - $($_.full_path)" }
Write-Host "NOTICE: CRS, licensing, and elevation datum are not detected by filename inventory; these must be verified before import."

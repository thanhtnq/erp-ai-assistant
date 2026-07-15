param(
  [string]$Source = "",
  [string]$Target = "D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin",
  [switch]$Watch
)

$ErrorActionPreference = "Stop"

if (-not $Source) {
  $Source = Join-Path $PSScriptRoot "..\cfml-examples"
}

$Source = (Resolve-Path -LiteralPath $Source).Path

if (-not (Test-Path -LiteralPath $Target)) {
  New-Item -ItemType Directory -Path $Target | Out-Null
}

$Target = (Resolve-Path -LiteralPath $Target).Path
$allowedExtensions = @(".cfm", ".css", ".html", ".png", ".jpg", ".jpeg", ".gif", ".svg")
$excludedFiles = @(
  "inc_wgp_tnorightbot_09_panel.cfm",
  "inc_wgp_tnorightbot_11_panel.cfm"
)

function Test-SyncableFile {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
  $name = [IO.Path]::GetFileName($Path)
  if ($excludedFiles -contains $name) { return $false }
  $ext = [IO.Path]::GetExtension($Path).ToLowerInvariant()
  return $allowedExtensions -contains $ext
}

function Copy-CfmlFile {
  param([string]$Path)

  if (-not (Test-SyncableFile $Path)) { return }

  $sourceRoot = $Source.TrimEnd("\", "/") + "\"
  if (-not $Path.StartsWith($sourceRoot, [StringComparison]::OrdinalIgnoreCase)) { return }
  $relative = $Path.Substring($sourceRoot.Length)

  $destination = Join-Path $Target $relative
  $destinationDir = Split-Path -Parent $destination
  if (-not (Test-Path -LiteralPath $destinationDir)) {
    New-Item -ItemType Directory -Path $destinationDir | Out-Null
  }

  Copy-Item -LiteralPath $Path -Destination $destination -Force
  Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $relative)
}

function Sync-All {
  Write-Host "Syncing CFML examples..."
  Write-Host "  From: $Source"
  Write-Host "  To:   $Target"

  Get-ChildItem -LiteralPath $Source -Recurse -File |
    Where-Object { Test-SyncableFile $_.FullName } |
    ForEach-Object { Copy-CfmlFile $_.FullName }
}

Sync-All

if (-not $Watch) {
  exit 0
}

Write-Host ""
Write-Host "Watching for changes. Press Ctrl+C to stop."

$watcher = New-Object IO.FileSystemWatcher
$watcher.Path = $Source
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$pending = @{}

Register-ObjectEvent $watcher Changed -SourceIdentifier CfmlChanged | Out-Null
Register-ObjectEvent $watcher Created -SourceIdentifier CfmlCreated | Out-Null
Register-ObjectEvent $watcher Renamed -SourceIdentifier CfmlRenamed | Out-Null

try {
  while ($true) {
    $event = Wait-Event -Timeout 1
    if ($event) {
      $path = if ($event.SourceEventArgs.FullPath) {
        $event.SourceEventArgs.FullPath
      } else {
        $event.SourceEventArgs.NewFullPath
      }

      if ($path) {
        $pending[$path] = Get-Date
      }

      Remove-Event -EventIdentifier $event.EventIdentifier
    }

    $now = Get-Date
    foreach ($item in @($pending.Keys)) {
      if (($now - $pending[$item]).TotalMilliseconds -ge 350) {
        Copy-CfmlFile $item
        $pending.Remove($item)
      }
    }
  }
}
finally {
  Unregister-Event -SourceIdentifier CfmlChanged -ErrorAction SilentlyContinue
  Unregister-Event -SourceIdentifier CfmlCreated -ErrorAction SilentlyContinue
  Unregister-Event -SourceIdentifier CfmlRenamed -ErrorAction SilentlyContinue
  $watcher.Dispose()
}

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z]:[\\/]?$')]
    [string]$Drive,

    [string]$MediaSource = (Join-Path $PSScriptRoot '..\..\SD-Card-Media-260805.zip'),

    [switch]$AllowFixedDrive,
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'

$driveLetter = $Drive.Substring(0, 1).ToUpperInvariant()
$root = "$driveLetter`:\"
$systemDrive = [IO.Path]::GetPathRoot($env:SystemRoot)
if ($root.Equals($systemDrive, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to prepare the Windows system drive: $root"
}

$volume = Get-Volume -DriveLetter $driveLetter -ErrorAction Stop
if ($volume.DriveType -ne 'Removable' -and -not $AllowFixedDrive) {
    throw "Drive $root reports type '$($volume.DriveType)'. Use -AllowFixedDrive only after verifying it is the SD card."
}
$fileSystem = [string]$volume.FileSystem
if ($fileSystem -notin @('FAT', 'FAT32')) {
    throw "Drive $root uses '$fileSystem'; the firmware requires FAT/FAT32. This script will not format the card."
}
if (-not (Test-Path -LiteralPath $root -PathType Container)) {
    throw "Drive is not accessible: $root"
}

$directories = @(
    'music',
    'photos',
    'video',
    'Waveshare\Recordings',
    'Waveshare\AIChats',
    'Waveshare\Diagnostics'
)
foreach ($relative in $directories) {
    $destination = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $destination.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Resolved directory escapes the SD root: $destination"
    }
    if ($PSCmdlet.ShouldProcess($destination, 'Create SD test directory')) {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
    }
}

$copied = 0
$skipped = 0

function Copy-MediaFile(
    [string]$Relative,
    [object]$SourceObject,
    [scriptblock]$CopyAction
)
{
    $relative = $Relative.TrimStart('\', '/')
    $destination = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $destination.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Resolved file escapes the SD root: $destination"
    }
    $parent = Split-Path -Parent $destination
    if ($PSCmdlet.ShouldProcess($parent, 'Create media directory')) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    if ((Test-Path -LiteralPath $destination) -and -not $Overwrite) {
        Write-Verbose "Keeping existing file: $destination"
        $script:skipped++
        return
    }
    if ($PSCmdlet.ShouldProcess($destination, "Copy SD media from $MediaSource")) {
        & $CopyAction $destination $SourceObject
        $script:copied++
    }
}

$resolvedMediaSource = (Resolve-Path -LiteralPath $MediaSource -ErrorAction Stop).Path
if (Test-Path -LiteralPath $resolvedMediaSource -PathType Container) {
    $sourceRoot = $resolvedMediaSource.TrimEnd('\', '/')
    Get-ChildItem -LiteralPath $sourceRoot -Recurse -File | ForEach-Object {
        $sourceFile = $_.FullName
        $relative = $sourceFile.Substring($sourceRoot.Length).TrimStart('\', '/')
        Copy-MediaFile $relative $sourceFile {
            param($destination, $source)
            Copy-Item -LiteralPath $source -Destination $destination -Force:$Overwrite
        }
    }
}
elseif ([IO.Path]::GetExtension($resolvedMediaSource).Equals(
        '.zip', [StringComparison]::OrdinalIgnoreCase
    )) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($resolvedMediaSource)
    try {
        foreach ($entry in $archive.Entries) {
            if ([string]::IsNullOrEmpty($entry.Name)) {
                continue
            }
            $relative = $entry.FullName.Replace('/', '\')
            Copy-MediaFile $relative $entry {
                param($destination, $archiveEntry)
                [IO.Compression.ZipFileExtensions]::ExtractToFile(
                    $archiveEntry, $destination, [bool]$Overwrite
                )
            }
        }
    }
    finally {
        $archive.Dispose()
    }
}
else {
    throw "MediaSource must be a directory or ZIP archive: $resolvedMediaSource"
}

if ($WhatIfPreference) {
    Write-Host "Dry run completed for $root; no files were changed."
}
else {
    Write-Host "SD card prepared at $root"
}
Write-Host "Volume: $($volume.FileSystemLabel)  $($volume.FileSystem)  $([math]::Round($volume.Size / 1GB, 2)) GiB"
Write-Host "Copied: $copied file(s); kept existing: $skipped file(s)"
Write-Host 'Eject the card through Windows before removing it from the reader.'

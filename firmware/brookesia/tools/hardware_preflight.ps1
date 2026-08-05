[CmdletBinding()]
param(
    [ValidatePattern('^COM[0-9]+$')]
    [string]$Port,

    [string]$SdDrive,
    [switch]$AllowFixedDrive,
    [switch]$Offline,

    [string]$FirmwarePath,
    [string]$MediaZipPath,

    [ValidatePattern('^[0-9A-Fa-f]{64}$')]
    [string]$ExpectedFirmwareSha256 =
        '2b7e01ff1f37027385a3820e006f945464cfcee2a05954b3239cf75f250080b6',

    [ValidatePattern('^[0-9A-Fa-f]{64}$')]
    [string]$ExpectedMediaZipSha256 =
        'ab92e1974f395091c62ac58f71cc8185e43f5db2ed89d96940bed735d0884f74'
)

$ErrorActionPreference = 'Stop'
$script:preflightFailures = [Collections.Generic.List[string]]::new()

function Write-Pass([string]$Message)
{
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-WarningResult([string]$Message)
{
    Write-Host "[SKIP] $Message" -ForegroundColor Yellow
}

function Write-Failure([string]$Message)
{
    $script:preflightFailures.Add($Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Get-Sha256([string]$Path)
{
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-EmbeddedHostPathCount([string]$Path)
{
    $bytes = [IO.File]::ReadAllBytes($Path)
    $printableRuns = [Text.RegularExpressions.Regex]::Matches(
        [Text.Encoding]::ASCII.GetString($bytes),
        '[\x20-\x7e]{8,}'
    )
    $count = 0
    foreach ($run in $printableRuns) {
        if ($run.Value -match '^(?:[A-Za-z]:[\\/]|/(?:home|Users|private|Volumes)/)') {
            $count++
        }
    }
    return $count
}

function Resolve-ExistingFile([string]$Path, [string]$Description)
{
    if ([string]::IsNullOrWhiteSpace($Path) -or
            -not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Description was not found: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Resolve-SafeChild([string]$Root, [string]$RelativePath)
{
    # Keep the trailing separator while joining. Trimming a Windows drive root
    # would turn it into a drive-relative current directory instead of the
    # physical card root.
    $rootFull = [IO.Path]::GetFullPath($Root)
    $candidate = [IO.Path]::GetFullPath((Join-Path $rootFull $RelativePath))
    $prefix = $rootFull.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes its expected root: $RelativePath"
    }
    return $candidate
}

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
if ([string]::IsNullOrWhiteSpace($FirmwarePath)) {
    $FirmwarePath = Join-Path $repoRoot (
        'firmware\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin'
    )
}
if ([string]::IsNullOrWhiteSpace($MediaZipPath)) {
    $MediaZipPath = Join-Path $repoRoot 'firmware\SD-Card-Media-260805.zip'
}

$resolvedFirmware = $null
$resolvedMediaZip = $null
$mediaManifest = $null
$mediaManifestSha = $null

try {
    $resolvedFirmware = Resolve-ExistingFile $FirmwarePath 'Combined firmware'
    $firmwareItem = Get-Item -LiteralPath $resolvedFirmware
    if ($firmwareItem.Length -ne 16MB) {
        Write-Failure "Combined firmware is $($firmwareItem.Length) bytes; expected 16777216"
    } else {
        Write-Pass 'Combined firmware size is exactly 16 MiB'
    }
    $firmwareSha = Get-Sha256 $resolvedFirmware
    if ($firmwareSha -ne $ExpectedFirmwareSha256.ToLowerInvariant()) {
        Write-Failure "Combined firmware SHA256 is $firmwareSha"
    } else {
        Write-Pass "Combined firmware SHA256 $firmwareSha"
    }
    $embeddedHostPathCount = Get-EmbeddedHostPathCount $resolvedFirmware
    if ($embeddedHostPathCount -ne 0) {
        Write-Failure (
            "Combined firmware contains $embeddedHostPathCount embedded host-absolute path string(s)"
        )
    } else {
        Write-Pass 'Combined firmware contains no embedded host-absolute paths'
    }
} catch {
    Write-Failure $_.Exception.Message
}

try {
    $resolvedMediaZip = Resolve-ExistingFile $MediaZipPath 'SD media ZIP'
    $mediaZipSha = Get-Sha256 $resolvedMediaZip
    if ($mediaZipSha -ne $ExpectedMediaZipSha256.ToLowerInvariant()) {
        Write-Failure "SD media ZIP SHA256 is $mediaZipSha"
    } else {
        Write-Pass "SD media ZIP SHA256 $mediaZipSha"
    }
} catch {
    Write-Failure $_.Exception.Message
}

try {
    if ($null -eq $resolvedMediaZip) {
        throw 'The SD media ZIP was unavailable'
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($resolvedMediaZip)
    try {
        $entries = @{}
        foreach ($zipEntry in $archive.Entries) {
            if ([string]::IsNullOrEmpty($zipEntry.Name)) {
                continue
            }
            $entryName = $zipEntry.FullName.Replace('\', '/')
            # Resolve against a synthetic root to reject absolute paths and ..
            # components before trusting an archive entry name.
            $syntheticRoot = Join-Path ([IO.Path]::GetPathRoot($repoRoot)) 'sd-media-root'
            $null = Resolve-SafeChild $syntheticRoot $entryName
            if ($entries.ContainsKey($entryName)) {
                throw "Duplicate SD media ZIP entry: $entryName"
            }
            $entries[$entryName] = $zipEntry
        }

        $manifestEntry = $entries['media_manifest.json']
        if ($null -eq $manifestEntry) {
            throw 'SD media ZIP is missing media_manifest.json'
        }
        $manifestStream = $manifestEntry.Open()
        $manifestMemory = [IO.MemoryStream]::new()
        try {
            $manifestStream.CopyTo($manifestMemory)
            $manifestBytes = $manifestMemory.ToArray()
        }
        finally {
            $manifestMemory.Dispose()
            $manifestStream.Dispose()
        }
        $manifestHasher = [Security.Cryptography.SHA256]::Create()
        try {
            $mediaManifestSha = ([BitConverter]::ToString(
                $manifestHasher.ComputeHash($manifestBytes)
            )).Replace('-', '').ToLowerInvariant()
        }
        finally {
            $manifestHasher.Dispose()
        }
        $mediaManifest = [Text.Encoding]::UTF8.GetString($manifestBytes) | ConvertFrom-Json

        $verifiedMedia = 0
        foreach ($entry in $mediaManifest.files) {
            $entryName = ([string]$entry.path).Replace('\', '/')
            $zipEntry = $entries[$entryName]
            if ($null -eq $zipEntry) {
                throw "SD media ZIP is missing: $entryName"
            }
            if ($zipEntry.Length -ne [int64]$entry.size) {
                throw "SD media ZIP size mismatch: $entryName"
            }
            $entryStream = $zipEntry.Open()
            $entryHasher = [Security.Cryptography.SHA256]::Create()
            try {
                $entrySha = ([BitConverter]::ToString(
                    $entryHasher.ComputeHash($entryStream)
                )).Replace('-', '').ToLowerInvariant()
            }
            finally {
                $entryHasher.Dispose()
                $entryStream.Dispose()
            }
            if ($entrySha -ne ([string]$entry.sha256).ToLowerInvariant()) {
                throw "SD media ZIP hash mismatch: $entryName"
            }
            $verifiedMedia++
        }
        if ($verifiedMedia -ne 9) {
            throw "SD media manifest contains $verifiedMedia files; expected 9"
        }
        Write-Pass 'SD media ZIP matches all 9 manifest hashes'
    }
    finally {
        $archive.Dispose()
    }
} catch {
    Write-Failure $_.Exception.Message
}

if (-not [string]::IsNullOrWhiteSpace($SdDrive)) {
    try {
        if ($SdDrive -notmatch '^[A-Za-z]:[\\/]?$') {
            throw "SD drive must be a drive root such as X: (received '$SdDrive')"
        }
        $driveLetter = $SdDrive.Substring(0, 1).ToUpperInvariant()
        $sdRoot = "${driveLetter}:\"
        $systemDrive = [IO.Path]::GetPathRoot($env:SystemRoot)
        if ($sdRoot.Equals($systemDrive, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing the Windows system drive: $sdRoot"
        }
        $volume = Get-Volume -DriveLetter $driveLetter -ErrorAction Stop
        if ($volume.DriveType -ne 'Removable' -and -not $AllowFixedDrive) {
            throw (
                "Drive $sdRoot reports '$($volume.DriveType)'; use -AllowFixedDrive " +
                'only after manually confirming it is the SD card'
            )
        }
        $fileSystem = [string]$volume.FileSystem
        if ($fileSystem -notin @('FAT', 'FAT32')) {
            throw "Drive $sdRoot uses '$fileSystem'; FAT/FAT32 is required"
        }
        if (-not (Test-Path -LiteralPath $sdRoot -PathType Container)) {
            throw "SD drive is not accessible: $sdRoot"
        }
        if ($null -eq $mediaManifest -or [string]::IsNullOrWhiteSpace($mediaManifestSha)) {
            throw 'The SD media ZIP manifest was unavailable'
        }

        foreach ($entry in $mediaManifest.files) {
            $targetPath = Resolve-SafeChild $sdRoot ([string]$entry.path)
            $targetPath = Resolve-ExistingFile $targetPath "SD-card fixture $($entry.path)"
            $targetItem = Get-Item -LiteralPath $targetPath
            if ($targetItem.Length -ne [int64]$entry.size -or
                    (Get-Sha256 $targetPath) -ne ([string]$entry.sha256).ToLowerInvariant()) {
                throw "SD-card fixture does not match: $($entry.path)"
            }
        }
        foreach ($relativeDirectory in @(
            'Waveshare\Recordings', 'Waveshare\AIChats', 'Waveshare\Diagnostics'
        )) {
            $directory = Resolve-SafeChild $sdRoot $relativeDirectory
            if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
                throw "Required SD directory is missing: $relativeDirectory"
            }
        }
        $cardManifestSha = Get-Sha256 (
            Resolve-ExistingFile (Join-Path $sdRoot 'media_manifest.json') 'SD-card manifest'
        )
        if ($cardManifestSha -ne $mediaManifestSha) {
            throw 'The SD-card media_manifest.json is not the current version'
        }
        Write-Pass (
            "SD card $sdRoot is $($volume.FileSystem), label '$($volume.FileSystemLabel)', " +
            'and all fixtures match'
        )
    } catch {
        Write-Failure $_.Exception.Message
    }
} else {
    Write-WarningResult 'No -SdDrive supplied; physical SD contents were not checked'
}

if ($Offline) {
    Write-WarningResult 'Offline mode selected; COM port and ESP-IDF environment were not checked'
} else {
    if ([string]::IsNullOrWhiteSpace($Port)) {
        Write-Failure 'No serial port supplied; rerun with -Port COMx'
    } else {
        try {
            $availablePorts = [IO.Ports.SerialPort]::GetPortNames()
            if ($availablePorts -notcontains $Port) {
                throw "$Port is not present"
            }
            $serialPort = $null
            try {
                $serialPort = Get-CimInstance Win32_SerialPort | Where-Object {
                    $_.DeviceID -eq $Port
                } | Select-Object -First 1
            } catch {
                # The port list is authoritative; CIM is only used for its label.
            }
            $serialName = if ($null -ne $serialPort -and
                    -not [string]::IsNullOrWhiteSpace([string]$serialPort.Name)) {
                [string]$serialPort.Name
            } else {
                $Port
            }
            Write-Pass "$Port is present as '$serialName'"
        } catch {
            Write-Failure $_.Exception.Message
        }
    }

    try {
        $null = Get-Command idf.py -ErrorAction Stop
        # ESP-IDF's export.ps1 exposes idf.py as a PowerShell function, whose
        # CommandInfo.Source is empty. Resolve it by command name so both the
        # function wrapper and a directly installed idf.py remain supported.
        $idfVersion = (& 'idf.py' --version 2>&1 | Out-String).Trim()
        if ($LASTEXITCODE -ne 0 -or $idfVersion -ne 'ESP-IDF v5.5.4') {
            throw "Expected ESP-IDF v5.5.4, received '$idfVersion'"
        }
        Write-Pass "ESP-IDF command reports $idfVersion"
    } catch {
        Write-Failure $_.Exception.Message
    }

    try {
        $null = Get-Command python -ErrorAction Stop
        $esptoolOutput = (& 'python' -m esptool version 2>&1 | Out-String).Trim()
        if ($LASTEXITCODE -ne 0 -or
                $esptoolOutput -notmatch '(?m)^esptool\.py v([^\r\n]+)\r?$') {
            throw 'esptool is unavailable through the active Python'
        }
        $esptoolVersion = $Matches[1]
        Write-Pass "esptool $esptoolVersion is available through the active Python"
    } catch {
        Write-Failure $_.Exception.Message
    }
}

if ($script:preflightFailures.Count -ne 0) {
    Write-Host ''
    foreach ($failure in $script:preflightFailures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    throw "Hardware preflight failed with $($script:preflightFailures.Count) issue(s)"
}

Write-Host ''
Write-Host 'Hardware preflight passed.' -ForegroundColor Green
if ($Offline) {
    Write-Host 'Reconnect the board and rerun without -Offline and with -Port COMx before flashing.'
}

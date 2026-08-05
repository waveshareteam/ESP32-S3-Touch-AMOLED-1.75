param(
    [string]$FixturePath
)

$ErrorActionPreference = 'Stop'

$componentRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$stubRoot = Join-Path $PSScriptRoot 'stubs'
$includeRoot = Join-Path $componentRoot 'include'
$buildRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('avi-player-safe-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $buildRoot | Out-Null

try {
    $common = @(
        '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-pthread',
        '-DAVI_PLAYER_VER_MAJOR=2', '-DAVI_PLAYER_VER_MINOR=0', '-DAVI_PLAYER_VER_PATCH=0',
        '-I', $stubRoot,
        '-I', $includeRoot,
        '-I', $PSScriptRoot
    )

    & gcc @common '-Dfopen=host_tracked_fopen' '-Dfclose=host_tracked_fclose' `
        '-Dfread=host_tracked_fread' '-c' `
        (Join-Path $componentRoot 'avi_player.c') '-o' (Join-Path $buildRoot 'avi_player.o')
    if ($LASTEXITCODE -ne 0) { throw 'avi_player.c host compilation failed' }

    & gcc @common '-c' (Join-Path $componentRoot 'avifile.c') '-o' (Join-Path $buildRoot 'avifile.o')
    if ($LASTEXITCODE -ne 0) { throw 'avifile.c host compilation failed' }

    & gcc @common '-c' (Join-Path $PSScriptRoot 'host_runtime.c') '-o' (Join-Path $buildRoot 'host_runtime.o')
    if ($LASTEXITCODE -ne 0) { throw 'host runtime compilation failed' }

    & gcc @common '-c' (Join-Path $PSScriptRoot 'avi_player_host_test.c') '-o' `
        (Join-Path $buildRoot 'avi_player_host_test.o')
    if ($LASTEXITCODE -ne 0) { throw 'host test compilation failed' }

    $testExe = Join-Path $buildRoot 'avi_player_host_test.exe'
    & gcc '-pthread' (Join-Path $buildRoot 'avi_player.o') (Join-Path $buildRoot 'avifile.o') `
        (Join-Path $buildRoot 'host_runtime.o') (Join-Path $buildRoot 'avi_player_host_test.o') `
        '-o' $testExe
    if ($LASTEXITCODE -ne 0) { throw 'host test link failed' }

    if ($FixturePath) {
        $resolvedFixture = (Resolve-Path -LiteralPath $FixturePath).Path
        & $testExe $resolvedFixture
    }
    else {
        & $testExe
    }
    if ($LASTEXITCODE -ne 0) { throw "host lifecycle tests failed with exit code $LASTEXITCODE" }
}
finally {
    $tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
    $resolvedBuildRoot = [System.IO.Path]::GetFullPath($buildRoot)
    $buildLeaf = Split-Path -Leaf $resolvedBuildRoot
    if ($resolvedBuildRoot.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -and
        $buildLeaf.StartsWith('avi-player-safe-', [StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $resolvedBuildRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
    else {
        throw "Refusing to remove unexpected host-test directory: $resolvedBuildRoot"
    }
}

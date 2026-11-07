<#
.SYNOPSIS
Render the project's local PlantUML sources as SVG and/or PNG.
.DESCRIPTION
Requires Java on PATH. Prefers the installed VS Code PlantUML extension;
otherwise downloads a pinned, checksum-verified JAR to the ignored .tools cache.
All diagram content is rendered locally. Smetana avoids a Graphviz install.
#>
[CmdletBinding()]
param(
    [ValidateSet('All', 'Svg', 'Png')]
    [string]$Format = 'All',
    [string]$PlantUmlJar
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$projectRoot = Split-Path -Parent $PSScriptRoot
$repositoryRoot = Split-Path -Parent $projectRoot
$umlRoot = Join-Path $projectRoot 'docs\uml'
$sourceDir = Join-Path $umlRoot 'source'
$plantUmlVersion = '1.2026.9'
$expectedHash = '96ace11f947a04a4320a413a0a2c6bad8b87daaac1869fe51e82622d812fe13c'
$javaCommand = Get-Command java -ErrorAction SilentlyContinue
if (-not $javaCommand) { throw 'Java is required. Install Java and ensure java is on PATH.' }

if (-not $PlantUmlJar) {
    $extensionRoot = Join-Path $env:USERPROFILE '.vscode\extensions'
    if (Test-Path -LiteralPath $extensionRoot) {
        $PlantUmlJar = Get-ChildItem -LiteralPath $extensionRoot -Directory -Filter 'jebbs.plantuml-*' |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName 'plantuml.jar' } |
            Where-Object { Test-Path -LiteralPath $_ } |
            Select-Object -First 1
    }
}
if (-not $PlantUmlJar) {
    $toolDir = Join-Path $repositoryRoot '.tools\uml-tools'
    New-Item -ItemType Directory -Path $toolDir -Force | Out-Null
    $PlantUmlJar = Join-Path $toolDir "plantuml-$plantUmlVersion-maven.jar"
    if (-not (Test-Path -LiteralPath $PlantUmlJar)) {
        $downloadPath = "$PlantUmlJar.download"
        $releaseUrl = "https://repo.maven.apache.org/maven2/net/sourceforge/plantuml/plantuml/$plantUmlVersion/plantuml-$plantUmlVersion.jar"
        Invoke-WebRequest -Uri $releaseUrl -OutFile $downloadPath
        if ((Get-FileHash -LiteralPath $downloadPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
            throw 'Downloaded PlantUML JAR failed SHA-256 verification.'
        }
        Move-Item -LiteralPath $downloadPath -Destination $PlantUmlJar
    }
    if ((Get-FileHash -LiteralPath $PlantUmlJar -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
        throw "Cached PlantUML JAR does not match the pinned version $plantUmlVersion."
    }
}
if (-not (Test-Path -LiteralPath $PlantUmlJar)) { throw "JAR not found: $PlantUmlJar" }
$PlantUmlJar = (Resolve-Path -LiteralPath $PlantUmlJar).Path
$umlSources = @(Get-ChildItem -LiteralPath $sourceDir -File | Where-Object { $_.Name -match '^\d{2}_.+\.puml$' } | Sort-Object Name)
if ($umlSources.Count -eq 0) { throw "No UML sources found in $sourceDir" }
$sourcePaths = @($umlSources | ForEach-Object { $_.FullName })
$javaOptions = @('-Xmx512m', '-Djava.awt.headless=true', '-DPLANTUML_LIMIT_SIZE=8192', '-jar', $PlantUmlJar, '-charset', 'UTF-8')

& $javaCommand.Source @javaOptions -checkonly @sourcePaths
if ($LASTEXITCODE -ne 0) { throw 'PlantUML syntax check failed.' }

$formats = if ($Format -eq 'All') { @('svg', 'png') } else { @($Format.ToLowerInvariant()) }
foreach ($outputFormat in $formats) {
    $outputDir = Join-Path $umlRoot $outputFormat
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    & $javaCommand.Source @javaOptions -failfast "-t$outputFormat" -o $outputDir @sourcePaths
    if ($LASTEXITCODE -ne 0) { throw "PlantUML $outputFormat render failed." }
    foreach ($umlSource in $umlSources) {
        $outputPath = Join-Path $outputDir "$($umlSource.BaseName).$outputFormat"
        if (-not (Test-Path -LiteralPath $outputPath) -or (Get-Item -LiteralPath $outputPath).Length -eq 0) {
            throw "Missing or empty output: $outputPath"
        }
        if ($outputFormat -eq 'svg' -and (Select-String -LiteralPath $outputPath -Pattern 'Syntax Error' -SimpleMatch -Quiet)) {
            throw "PlantUML error image detected: $outputPath"
        }
    }
    Write-Output "Rendered $($umlSources.Count) $($outputFormat.ToUpperInvariant()) diagrams to $outputDir"
}

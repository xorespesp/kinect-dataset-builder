param (
    [string]$BinDir = (Join-Path (Split-Path $PSScriptRoot) ".kinect-sdk")
)

$ErrorActionPreference = "Stop"

$k4a_nupkg_url = "https://www.nuget.org/api/v2/package/Microsoft.Azure.Kinect.Sensor/1.4.2"
$k4abt_nupkg_url = "https://www.nuget.org/api/v2/package/Microsoft.Azure.Kinect.BodyTracking/1.1.2"
$k4abt_onnx_nupkg_url = "https://www.nuget.org/api/v2/package/Microsoft.Azure.Kinect.BodyTracking.ONNXRuntime/1.10.0"

if (-not (Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir -Force | Out-Null }

$k4a_nupkg = Join-Path $BinDir "k4a_1.4.2.nupkg"
$k4abt_nupkg = Join-Path $BinDir "k4abt_1.1.2.nupkg"
$k4abt_onnx_nupkg = Join-Path $BinDir "k4abt_onnx_1.10.0.nupkg"

if (-not (Test-Path $k4a_nupkg)) {
    Write-Host "Fetching K4A nupkg ..."
    Invoke-WebRequest -Uri $k4a_nupkg_url -OutFile $k4a_nupkg
} else {
    Write-Host "K4A nupkg already fetched."
}

if (-not (Test-Path $k4abt_nupkg)) {
    Write-Host "Fetching K4ABT nupkg ..."
    Invoke-WebRequest -Uri $k4abt_nupkg_url -OutFile $k4abt_nupkg
} else {
    Write-Host "K4ABT nupkg already fetched."
}

if (-not (Test-Path $k4abt_onnx_nupkg)) {
    Write-Host "Fetching K4ABT ONNXRuntime nupkg ..."
    Invoke-WebRequest -Uri $k4abt_onnx_nupkg_url -OutFile $k4abt_onnx_nupkg
} else {
    Write-Host "K4ABT ONNXRuntime nupkg already fetched."
}

$k4a_nupkg_extracted = Join-Path $BinDir "k4a"
$k4abt_nupkg_extracted = Join-Path $BinDir "k4abt"
$k4abt_onnx_nupkg_extracted = Join-Path $BinDir "k4abt_onnx"

Write-Host "Installing packages to $BinDir ..."
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (-not (Test-Path $k4a_nupkg_extracted)) { [System.IO.Compression.ZipFile]::ExtractToDirectory($k4a_nupkg, $k4a_nupkg_extracted) }
if (-not (Test-Path $k4abt_nupkg_extracted)) { [System.IO.Compression.ZipFile]::ExtractToDirectory($k4abt_nupkg, $k4abt_nupkg_extracted) }
if (-not (Test-Path $k4abt_onnx_nupkg_extracted)) { [System.IO.Compression.ZipFile]::ExtractToDirectory($k4abt_onnx_nupkg, $k4abt_onnx_nupkg_extracted) }

$k4a_dlls = @(
    "$k4a_nupkg_extracted\lib\native\amd64\release\k4a.dll",
    "$k4a_nupkg_extracted\lib\native\amd64\release\k4arecord.dll",
    "$k4a_nupkg_extracted\lib\native\amd64\release\depthengine_2_0.dll"
)
$k4abt_dlls = @(
    "$k4abt_nupkg_extracted\lib\native\amd64\release\k4abt.dll"
)
$k4abt_models = @(
    "$k4abt_nupkg_extracted\content\dnn_model_2_0_op11.onnx",
    "$k4abt_nupkg_extracted\content\dnn_model_2_0_lite_op11.onnx"
)
$onnx_dlls = @(
    "$k4abt_onnx_nupkg_extracted\lib\native\amd64\release\onnxruntime.dll",
    "$k4abt_onnx_nupkg_extracted\lib\native\amd64\release\onnxruntime_providers_cuda.dll",
    "$k4abt_onnx_nupkg_extracted\lib\native\amd64\release\onnxruntime_providers_shared.dll",
    "$k4abt_onnx_nupkg_extracted\lib\native\amd64\release\onnxruntime_providers_tensorrt.dll",
    "$k4abt_onnx_nupkg_extracted\lib\native\amd64\release\directml.dll"
)

foreach ($file in $k4a_dlls + $k4abt_dlls + $k4abt_models + $onnx_dlls) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $BinDir -Force
        Write-Host "Installed $(Split-Path $file -Leaf)"
    } else {
        Write-Warning "File not found: $file"
    }
}

Write-Host "`nCleaning up ..."
#Remove-Item -Path $k4a_nupkg, $k4abt_nupkg, $k4abt_onnx_nupkg -Force -ErrorAction SilentlyContinue
Remove-Item -Path $k4a_nupkg_extracted, $k4abt_nupkg_extracted, $k4abt_onnx_nupkg_extracted -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`nDone! All dependencies are properly installed in $BinDir."

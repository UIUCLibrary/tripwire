[CmdletBinding()]
param (
    [ValidateNotNullOrEmpty()]
    [string]$PythonVersion = "3.13"
)

function Get-Uv{
    [CmdletBinding()]
    param (
        [string]$FallThroughPath
    )
    try{
        $uv = (Get-Command "uv.exe" -ErrorAction Stop).path
        Write-Host "Using system uv"
        return $uv
    } catch {
        py -m venv $FallThroughPath
        & $FallThroughPath\Scripts\pip install --disable-pip-version-check uv | Out-Null
        return Join-Path $FallThroughPath 'Scripts\uv'
    }

}

try{
    $tempPath = [System.IO.Path]::GetTempPath()
    $tempDirName = (New-Guid).ToString("N")
    $fullTempDirPath = Join-Path $tempPath $tempDirName
    New-Item -ItemType Directory -Path $fullTempDirPath | Out-Null
    $uv = Get-Uv -FallThroughPath $fullTempDirPath
    Write-Host "using $uv"
    & $uv build --python=${PythonVersion} --wheel
    if ($LASTEXITCODE -ne 0)
    {
        Write-Host "uv build failed with exit code: $LASTEXITCODE"
        exit $LASTEXITCODE # Exit the PowerShell script with the failure code
    }
    & $uv run --python=$PythonVersion --isolated --group standalone-packaging --no-dev contrib/create_standalone.py --include-tab-completions tripwire  contrib/bootstrap_standalone.py
    if ($LASTEXITCODE -ne 0)
    {
        Write-Host "contrib/create_standalone.py failed with exit code: $LASTEXITCODE"
        exit $LASTEXITCODE # Exit the PowerShell script with the failure code
    }
} finally {
    if (Test-Path $fullTempDirPath){
        Write-Host "Removing $fullTempDirPath"
        Remove-Item -Path $tempPath -Recurse -Force
    }
}

param(
    [string]$BotRoot = "C:\Prescription Automation Bot",
    [string]$PythonExe = "python",
    [string]$RepoUrl = "https://github.com/GaneshCloudrx/prescription-automation-bot.git",
    [string]$Branch = "dev"
)

$ErrorActionPreference = "Stop"

$deployPath = Join-Path $BotRoot "deploy"
$updateScriptPath = Join-Path $deployPath "update_from_git.ps1"
$appPath = Join-Path $BotRoot "app"
$mainPath = Join-Path $appPath "main.py"

if (Test-Path $updateScriptPath) {
    try {
        & $updateScriptPath -BotRoot $BotRoot -PythonExe $PythonExe -RepoUrl $RepoUrl -Branch $Branch
    }
    catch {
        Write-Host "Git update failed. Starting existing app code."
        Write-Host $_.Exception.Message
    }
}

Write-Host "Waiting 60 seconds before starting the bot."
Start-Sleep -Seconds 60

if (-not (Test-Path $mainPath)) {
    throw "Bot entrypoint not found: $mainPath"
}

Set-Location $appPath
& $PythonExe $mainPath

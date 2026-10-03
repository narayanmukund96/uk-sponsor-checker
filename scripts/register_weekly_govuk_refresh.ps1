param(
  [string]$TaskName = "UK Sponsor Checker Weekly Dataset Refresh",
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$PythonPath = "",
  [string]$DayOfWeek = "Monday",
  [string]$At = "09:30"
)

$ErrorActionPreference = "Stop"

if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if (-not $pythonCommand) {
    throw "No Python executable found. Pass -PythonPath explicitly."
  }
  $PythonPath = $pythonCommand.Source
}

$scriptPath = Join-Path $ProjectRoot "scripts\refresh_from_govuk.py"
$logDir = Join-Path $ProjectRoot "data\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$argument = "-NoProfile -ExecutionPolicy Bypass -Command `"Set-Location -LiteralPath '$ProjectRoot'; & '$PythonPath' '$scriptPath' *> '$logDir\weekly-refresh.log'`""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argument
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Refresh UK Sponsor Checker dataset from GOV.UK weekly." -Force | Out-Null
Write-Output "Registered scheduled task '$TaskName' for $DayOfWeek at $At."

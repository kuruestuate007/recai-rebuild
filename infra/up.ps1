[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Profile,
    [Parameter(Mandatory)][ValidatePattern('^[0-9]{12}$')][string]$AccountId,
    [Parameter(Mandatory)][ValidateSet('us-east-2','eu-central-2')][string]$Region,
    [Parameter(Mandatory)][ValidatePattern('^[a-z][a-z0-9-]{2,11}$')][string]$StackId,
    [Parameter(Mandatory)][ValidateRange(1,100000)][decimal]$MonthlyCapUsd,
    [Parameter(Mandatory)][string]$BudgetEmail,
    [Parameter(Mandatory)][uri]$PortalCallback,
    [Parameter(Mandatory)][string]$ConnectorZip,
    [Parameter(Mandatory)][string]$IngestZip,
    [Parameter(Mandatory)][string]$UsageFile,
    [Parameter(Mandatory)][ValidateRange(0,100000)][decimal]$ReviewedMonthlyUsd,
    [switch]$EnableRuntime,
    [switch]$EnableBudgetAction
)

$ErrorActionPreference = 'Stop'
function Invoke-Native([string]$Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command failed ($LASTEXITCODE)." }
}

if ($ReviewedMonthlyUsd -gt $MonthlyCapUsd) { throw 'Reviewed monthly estimate exceeds the cap.' }
$paths = @($ConnectorZip,$IngestZip,$UsageFile) | ForEach-Object {
    (Resolve-Path -LiteralPath $_ -ErrorAction Stop).Path
}
$ConnectorZip, $IngestZip, $UsageFile = $paths
$actual = Invoke-Native aws @('sts','get-caller-identity','--profile',$Profile,'--region',$Region,'--query','Account','--output','text')
if ("$actual".Trim() -ne $AccountId) { throw 'The active AWS account does not match the pinned account ID.' }
Write-Host "Target account $AccountId, region $Region, stack $StackId"
Write-Host "Reviewed all-in monthly estimate: USD $ReviewedMonthlyUsd. Budget: USD $MonthlyCapUsd."

$stateRoot = Join-Path $PSScriptRoot ".local/$AccountId-$Region-$StackId"
New-Item -ItemType Directory -Path $stateRoot -Force | Out-Null
$state = Join-Path $stateRoot 'terraform.tfstate'
$plan = Join-Path $stateRoot 'review.tfplan'
$planJson = Join-Path $stateRoot 'review.json'
$variables = @(
    "-var=profile=$Profile", "-var=account_id=$AccountId", "-var=region=$Region", "-var=stack_id=$StackId",
    "-var=monthly_cap_usd=$($MonthlyCapUsd.ToString([cultureinfo]::InvariantCulture))", "-var=budget_email=$BudgetEmail",
    "-var=portal_callback=$PortalCallback", "-var=connector_zip=$ConnectorZip", "-var=ingest_zip=$IngestZip",
    "-var=enable_runtime=$($EnableRuntime.IsPresent.ToString().ToLowerInvariant())",
    "-var=enable_budget_action=$($EnableBudgetAction.IsPresent.ToString().ToLowerInvariant())"
)
try {
    Invoke-Native terraform @("-chdir=$PSScriptRoot",'init','-input=false')
    Invoke-Native terraform (@("-chdir=$PSScriptRoot",'plan','-input=false',"-state=$state","-out=$plan") + $variables)
    $json = Invoke-Native terraform @("-chdir=$PSScriptRoot",'show','-json',$plan)
    $json | Set-Content -LiteralPath $planJson -Encoding utf8
    Invoke-Native infracost @('breakdown',"--path=$planJson","--usage-file=$UsageFile")
    if ((Read-Host "Review the plan, unpriced usage, and estimate. Type DEPLOY $StackId to apply") -cne "DEPLOY $StackId") { return }
    Invoke-Native terraform @("-chdir=$PSScriptRoot",'apply','-input=false',"-state=$state",$plan)
    Invoke-Native terraform @("-chdir=$PSScriptRoot",'output',"-state=$state",'-raw','endpoint')
} finally {
    foreach ($path in $plan, $planJson) {
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
    }
}

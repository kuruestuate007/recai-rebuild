[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Profile,
    [Parameter(Mandatory)][ValidatePattern('^[0-9]{12}$')][string]$AccountId,
    [Parameter(Mandatory)][ValidateSet('us-east-2','eu-central-2')][string]$Region,
    [Parameter(Mandatory)][ValidatePattern('^[a-z][a-z0-9-]{2,11}$')][string]$StackId,
    [Parameter(Mandatory)][string]$VarFile
)
$ErrorActionPreference = 'Stop'
function Invoke-Native([string]$Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command failed ($LASTEXITCODE)." }
}
$VarFile = (Resolve-Path -LiteralPath $VarFile -ErrorAction Stop).Path
$actual = Invoke-Native aws @('sts','get-caller-identity','--profile',$Profile,'--region',$Region,'--query','Account','--output','text')
if ("$actual".Trim() -ne $AccountId) { throw 'The active AWS account does not match the pinned account ID.' }

$stateRoot = Join-Path $PSScriptRoot ".local/$AccountId-$Region-$StackId"
$state = Join-Path $stateRoot 'terraform.tfstate'
$plan = Join-Path $stateRoot 'destroy.tfplan'
if (Test-Path -LiteralPath $state) {
    $target = (Invoke-Native terraform @("-chdir=$PSScriptRoot",'output',"-state=$state",'-json','target')) | ConvertFrom-Json
    if ($target.account -ne $AccountId -or $target.region -ne $Region -or $target.stack -ne $StackId) {
        throw 'State belongs to a different deployment target.'
    }
    try {
        $vars = @("-var-file=$VarFile","-var=profile=$Profile","-var=account_id=$AccountId","-var=region=$Region","-var=stack_id=$StackId")
        Invoke-Native terraform (@("-chdir=$PSScriptRoot",'plan','-destroy','-input=false',"-state=$state","-out=$plan") + $vars)
        if ((Read-Host "Type DESTROY $StackId to delete only the resources in this state") -cne "DESTROY $StackId") { return }
        Invoke-Native terraform @("-chdir=$PSScriptRoot",'apply','-input=false',"-state=$state",$plan)
        $managed = Invoke-Native terraform @("-chdir=$PSScriptRoot",'state','list',"-state=$state")
        if ($managed) { throw "Terraform still tracks: $managed" }
    } finally {
        if (Test-Path -LiteralPath $plan) { Remove-Item -LiteralPath $plan -Force }
    }
}
$remaining = Invoke-Native aws @('resourcegroupstaggingapi','get-resources','--profile',$Profile,'--region',$Region,
    '--tag-filters','Key=project,Values=recai-rebuild',"Key=stack,Values=$Region-$StackId",
    '--query','ResourceTagMappingList[].ResourceARN','--output','text')
if ("$remaining".Trim()) { throw "Tagged resources remain: $remaining" }
Write-Host 'No resources found in Terraform state or the regional tag inventory. Check global and untaggable resources separately.'


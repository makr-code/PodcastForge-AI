Write-Output '--- Processes with libiomp modules ---'
$found = $false
Get-Process -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        foreach ($m in $_.Modules) {
            if ($m.ModuleName -like '*libiomp*') {
                Write-Output ("{0,-6} {1} {2}" -f $_.Id, $_.ProcessName, $m.FileName)
                $found = $true
            }
        }
    } catch {
        # Access denied for system processes - ignore
    }
}
if (-not $found) { Write-Output 'None found.' }

Write-Output '--- Python processes (Id,Name,Path) ---'
Get-Process -Name python,python3 -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Path | Format-Table -AutoSize

Write-Output '--- Filesystem search for libiomp5md.dll (common locations) ---'
$paths = @('C:\Users\mkrueger\miniconda3','C:\VCC\VCCDB\PodcastForge-AI','C:\Program Files','C:\Program Files (x86)')
foreach ($p in $paths) {
    if (Test-Path $p) {
        Write-Output "Searching: $p"
        Get-ChildItem -Path $p -Filter 'libiomp5md.dll' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { Write-Output $_.FullName }
    }
}

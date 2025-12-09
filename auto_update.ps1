# CodeCrafters Shell Automation Script
param([string]$pythonCode)
$repoPath = "C:\Users\Prajeesh\codecrafters-shell-python"
Set-Content -Path "$repoPath\app\main.py" -Value $pythonCode -Encoding UTF8
cd $repoPath
git add app/main.py
git commit -m "automated stage update"
git push origin master
Write-Host "✓ Code pushed to CodeCrafters"
Write-Host "✓ Tests are running... check CodeCrafters for results"
Write-Host "✓ Tell me when you've reviewed the logs"
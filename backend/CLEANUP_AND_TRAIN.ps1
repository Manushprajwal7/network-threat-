# Clean cache and temporary files
Write-Host "========================================" -ForegroundColor Green
Write-Host "CLEANING CACHE AND TEMP FILES" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Remove __pycache__ directories
Write-Host "Removing __pycache__ directories..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -Force | Remove-Item -Recurse -Force
Write-Host "[OK] Removed __pycache__ directories" -ForegroundColor Green

# Remove .pyc files
Write-Host "Removing .pyc files..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -Force | Remove-Item -Force
Write-Host "[OK] Removed .pyc files" -ForegroundColor Green

# Clear old reports
Write-Host "Clearing old reports..." -ForegroundColor Yellow
$reportDir = ".\ml_model\reports"
if (Test-Path $reportDir) {
    Remove-Item -Path "$reportDir\*" -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Cleared reports directory" -ForegroundColor Green
}

# Keep existing trained models (optional - comment out if you want to retrain all)
Write-Host "`nExisting trained models will be kept:" -ForegroundColor Cyan
Write-Host "  - random_forest.pkl" -ForegroundColor Gray
Write-Host "  - decision_tree.pkl" -ForegroundColor Gray
Write-Host "  - logistic_regression.pkl" -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "CLEANUP COMPLETE - Ready for training!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

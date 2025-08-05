# DHM Hydro Adjust - Setup Script for Windows
# Run this script in PowerShell from the project root directory

Write-Host "DHM Hydro Adjust - Development Setup" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "setup.py")) {
    Write-Host "Error: setup.py not found. Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

Write-Host "`nSetting up Python environment..." -ForegroundColor Yellow

# Option 1: Using conda (recommended)
Write-Host "`nOption 1: Conda Environment (Recommended)" -ForegroundColor Cyan
Write-Host "Run these commands to create a conda environment:" -ForegroundColor White
Write-Host "  conda env create -f environment.yml" -ForegroundColor Gray
Write-Host "  conda activate hydroadjust-dev" -ForegroundColor Gray

Write-Host "`nOption 2: Pip Installation" -ForegroundColor Cyan  
Write-Host "Run these commands to install with pip:" -ForegroundColor White
Write-Host "  pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "  pip install -e ." -ForegroundColor Gray

Write-Host "`nTesting Installation" -ForegroundColor Yellow
Write-Host "After installation, test with:" -ForegroundColor White
Write-Host "  python test_installation.py" -ForegroundColor Gray

Write-Host "`nUsing the Workflow" -ForegroundColor Yellow
Write-Host "1. Open 'hydro_workflow_notebook.ipynb' in Jupyter Lab or VS Code" -ForegroundColor White
Write-Host "2. Configure your data paths in the configuration section" -ForegroundColor White  
Write-Host "3. Run the workflow cells step by step" -ForegroundColor White

Write-Host "`nStarting Jupyter Lab" -ForegroundColor Yellow
$response = Read-Host "Would you like to start Jupyter Lab now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    try {
        jupyter lab
    } catch {
        Write-Host "Jupyter Lab not found. Install it with: pip install jupyterlab" -ForegroundColor Red
    }
}

Write-Host "`nSetup complete! 🎉" -ForegroundColor Green

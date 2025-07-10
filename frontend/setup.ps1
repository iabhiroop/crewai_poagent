Write-Host "Setting up AI Purchase Order System Frontend..." -ForegroundColor Green
Write-Host ""

Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv frontend_env

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\frontend_env\Scripts\Activate.ps1"

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "Setup complete! To run the frontend:" -ForegroundColor Green
Write-Host "1. Navigate to the frontend directory: cd frontend" -ForegroundColor Cyan
Write-Host "2. Activate environment: .\frontend_env\Scripts\Activate.ps1" -ForegroundColor Cyan  
Write-Host "3. Run the app: streamlit run app.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "The dashboard will open in your browser at http://localhost:8501" -ForegroundColor Green
Read-Host "Press Enter to continue..."

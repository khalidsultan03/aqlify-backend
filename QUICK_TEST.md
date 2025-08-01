# Quick Test Setup for Aqlify Platform

## Option 1: Install Python and Test Locally

### Step 1: Install Python
1. Download Python 3.11+ from https://python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart your terminal

### Step 2: Quick Local Test
```powershell
# Navigate to your project directory
cd your-aqlify-project-folder

# Install dependencies
pip install fastapi uvicorn sqlalchemy python-dotenv openai

# Create a simple test environment file
echo "OPENAI_API_KEY=test-key" > .env
echo "DATABASE_URL=sqlite:///./test.db" >> .env
echo "SECRET_KEY=test-secret-key-for-development" >> .env

# Run the basic version first
python main.py

# Or run the advanced version
python main_v3.py
```

## Option 2: Docker Test (Easiest)

### Prerequisites
- Install Docker Desktop from https://docker.com/products/docker-desktop

### Quick Docker Test
```powershell
# Build and run with Docker
docker build -t aqlify-test .
docker run -p 8000:8000 -e OPENAI_API_KEY=test-key aqlify-test
```

## Option 3: Online Test (No Installation)

### Use GitHub Codespaces or Replit
1. Push code to GitHub
2. Open in GitHub Codespaces
3. Run: `python main_v3.py`

## Testing the API

Once running (any method), test these endpoints:

### 1. Check if server is running
```bash
curl http://localhost:8000/
```

### 2. View API documentation
Open in browser: http://localhost:8000/docs

### 3. Test registration
```powershell
curl -X POST "http://localhost:8000/auth/register" -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"password123\",\"company_name\":\"Test Company\"}"
```

### 4. Test basic forecast (after registration)
```powershell
# First get your access token from step 3, then:
curl -X POST "http://localhost:8000/forecast" -H "Authorization: Bearer YOUR_TOKEN" -H "Content-Type: application/json" -d "{\"product_id\":\"test\",\"forecast_days\":7,\"method\":\"statistical\"}"
```

## Expected Results

✅ Server starts on http://localhost:8000
✅ API docs accessible at /docs
✅ Registration works
✅ Basic forecasting works
✅ No major errors in logs

## Troubleshooting

### Common Issues:
1. **Port already in use**: Change port in command `uvicorn main_v3:app --port 8001`
2. **Missing dependencies**: Run `pip install -r requirements_v3.txt`
3. **Database errors**: Use SQLite for testing: `DATABASE_URL=sqlite:///./test.db`
4. **API key errors**: Set dummy key: `OPENAI_API_KEY=test-key`

## Quick Success Check

If you see this when visiting http://localhost:8000:
```json
{
  "message": "Aqlify Universal Forecasting Platform",
  "version": "3.0.0",
  "status": "active"
}
```

🎉 **SUCCESS!** Your platform is running!

Next: Visit http://localhost:8000/docs to see the full API documentation and test all features interactively.

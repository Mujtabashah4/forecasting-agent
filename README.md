# Forecasting Agent System

**AI-Powered Project Cost & Schedule Forecasting Tool**

## Overview

The Forecasting Agent is an AI-powered system that analyzes project budgets, actuals, and purchase orders to provide intelligent forecasting recommendations. It integrates with Capexplan via secure REST API and provides human-in-the-loop recommendations without auto-applying changes.

## Key Features

- Analyzes project budgets, actuals, and purchase orders
- Detects variances, large POs, and budget threshold violations
- Generates alternative forecast scenarios with AI explanations
- Provides human-in-the-loop recommendations (no auto-apply)
- Secure REST API with JWT authentication
- AI-powered analysis using Qwen 2.5 LLM via Ollama

## Technology Stack

- **API Framework:** FastAPI 0.104.1
- **Workflow Engine:** LangGraph 0.0.49
- **LLM:** Qwen 2.5-7B via Ollama
- **Authentication:** JWT (PyJWT)
- **Data Validation:** Pydantic v2
- **Deployment:** Docker + Docker Compose
- **Python:** 3.11+

## Quick Start

### 1. Setup Environment

```bash
# Create .env file
cp .env.example .env
# Edit .env to change API_SECRET_KEY and SECRET_KEY

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Ollama & Qwen Model

```bash
# Install Ollama (if needed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Qwen 2.5 model
ollama pull qwen2.5:7b
```

### 3. Start Server

```bash
# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API Docs:** http://localhost:8000/docs

### 4. Test Installation

```bash
# Run automated tests
python3 scripts/test_cli.py
```

**Expected Output:**
```
✅ Status: healthy
✅ Token obtained successfully
✅ Forecast review completed successfully
📈 Budget Consumption: X.X%
📈 Net Order Value: $X,XXX.XX
⚠️  Flags Detected: X
💡 Scenarios Generated: 3
```

## Project Structure

```
Marc_forecastingAgent/
├── app/
│   ├── agent/
│   │   ├── nodes/          # 9 workflow nodes
│   │   ├── state.py        # Agent state definition
│   │   └── workflow.py     # LangGraph orchestration
│   ├── api/
│   │   ├── deps.py         # Auth dependencies
│   │   └── v1/
│   │       ├── endpoints/  # Auth, health, forecast endpoints
│   │       └── router.py   # API router
│   ├── schemas/            # Request, response, common schemas
│   ├── services/           # LLM service, auth service
│   ├── utils/              # Logger, helpers
│   ├── config.py           # Configuration
│   └── main.py             # FastAPI application
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   └── test_cli.py         # Testing script
├── tests/                  # Test directory
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## LangGraph Workflow Nodes

The system uses a 9-node LangGraph workflow:

1. **Load Data** - Validates and loads input data
2. **Calculate Metrics** - NOV calculation, budget consumption
3. **Detect Variances** - Identifies budget overruns (>5% threshold)
4. **Check Thresholds** - 90% budget alert, NOV constraint
5. **Analyze POs** - Large PO detection (>2x monthly average)
6. **Generate Scenarios** - Creates forecast options
7. **Build Questions** - Generates questions for user based on detected issues
8. **Generate Explanation** - AI-powered explanation with fallback
9. **Compile Response** - Final response assembly

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/token` | POST | Get JWT access token |
| `/api/v1/health` | GET | Health check + LLM status |
| `/api/v1/forecast/review` | POST | Main forecast analysis endpoint |

## Business Rules

- Actuals are final (never change past months)
- NOV calculation (Total POs - Total Actuals)
- NOV constraint (future forecasts >= NOV)
- 90% budget threshold alert
- Large PO detection (>2x monthly)
- Variance detection (>5% threshold)
- Human-in-the-loop (no auto-apply)
- NEW forecast creation (preserve original)

## Docker Deployment

```bash
cd docker

# Start all services
docker-compose up -d

# Pull Qwen model in Ollama container
docker-compose exec ollama ollama pull qwen2.5:7b

# Check logs
docker-compose logs -f forecasting-agent

# Stop services
docker-compose down
```

## Security Features

- **JWT Token Authentication** - Secure token-based auth
- **IP Whitelisting** - Restrict access to allowed IPs
- **Environment Variables** - No credentials in code
- **Audit Logging** - All API calls logged
- **CORS Configuration** - Cross-origin request control
- **Password Hashing** - bcrypt password storage

## What Agent Does

✅ Analyzes forecast, actuals, POs, variances
✅ Calculates NOV (Total POs - Total Actuals)
✅ Detects issues (variances, thresholds, large POs)
✅ Generates scenarios with AI explanations
✅ Returns recommendations to TEMP TABLE
✅ Human-in-the-loop (no auto-apply)

## What Agent Does NOT Do

❌ Modify past actuals
❌ Apply rollover (Capexplan does this)
❌ Auto-apply changes
❌ Connect to database directly (API only)
❌ Handle UI (Capexplan handles this)

## Troubleshooting

### Ollama Connection Failed

```bash
# Check Ollama is running
ollama list

# Start Ollama service
ollama serve

# Verify Qwen model is pulled
ollama pull qwen2.5:7b
```

### Authentication Errors

- Check `.env` file has correct `SECRET_KEY` and `API_SECRET_KEY`
- Verify username/password: `capexplan` / `demo_password`
- Check IP is in `ALLOWED_IPS` list

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## License

Created: January 2026
Technology: FastAPI + LangGraph + Qwen 2.5-7B + Ollama

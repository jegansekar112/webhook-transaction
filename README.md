# Backend - Webhook Transaction Service

A Flask-based service that receives transaction webhooks, processes them asynchronously, and stores results in a PostgreSQL database.

## 📋 Features

- **Fast Webhook Processing**: Returns 202 Accepted within 500ms
- **Background Task Processing**: Uses Celery for async processing with 30-second delay
- **Idempotency**: Handles duplicate webhooks gracefully
- **Data Persistence**: Stores transactions in PostgreSQL
- **Health Check**: Endpoint to verify service status
- **Transaction Query**: Retrieve transaction status by ID

## 🛠️ Technology Stack

- **Flask**: Lightweight Python web framework
- **Marshmallow**: Schema validation and serialization
- **PostgreSQL**: Relational database
- **Celery**: Distributed task queue
- **Redis**: Message broker for Celery
- **SQLAlchemy**: ORM for database operations
- **Gunicorn**: Production WSGI server

## 📦 Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+

### Setup Steps

1. **Clone the repository and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your database and Redis credentials:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/webhook_db
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

5. **Set up Database**

   **Option A: Cloud Database (Recommended for Production)**
   
   As per requirements: "Use any cloud-based database"
   
   - **Supabase** (Recommended - Free tier): See [CLOUD_DATABASE_SETUP.md](./CLOUD_DATABASE_SETUP.md)
   - **Railway PostgreSQL**: Add PostgreSQL service, copy connection URL
   - **AWS RDS**: Create PostgreSQL instance, get endpoint
   - **Neon**: Create serverless PostgreSQL project
   
   Update `.env` with cloud database URL:
   ```env
   DATABASE_URL=postgresql://user:password@cloud-host:5432/database
   ```
   
   **Option B: Local Database (For Development Only)**
   
   - **SQLite** (Default - No setup needed): Already configured
   - **Local PostgreSQL**: 
     ```bash
     createdb webhook_db
     # Update .env: DATABASE_URL=postgresql://postgres:postgres@localhost:5432/webhook_db
     ```

6. **Initialize database tables**
   ```bash
   python -c "from app.database import engine, Base; from app.models import Transaction; Base.metadata.create_all(bind=engine)"
   ```
   
   **Note:** For cloud databases, run this once after setting DATABASE_URL. Tables will be created automatically.

## 🚀 Running the Application

### Quick Start (Recommended)

**Use the startup script to start all services:**
```bash
cd backend
./start_services.sh
```

This will automatically:
- ✅ Check and start Redis (if needed)
- ✅ Start Celery worker for background processing
- ✅ Start Flask API server

### Manual Start (Step by Step)

**1. Start Redis (Required for Celery)**
```bash
# Install Redis if not installed:
# Ubuntu/Debian: sudo apt install redis-server
# macOS: brew install redis

redis-server
# Or run in background: redis-server --daemonize yes
```

**2. Start Celery Worker (In a separate terminal)**
```bash
cd backend
source venv/bin/activate
celery -A celery_worker.celery_app worker --loglevel=info
```

**3. Start Flask Server**

**Make sure you're in the backend directory:**
```bash
cd backend
source venv/bin/activate
```

**Development mode (choose one method):**

**Method 1: Using run.py (Recommended - easiest)**
```bash
python3 run.py
```

**Method 2: Running as module**
```bash
python3 -m app.main
```

**Method 3: Using Flask CLI**
```bash
flask --app app.main run --host 0.0.0.0 --port 8000
```

**Production mode (using Gunicorn):**
```bash
gunicorn app.main:app --bind 0.0.0.0:8000 --workers 4 --threads 2
```

### Stop All Services

```bash
cd backend
./stop_services.sh
```

Or manually:
```bash
pkill -f "celery.*worker"
pkill -f "python3 run.py"
redis-cli shutdown  # Optional
```

The API will be available at `http://localhost:8000`

**⚠️ Important:** For transactions to be processed (status change from PROCESSING to PROCESSED), you **must** have:
1. ✅ Redis running
2. ✅ Celery worker running

Without these, webhooks will be accepted but transactions will remain in PROCESSING status.

## 📡 API Endpoints

### 1. Health Check
```http
GET /
```

**Response:**
```json
{
  "status": "HEALTHY",
  "current_time": "2024-01-15T10:30:00Z"
}
```

### 2. Webhook Endpoint
```http
POST /v1/webhooks/transactions
Content-Type: application/json
```

**Request Body:**
```json
{
  "transaction_id": "txn_abc123def456",
  "source_account": "acc_user_789",
  "destination_account": "acc_merchant_456",
  "amount": 1500,
  "currency": "INR"
}
```

**Response:** `202 Accepted`
```json
{
  "message": "Webhook received and queued for processing"
}
```

### 3. Query Transaction
```http
GET /v1/transactions/{transaction_id}
```

**Response:**
```json
{
  "transaction_id": "txn_abc123def456",
  "source_account": "acc_user_789",
  "destination_account": "acc_merchant_456",
  "amount": 1500.0,
  "currency": "INR",
  "status": "PROCESSED",
  "created_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:30:30Z"
}
```

## 🧪 Testing

### Test Single Transaction
```bash
curl -X POST http://localhost:8000/v1/webhooks/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_test_001",
    "source_account": "acc_user_001",
    "destination_account": "acc_merchant_001",
    "amount": 100.50,
    "currency": "USD"
  }'
```

Wait ~30 seconds, then check status:
```bash
curl http://localhost:8000/v1/transactions/txn_test_001
```

### Test Idempotency (Duplicate Prevention)
```bash
# Send same webhook multiple times
curl -X POST http://localhost:8000/v1/webhooks/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_duplicate_test",
    "source_account": "acc_user_001",
    "destination_account": "acc_merchant_001",
    "amount": 200.00,
    "currency": "USD"
  }'

# Send again immediately
curl -X POST http://localhost:8000/v1/webhooks/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_duplicate_test",
    "source_account": "acc_user_001",
    "destination_account": "acc_merchant_001",
    "amount": 200.00,
    "currency": "USD"
  }'
```

Only one transaction should be processed.

### Test Performance
```bash
# Send multiple webhooks quickly
for i in {1..10}; do
  curl -X POST http://localhost:8000/v1/webhooks/transactions \
    -H "Content-Type: application/json" \
    -d "{
      \"transaction_id\": \"txn_perf_$i\",
      \"source_account\": \"acc_user_$i\",
      \"destination_account\": \"acc_merchant_$i\",
      \"amount\": $((i * 100)),
      \"currency\": \"USD\"
    }"
done
```

All should return 202 Accepted quickly (<500ms).

## 🏗️ Architecture Explanation

### Code Structure

```
backend/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Flask app and endpoints
│   ├── database.py          # Database connection and session management
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Marshmallow request/response schemas
│   └── tasks.py             # Celery background tasks
├── celery_worker.py         # Celery worker entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Key Design Decisions

1. **Flask**: Chosen for its simplicity, flexibility, and large ecosystem. Lightweight and easy to deploy
2. **Marshmallow**: Provides schema validation and serialization similar to Pydantic
3. **Celery + Redis**: Provides reliable background task processing with retry mechanisms
4. **PostgreSQL**: Robust relational database for transaction storage
5. **Idempotency**: Implemented at database level using `transaction_id` as primary key
6. **202 Accepted**: Returns immediately while processing happens asynchronously
7. **Gunicorn**: Production WSGI server for running Flask in production

### Processing Flow

1. Webhook received → Flask endpoint
2. Validate request data using Marshmallow schema
3. Check if transaction exists (idempotency)
4. Store transaction with `PROCESSING` status
5. Return 202 Accepted immediately
6. Trigger Celery background task
7. Task waits 30 seconds (simulating external API)
8. Update transaction status to `PROCESSED`
9. Set `processed_at` timestamp

## ☁️ Deployment

### Option 1: Railway
1. Create account at [railway.app](https://railway.app)
2. Create new project
3. Add PostgreSQL service
4. Add Redis service
5. Deploy from GitHub repository
6. Set environment variables

### Option 2: Heroku
1. Install Heroku CLI
2. Create `Procfile` (already included):
   ```
   web: gunicorn app.main:app --bind 0.0.0.0:$PORT --workers 4 --threads 2
   worker: celery -A celery_worker.celery_app worker --loglevel=info
   ```
3. Deploy using Heroku Git

### Option 3: AWS/GCP/Azure
- Use managed PostgreSQL (RDS/Cloud SQL)
- Use managed Redis (ElastiCache/Memorystore)
- Deploy Flask using Gunicorn with Docker or EC2/Compute Engine
- Run Celery worker as separate service

## 📝 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery message broker | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/0` |

## 🔍 Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL format
- Ensure database exists

### Celery Worker Not Processing
- Verify Redis is running: `redis-cli ping`
- Check Celery worker logs
- Ensure CELERY_BROKER_URL is correct

### Tasks Not Completing
- Check Celery worker is running
- Verify Redis connectivity
- Check worker logs for errors

## 📄 License

Created for WFG Full Stack Developer Assessment.




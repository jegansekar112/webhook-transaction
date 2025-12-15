# Webhook Transaction Service

A Flask based service that receives transaction webhooks, processes them asynchronously, and stores results in a PostgreSQL database.

## Features

- **Fast Webhook Processing**: Returns 202 Accepted
- **Background Task Processing**: Uses Python threads for async processing with 30 second delay
- **Idempotency**: Handles duplicate webhooks gracefully
- **Data Persistence**: Stores transactions in PostgreSQL
- **Health Check**: Endpoint to verify service status
- **Transaction Query**: Retrieve transaction status by ID

## Technology Stack

- **Flask**: Lightweight Python web framework
- **Pydantic**: Schema validation and serialization
- **PostgreSQL**: Relational database
- **Python Threading**: Background task processing
- **SQLAlchemy**: ORM for database operations
- **Gunicorn**: Production WSGI server

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 12+ (or SQLite for local development)

### Setup Steps

1. **Clone the repository and navigate to backend directory**

```bash
cd backend
```

2. **Create virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create `.env` file with your database credentials:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/webhook_db
# Or use SQLite for local development:
# DATABASE_URL=sqlite:///./webhook_db.sqlite
```

5. **Set up Database**

- **Supabase** (Recommended - Free tier)

Update `.env` with cloud database URL:

```env
DATABASE_URL=postgresql://user:password@cloud-host:5432/database
```

6. **Initialize database tables**

```bash
python -c "from app.database import engine, Base; from app.models import Transaction; Base.metadata.create_all(bind=engine)"
```

**Note:** For cloud databases, run this once after setting DATABASE_URL. Tables will be created automatically.

## Running the Application

**Use the startup script to start the service:**

```bash
cd backend
./start_services.sh
```

This will automatically:

- Start Flask API server
- Background processing uses Python threads

### Manual Start (Step by Step)

**Start Flask Server**

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

### Stop Service

```bash
cd backend
./stop_services.sh
```

Or manually:

```bash
pkill -f "python3 run.py"
```

The API will be available at `http://localhost:8000`

** Important:** Background processing uses Python threads. Transactions will be processed automatically after ~30 seconds.

## API Endpoints

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

## Testing

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

## Architecture Explanation

### Code Structure

```
backend/
├── app/
│ ├── __init__.py # Package initialization
│ ├── main.py # Flask app and endpoints
│ ├── database.py # Database connection and session management
│ ├── models.py # SQLAlchemy database models
│ ├── schemas.py # Pydantic request/response schemas
│ ├── tasks_threaded.py # Thread-based background processing
│ └── utils.py # Utility functions
├── requirements.txt # Python dependencies
├── run.py # Application entry point
└── README.md # This file
```

### Key Design Decisions

1. **Flask**: Chosen for its simplicity, flexibility, and large ecosystem. Lightweight and easy to deploy
2. **Pydantic**: Provides schema validation and serialization with type safety
3. **Python Threading**: Simple background processing without Redis/Celery complexity. Perfect for assessment requirements
4. **PostgreSQL**: Robust relational database for transaction storage
5. **Idempotency**: Implemented at database level using `transaction_id` as primary key
6. **202 Accepted**: Returns immediately while processing happens asynchronously
7. **Gunicorn**: Production WSGI server for running Flask in production

### Processing Flow

1. Webhook received → Flask endpoint
2. Validate request data using Pydantic schema
3. Check if transaction exists (idempotency)
4. Store transaction with `PROCESSING` status
5. Return 202 Accepted immediately
6. Start background thread for processing
7. Thread waits 30 seconds (simulating external API)
8. Update transaction status to `PROCESSED`
9. Set `processed_at` timestamp

## Deployment

### Option 1: Render (Recommended - Easiest)

1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click "New +" → "Blueprint"
4. Connect your repository
5. Render will auto-setup from `render.yaml` (no Redis needed!)

### Option 2: Railway

1. Create account at [railway.app](https://railway.app)
2. Create new project
3. Add PostgreSQL service (no Redis needed!)
4. Deploy from GitHub repository
5. Set DATABASE_URL environment variable

### Option 3: Vercel (Now Possible!)

1. Install Vercel CLI: `npm i -g vercel`
2. Create `vercel.json` configuration
3. Deploy: `vercel --prod`
4. No Redis/Celery needed - threads work in serverless!

### Option 4: Heroku

1. Install Heroku CLI
2. Create `Procfile` with:

```
web: gunicorn app.main:app --bind 0.0.0.0:$PORT --workers 4
```

3. Deploy using Heroku Git
4. Add PostgreSQL addon (no Redis needed!)

## Environment Variables

| Variable       | Description                  | Example                               |
| -------------- | ---------------------------- | ------------------------------------- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |

## Troubleshooting

### Database Connection Issues

- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL format
- Ensure database exists

### Background Processing Not Working

- Check Flask app logs for thread errors
- Verify database connection is working
- Ensure transactions are being created in database
- Check that threads are starting (look for log messages)

## License

Created for WFG Full Stack Developer Assessment.

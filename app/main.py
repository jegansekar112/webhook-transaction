"""
Main Flask application file.
This file sets up the Flask app and defines all API endpoints.
"""
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from app.database import get_db, engine, Base
from app.models import Transaction, TransactionStatus
from app.schemas import (
    WebhookRequest,
    TransactionResponse)
from pydantic import ValidationError as PydanticValidationError
from app.tasks_threaded import process_transaction_async
from app.utils import get_ist_now, get_ist_now_naive  

Base.metadata.create_all(bind=engine)

app = Flask(__name__)

CORS(app)

@app.route("/", methods=["GET"])
def health_check():
    """
    Health check endpoint 
    """
    current_time = get_ist_now()
    
    formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "status": "HEALTHY",
        "current_time": formatted_time
    }, 200

@app.route("/v1/webhooks/transactions", methods=["POST"])
def receive_webhook():
    """
    Webhook endpoint to receive transaction notifications.
    
    This endpoint:
    1. Accepts transaction webhook data
    2. Returns 202 Accepted immediately 
    3. Stores transaction in database with PROCESSING status
    4. Triggers background processing task
    5. Handles idempotency 
    
    Returns:
        202 Accepted status with acknowledgment response
    """
    db = next(get_db())
    
    try:
        # Validate request JSON data using Pydantic
        try:
            webhook_request = WebhookRequest(**request.json)
        except PydanticValidationError as err:
            return jsonify({
                "error": "Validation error",
                "details": err.errors()
            }), 400
        
        existing_transaction = db.query(Transaction).filter(
            Transaction.transaction_id == webhook_request.transaction_id
        ).first()
        
        if existing_transaction:
            # Transaction already exists
            if existing_transaction.status == TransactionStatus.PROCESSING:
                return jsonify({
                    "message": "Transaction already being processed"
                }), 202
            else:
                return jsonify({
                    "message": "Transaction already processed"
                }), 202
        
        # Create new transaction record with PROCESSING status
        new_transaction = Transaction(
            transaction_id=webhook_request.transaction_id,
            source_account=webhook_request.source_account,
            destination_account=webhook_request.destination_account,
            amount=webhook_request.amount,
            currency=webhook_request.currency,
            status=TransactionStatus.PROCESSING,
            created_at=get_ist_now_naive()  
        )
        
        db.add(new_transaction)
        
        # Commit transaction to database
        db.commit()
        
        # Trigger background processing using thread
        process_transaction_async(webhook_request.transaction_id)
        
        # Return response immediately 
        return jsonify({
            "message": "Webhook received and queued for processing"
        }), 202
    
    except Exception as e:
        db.rollback()
        app.logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({
            "message": "Webhook received, processing may be delayed"
        }), 202
    
    finally:
        db.close()

@app.route("/v1/transactions/<transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    """
    Query endpoint to retrieve transaction status.
    
    Args:
        transaction_id: The unique identifier of the transaction (from URL path)
    
    Returns:
        JSON array with transaction details including status and timestamps
        Format: [{"transaction_id": "...", ...}] 
    
    Raises:
        404: If transaction not found
    """
    db = next(get_db())
    
    try:
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()
        
        if not transaction:
            # Transaction not found 
            abort(404, description=f"Transaction {transaction_id} not found")
        
        transaction_response = TransactionResponse.model_validate(transaction)
        
        transaction_dict = transaction_response.model_dump(mode='json')
        
        return jsonify([transaction_dict]), 200
    
    finally:
        db.close()

@app.errorhandler(404)
def not_found(error):
    """
    Custom 404 error handler.
    Returns JSON response instead of HTML.
    """
    return jsonify({
        "error": "Not Found",
        "message": str(error.description)
    }), 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

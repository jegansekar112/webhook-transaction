"""
Background task processing using Python threads.
This is a simpler alternative to Celery that doesn't require Redis.
"""
import threading
import time
from app.database import SessionLocal
from app.models import Transaction, TransactionStatus
from app.utils import get_ist_now_naive
import logging

logger = logging.getLogger(__name__)

def process_transaction_background(transaction_id: str):
    """
    Background task to process a transaction using a thread.
    
    Args:
        transaction_id: The unique identifier of the transaction to process
    
    This function:
    1. Waits 30 seconds (simulating external API calls)
    2. Updates transaction status to PROCESSED
    3. Sets processed_at timestamp
    """
    try:
        # simulating external API call
        logger.info(f"Processing transaction {transaction_id} in background thread...")
        time.sleep(30)
        
        # Create new database session for this thread
        db = SessionLocal()
        
        try:
            transaction = db.query(Transaction).filter(
                Transaction.transaction_id == transaction_id
            ).first()
            
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return
            
            # Check if already processed 
            if transaction.status == TransactionStatus.PROCESSED:
                logger.info(f"Transaction {transaction_id} already processed")
                return
            
            # Update transaction status to PROCESSED
            transaction.status = TransactionStatus.PROCESSED
            transaction.processed_at = get_ist_now_naive()
            
            db.commit()
            logger.info(f"Transaction {transaction_id} processed successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing transaction {transaction_id}: {str(e)}", exc_info=True)
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Thread error for transaction {transaction_id}: {str(e)}", exc_info=True)

def process_transaction_async(transaction_id: str):
    """
    Start a background thread to process a transaction.
    
    Args:
        transaction_id: The unique identifier of the transaction to process
    """
    thread = threading.Thread(
        target=process_transaction_background,
        args=(transaction_id,),
        daemon=True 
    )
    thread.start()
    logger.info(f"Started background thread for transaction {transaction_id}")


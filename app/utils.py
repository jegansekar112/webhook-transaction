from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """
    Get current time in Indian Standard Time
    
    Returns:
        datetime: Current datetime in IST timezone
    """
    utc_now = datetime.now(pytz.UTC)
    ist_now = utc_now.astimezone(IST)
    return ist_now

def get_ist_now_naive():
    """
    Get current time in IST as naive datetime object    
    Returns:
        datetime: Current datetime in IST (naive)
    """
    ist_now = get_ist_now()
    return ist_now.replace(tzinfo=None)


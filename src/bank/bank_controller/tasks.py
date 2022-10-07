from config.celery import app

from .services.credit_service import checking_credits_status


# Starts a task to check the status of credits

@app.task
def periodic_check_credit_status():
    checking_credits_status()
from celery import shared_task
import pandas as pd
from django.contrib.auth import get_user_model
from django.utils.timezone import now
import requests
from io import StringIO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

@shared_task
def calculate_credit_score(user_id):
    try:
        user = User.objects.get(id=user_id)
        csv_url = user.csv_file_url
        logger.info(f"csv_url: {csv_url}")

        response = requests.get(csv_url)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))

        if 'transaction_type' not in df.columns or 'amount' not in df.columns:
            raise ValueError("CSV must contain 'transaction_type' and 'amount' columns")

        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

        credit_sum = df[df['transaction_type'] == 'CREDIT']['amount'].sum()
        debit_sum = df[df['transaction_type'] == 'DEBIT']['amount'].sum()

        total_balance = credit_sum - debit_sum

        if total_balance >= 10_00_000:
            credit_score = 900
        elif total_balance <= 1_00_000:
            credit_score = 300
        else:
            credit_score = 300 + ((total_balance - 1_00_000) // 15_000) * 10
            credit_score = min(credit_score, 900)

        user.credit_score = int(credit_score)
        user.save()
        return {"status": "success", "credit_score": user.credit_score}

    except Exception as e:
        logger.error(f"Failed to calculate credit score for user {user_id}: {str(e)}", exc_info=True)
        raise e

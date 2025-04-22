from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import logging
from transformers import pipeline

# تنظیم لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_fashion_comments(**kwargs):
    try:
        logger.info("Fetching comments from external API...")
        response = requests.get("https://jsonplaceholder.typicode.com/comments")
        response.raise_for_status()
        comments = response.json()

        logger.info(f"Fetched {len(comments)} comments from API")

        # محدود کردن به 10 کامنت برای تست
        comments = comments[:10]

        if not comments:
            logger.warning("No comments fetched from API")
            return

        logger.info(f"Pushing {len(comments)} comments to XCom")
        kwargs['ti'].xcom_push(key='fashion_comments', value=comments)

    except requests.RequestException as e:
        logger.error(f"Error fetching comments from API: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error in fetch_fashion_comments: {str(e)}", exc_info=True)
        raise


def save_comments_to_db(**kwargs):
    try:
        logger.info("Pulling comments data from XCom...")
        comments_data = kwargs['ti'].xcom_pull(task_ids='fetch_comments', key='fashion_comments')

        if not comments_data:
            logger.warning("No comments data to save")
            return

        logger.info(f"Processing {len(comments_data)} comment records")
        hook = PostgresHook(postgres_conn_id='postgres_conn')
        logger.info("Attempting to connect to PostgreSQL...")
        with hook.get_conn() as conn:
            with conn.cursor() as cursor:
                logger.info("Successfully connected to PostgreSQL")
                comment_ids = []
                for data in comments_data:
                    comment = data.get('body')
                    if comment:
                        logger.info(f"Inserting comment: {comment[:50]}...")
                        cursor.execute(
                            "INSERT INTO fashion_comments (comment) VALUES (%s) RETURNING id",
                            (comment,)
                        )
                        comment_id = cursor.fetchone()[0]
                        comment_ids.append(comment_id)
                    else:
                        logger.warning(f"Skipping record with missing comment: {data}")
                conn.commit()
                logger.info("Database changes committed")
                kwargs['ti'].xcom_push(key='comment_ids', value=comment_ids)

    except Exception as e:
        logger.error(f"Error in save_comments_to_db: {str(e)}", exc_info=True)
        raise


def analyze_sentiment(**kwargs):
    try:
        logger.info("Pulling comments data from XCom...")
        comments_data = kwargs['ti'].xcom_pull(task_ids='fetch_comments', key='fashion_comments')
        comment_ids = kwargs['ti'].xcom_pull(task_ids='save_comments', key='comment_ids')

        if not comments_data or not comment_ids:
            logger.warning("No comments data or IDs to analyze")
            return

        logger.info(f"Analyzing sentiment for {len(comments_data)} comments")
        sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

        results = []
        for comment, comment_id in zip(comments_data, comment_ids):
            comment_text = comment.get('body')
            if comment_text:
                logger.info(f"Analyzing comment: {comment_text[:50]}...")
                result = sentiment_analyzer(comment_text)[0]
                sentiment = result['label'].lower()  # 'POSITIVE' or 'NEGATIVE'
                score = result['score']
                logger.info(f"Sentiment: {sentiment}, Score: {score}")
                results.append((comment_id, sentiment))
            else:
                logger.warning(f"Skipping comment with missing text: {comment}")

        logger.info("Saving sentiment results to database...")
        hook = PostgresHook(postgres_conn_id='postgres_conn')
        with hook.get_conn() as conn:
            with conn.cursor() as cursor:
                for comment_id, sentiment in results:
                    cursor.execute(
                        "INSERT INTO sentiment_analysis (comment_id, sentiment) VALUES (%s, %s)",
                        (comment_id, sentiment)
                    )
                conn.commit()
                logger.info("Sentiment analysis results committed")

    except Exception as e:
        logger.error(f"Error in analyze_sentiment: {str(e)}", exc_info=True)
        raise


# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 4, 21),
    'retries': 1,
}

# Define the DAG
with DAG(
        dag_id='fashion_pipeline',
        default_args=default_args,
        description='Fetch fashion comments, save to PostgreSQL, and analyze sentiment',
        schedule_interval=None,
        catchup=False,
) as dag:
    fetch_comments = PythonOperator(
        task_id='fetch_comments',
        python_callable=fetch_fashion_comments,
        provide_context=True,
    )

    save_comments = PythonOperator(
        task_id='save_comments',
        python_callable=save_comments_to_db,
        provide_context=True,
    )

    analyze_sentiment_task = PythonOperator(
        task_id='analyze_sentiment',
        python_callable=analyze_sentiment,
        provide_context=True,
    )

    fetch_comments >> save_comments >> analyze_sentiment_task
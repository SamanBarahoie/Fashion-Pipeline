# Fashion Pipeline Project

This project is a data pipeline built with Apache Airflow, PostgreSQL, and Docker to fetch comments from an external API, store them in a PostgreSQL database, and perform sentiment analysis using a machine learning model. The pipeline is designed for processing fashion-related comments (or similar textual data) and analyzing their sentiment (positive or negative).

---

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Running the Pipeline](#running-the-pipeline)
- [Verifying Results](#verifying-results)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

The `fashion_pipeline` project automates the process of:

- Fetching comments from a public API: `https://jsonplaceholder.typicode.com/comments`
- Storing the comments in a PostgreSQL database (`fashion_comments` table)
- Analyzing sentiment using a pre-trained model (`distilbert-base-uncased-finetuned-sst-2-english`)
- Saving the results to a `sentiment_analysis` table

Technologies used: Apache Airflow, PostgreSQL, Docker, Hugging Face Transformers.

---

## Features

- **Data Ingestion:** Fetch up to 10 comments from an API
- **Data Storage:** Store comments with timestamps in PostgreSQL
- **Sentiment Analysis:** Classify comments as positive or negative
- **Orchestration:** Workflow managed with Airflow DAGs
- **Containerization:** All services run in Docker for portability

---

## Architecture

### Components:

- **Apache Airflow**: Orchestrates the pipeline
  - `fetch_comments`: Retrieves comments from API
  - `save_comments`: Saves to `fashion_comments`
  - `analyze_sentiment`: Analyzes and stores to `sentiment_analysis`
- **PostgreSQL**: Stores raw and analyzed data
- **Docker**: Hosts all services in containers
- **Transformer Model**: Pre-trained sentiment model from Hugging Face

---

## Prerequisites

- Docker & Docker Compose
- Git (optional)
- Internet connection
- 4GB RAM, 10GB disk

---

## Project Structure

```
fashion_pipeline/
├── dags/
│   └── fashion_pipeline.py        # DAG definition
├── init.sql                       # DB schema
├── docker-compose.yml             # Docker services
└── README.md                      # Project documentation
```

---

## Setup Instructions

### 1. Clone the Repository (Optional)
```bash
git clone <repository-url>
cd fashion_pipeline
```

### 2. Create Project Files
Ensure these files exist: `docker-compose.yml`, `init.sql`, `dags/fashion_pipeline.py`.

### 3. Start Docker Services
```bash
docker-compose up -d
docker ps  # Verify services are running
```

### 4. Install Python Dependencies
```bash
docker exec -it fashion_pipeline-airflow-webserver-1 bash
pip install requests psycopg2-binary transformers torch
exit
```

### 5. Configure Airflow Connection

- Go to [http://localhost:8080](http://localhost:8080)
- Login: `admin` / `admin`
- Navigate to **Admin > Connections**
- Create a new Postgres connection:

| Field     | Value        |
|-----------|--------------|
| Conn Id   | postgres_conn |
| Host      | postgres      |
| Schema    | fashion_db    |
| Login     | user          |
| Password  | password      |
| Port      | 5432          |

---

## Running the Pipeline

- In Airflow UI, enable and **Trigger DAG**
- Or via CLI:
```bash
docker exec -it fashion_pipeline-airflow-webserver-1 airflow dags trigger fashion_pipeline
```

Monitor the run in **Graph View**.

---

## Verifying Results

### Check Logs
```bash
docker exec -it fashion_pipeline-airflow-webserver-1 bash
cat /opt/airflow/logs/fashion_pipeline/fetch_comments/<log_file>
cat /opt/airflow/logs/fashion_pipeline/save_comments/<log_file>
cat /opt/airflow/logs/fashion_pipeline/analyze_sentiment/<log_file>
```

### Check Database

```bash
docker exec -it fashion_pipeline-postgres-1 psql -U user -d fashion_db -c "SELECT * FROM fashion_comments;"
docker exec -it fashion_pipeline-postgres-1 psql -U user -d fashion_db -c "SELECT * FROM sentiment_analysis;"
```

---

## Troubleshooting

### ModuleNotFoundError: transformers
```bash
docker exec -it fashion_pipeline-airflow-webserver-1 bash
pip install transformers torch
docker-compose restart
```

### PostgreSQL Connection Error
```python
from airflow.providers.postgres.hooks.postgres import PostgresHook
hook = PostgresHook(postgres_conn_id='postgres_conn')
hook.get_conn()
```

### Memory Issues
Edit `docker-compose.yml`:
```yaml
airflow-webserver:
  deploy:
    resources:
      limits:
        memory: 4g
```

Restart:
```bash
docker-compose down && docker-compose up -d
```

### API Unavailable
```bash
docker exec -it fashion_pipeline-airflow-webserver-1 ping jsonplaceholder.typicode.com
```

---

## Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Create a Pull Request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
```


# Production-Ready ML Model Serving with FastAPI

## Introduction

This lab teaches you to build a production-ready sentiment analysis API from scratch. You will progressively add authentication (JWT), database persistence (PostgreSQL + Alembic), ML model serving (scikit-learn), and production features (Nginx load balancing, TLS, rate limiting, async processing with Celery/Redis).

![dia1]()

The approach emphasizes learning by doing. You will predict outcomes, complete code scaffolds, and deliberately break things to understand why production patterns matter.

**Prerequisites:** Basic Python knowledge, familiarity with REST API concepts, and Docker fundamentals.


## Learning Objectives

By the end of this lab, you will be able to:

1. Design a modular FastAPI application with proper separation of concerns
2. Implement JWT-based authentication with password hashing
3. Configure PostgreSQL database connections with SQLAlchemy ORM
4. Create and run database migrations using Alembic
5. Build and serve a machine learning model for real-time predictions
6. Implement background task processing with Celery and Redis
7. Configure Nginx as a reverse proxy with load balancing and TLS
8. Apply rate limiting to protect API endpoints
9. Create comprehensive health checks for production monitoring
10. Deploy a multi-container application using Docker Compose


## Prologue: The Challenge

You join the platform safety team at a social media company. User comments require automated analysis for sentiment detection. Currently, moderators review everything manually, and the backlog grows daily.

Your task is to build a Sentiment Analysis API that:
- Authenticates users securely
- Analyzes text sentiment in real-time
- Processes batch requests asynchronously
- Scales horizontally behind a load balancer
- Handles failures gracefully

The system must be production-ready: secure, scalable, and observable.


## Environment Setup

Update your system and install required packages:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
```

Create the project directory structure:

```bash
mkdir -p sentiment-api/backend/app/{core,db,routers,dependencies,schemas,services,middleware}
mkdir -p sentiment-api/{nginx/ssl,models,alembic/versions}
cd sentiment-api
```

Verify Docker is running:

```bash
docker --version
docker compose --version
```

Expected output format:
```
Docker version 24.x.x
Docker Compose version v2.x.x
```
## Project Structure
```
sentiment-api/
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── Makefile
├── setup.sh
├── test_api.sh
├── init_db.py
├── train_model.py
├── alembic.ini
│
├── models/
│   └── sentiment_model.pkl
│
├── logs/
│   └── app.log
│
├── nginx/
│   ├── nginx.conf
│   └── ssl/
│       ├── cert.pem
│       └── key.pem
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── YYYYMMDD_HHMM_xxxxx_initial_migration.py
│
└── backend/
    ├── __init__.py
    └── app/
        ├── __init__.py
        ├── main.py
        │
        ├── core/
        │   ├── __init__.py
        │   ├── config.py
        │   ├── security.py
        │   └── logging.py
        │
        ├── db/
        │   ├── __init__.py
        │   ├── models.py
        │   └── session.py
        │
        ├── routers/
        │   ├── __init__.py
        │   ├── auth.py
        │   ├── users.py
        │   ├── protected.py
        │   ├── sentiment.py
        │   └── health.py
        │
        ├── dependencies/
        │   ├── __init__.py
        │   └── auth.py
        │
        ├── schemas/
        │   └── __init__.py
        │
        ├── services/
        │   └── __init__.py
        │
        └── middleware/
            └── __init__.py
```

### File Descriptions
#### Root Files
`.env` - Environment variables (DB credentials, JWT secret, Redis URL)\
`.env.example` - Template for environment variables\
`.gitignore` - Git ignore rules\
`docker-compose.yml` - Orchestrates all services (DB, Redis, API, Nginx, Celery)\
`Dockerfile` - Builds API container image\
`requirements.txt` - Python dependencies\
`Makefile` - Convenient commands (build, up, down, test)\
`setup.sh` - Automated setup script\
`test_api.sh` - API testing script\
`init_db.py` - Creates database tables\
`train_model.py` - Trains sentiment analysis ML model\
`alembic.ini` - Alembic migration configuration

#### `models/`
`sentiment_model.pkl` - Trained scikit-learn model

#### `logs/`
`app.log` - Application logs

#### `nginx`
`nginx.conf` - Reverse proxy, TLS, rate limiting, load balancing
`ssl/cert.pem `- SSL certificate
`ssl/key.pem` - SSL private key

#### `alembic/`
`env.py` - Alembic environment configuration
`script.py.mako` - Migration file template
`versions/*.py` - Database migration files

#### `backend/app/`
`main.py` - FastAPI app entry + Celery configuration

#### `backend/app/core/`
`config.py` - Settings (DB URL, JWT secret, Redis URL)
`security.py` - JWT token creation/validation, password hashing
`logging.py` - Logging configuration

#### `backend/app/db/`
`models.py` - SQLAlchemy models (User, SentimentRequest, BackgroundTask)
`session.py` - Database connection & session management

#### `backend/app/routers/`
`auth.py` - Register & login endpoints
`users.py` - User profile endpoints
`protected.py` - Test authentication
`sentiment.py` - ML sentiment analysis (sync + async)
`health.py` - Health check endpoint

#### `backend/app/dependencies/`
`auth.py` - JWT authentication dependencies (get_current_user)

#### `backend/app/schemas/`
`init.py` - Pydantic validation schemas placeholder

#### `backend/app/services/`
Business logic services placeholder

#### `backend/app/middleware/`
Middleware placeholder

## Chapter 1: Foundation Setup

The foundation determines how the entire application behaves. Configuration errors at this stage propagate through every component. Proper environment management prevents secrets from leaking into version control.

### 1.1 What You Will Build

- Environment configuration file with database and JWT settings
- Python dependencies manifest
- Dockerfile for containerization
- Docker Compose for service orchestration

### 1.2 Think First: Configuration Management

**Question:** Why should database credentials be stored in environment variables rather than hardcoded in source files?

<details>
<summary>Click to review</summary>

Environment variables allow different credentials per deployment environment (development, staging, production) without code changes. Hardcoded credentials get committed to version control, creating security vulnerabilities. Environment variables can be injected by container orchestrators like Kubernetes without rebuilding images.

</details>

### 1.3 Implementation

Create the `.env` file from the example with the following configuration.
```bash
cp .env.example .env
```
Complete the blanks:

```bash
# Database Configuration
POSTGRES_USER=sentiment_user
POSTGRES_PASSWORD=sentiment_pass_123
POSTGRES_DB=sentiment_db
POSTGRES_HOST=___  # Q1: What hostname resolves to the database container?
POSTGRES_PORT=5432
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=___  # Q2: What algorithm does JWT use for signing?
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# Application
DEBUG=True
```

**Hints:**
- Q1: Docker Compose service names become hostnames within the network
- Q2: Common symmetric algorithms include HS256, HS384, HS512

<details>
<summary>Click to see solution</summary>

```bash
POSTGRES_HOST=db
ALGORITHM=HS256
```

</details>

Create `requirements.txt`:

```txt
# FastAPI and server
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Machine Learning
scikit-learn==1.4.0
pandas==2.2.0
numpy==1.26.3
joblib==1.3.2

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.2

# Rate Limiting
slowapi==0.1.9

# Background Tasks
celery==5.3.6
redis==5.0.1

# Utilities
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# HTTP Client
httpx==0.26.0
requests==2.31.0
```

**What this does:** Lists all Python packages with pinned versions. Pinning versions ensures consistent builds across environments.

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY models/ ./models/
COPY init_db.py .
COPY train_model.py .

# Create models directory if it doesn't exist
RUN mkdir -p models

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**What this does:** Defines how to build the container image. It starts from Python 3.11, installs dependencies, copies code, and runs the FastAPI server.

**Why:** Containers ensure the app runs identically everywhere - your machine, CI/CD, production.

Create `docker-compose.yml`:

```yaml
services:
  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: sentiment_db
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - sentiment_network
    restart: unless-stopped

  # Redis for caching and message queue
  redis:
    image: redis:7-alpine
    container_name: sentiment_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - sentiment_network
    restart: unless-stopped

  # API Instance 1
  api1:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: sentiment_api1
    environment:
      - INSTANCE_ID=API-1
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=${ALGORITHM}
      - ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_URL=${REDIS_URL}
    ports:
      - "8001:8000"
    volumes:
      - ./backend:/app/backend
      - ./models:/app/models
      - ./alembic:/app/alembic
      - ./alembic.ini:/app/alembic.ini
      - ./init_db.py:/app/init_db.py
      - ./train_model.py:/app/train_model.py
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - sentiment_network
    restart: unless-stopped
    command: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

  # API Instance 2 (for load balancing)
  api2:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: sentiment_api2
    environment:
      - INSTANCE_ID=API-2
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=${ALGORITHM}
      - ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_URL=${REDIS_URL}
    ports:
      - "8002:8000"
    volumes:
      - ./backend:/app/backend
      - ./models:/app/models
      - ./alembic:/app/alembic
      - ./alembic.ini:/app/alembic.ini
      - ./init_db.py:/app/init_db.py
      - ./train_model.py:/app/train_model.py
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - sentiment_network
    restart: unless-stopped
    command: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    container_name: sentiment_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api1
      - api2
    networks:
      - sentiment_network
    restart: unless-stopped

  # Celery Worker for background tasks
  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: sentiment_celery_worker
    env_file:
      - .env
    volumes:
      - ./backend:/app/backend
      - ./models:/app/models
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - sentiment_network
    restart: unless-stopped
    command: celery -A backend.app.main.celery_app worker --loglevel=info

volumes:
  postgres_data:

networks:
  sentiment_network:
    driver: bridge
```

**What this does:** Defines 6 services that work together:

| Service | Purpose |
|---------|---------|
| `db` | PostgreSQL database for storing users and requests |
| `redis` | Message broker for Celery and caching |
| `api1`, `api2` | Two FastAPI instances for horizontal scaling |
| `nginx` | Load balancer distributing traffic between API instances |
| `celery_worker` | Processes background tasks (batch analysis) |

**Why:** Docker Compose orchestrates multiple containers as a single application. Services communicate via the `sentiment_network`.

**How it works:**
1. `depends_on` ensures database and Redis start before API
2. `healthcheck` verifies services are ready before starting dependents
3. `volumes` mount code for hot-reloading during development
4. Environment variables come from `.env` file

### 1.4 Understanding the Code

Match each Dockerfile instruction to its purpose:

| Instruction | Purpose (A-E) |
|-------------|---------------|
| `WORKDIR /app` | ___ |
| `ENV PYTHONPATH=/app` | ___ |
| `EXPOSE 8000` | ___ |
| `--no-cache-dir` | ___ |
| `PYTHONUNBUFFERED=1` | ___ |

**Options:**
- A: Documents which port the container listens on
- B: Sets the directory for subsequent commands
- C: Ensures Python output appears immediately in logs
- D: Reduces image size by not storing pip cache
- E: Allows imports from the app directory

<details>
<summary>Click to see answers</summary>

| Instruction | Answer |
|-------------|--------|
| `WORKDIR /app` | B |
| `ENV PYTHONPATH=/app` | E |
| `EXPOSE 8000` | A |
| `--no-cache-dir` | D |
| `PYTHONUNBUFFERED=1` | C |

</details>

### 1.5 Checkpoint

**Self-Assessment:**
- [ ] `.env` file contains database credentials
- [ ] `requirements.txt` lists all dependencies with versions
- [ ] `Dockerfile` uses Python 3.11 slim image
- [ ] You can explain why environment variables store secrets


## Chapter 2: Infrastructure with Nginx

Before starting the containers, we need to configure Nginx. The `docker-compose.yml` references the Nginx service, so without this configuration, the containers will fail to start.

Nginx acts as a reverse proxy, handling TLS termination, load balancing, and rate limiting.

#### Real-World Scenario: The Black Friday Crash

Your sentiment analysis API has been running smoothly for months on a single server. Then Black Friday arrives—traffic spikes 10x as e-commerce platforms flood your API with product review analysis requests. Your single server maxes out at 100% CPU, response times climb from 50ms to 30 seconds, and eventually the server crashes. Customers are furious.

The solution? **Horizontal scaling with load balancing.** Instead of one powerful server, you run multiple API instances behind Nginx. When traffic spikes, Nginx distributes requests across all instances using algorithms like "least connections" (sending requests to the least busy server). Rate limiting prevents any single client from overwhelming the system. TLS termination at Nginx means your API servers don't waste CPU on encryption. The result: your API handles 10x traffic by adding more instances, not bigger servers.

### 2.1 Think First: Load Balancing Algorithms

Match each algorithm to its behavior:

| Algorithm | Behavior (A-C) |
|-----------|----------------|
| Round Robin | ___ |
| Least Connections | ___ |
| IP Hash | ___ |

**Options:**
- A: Routes to server with fewest active connections
- B: Routes same client to same server (session affinity)
- C: Routes to each server in sequence

<details>
<summary>Click to review</summary>

| Algorithm | Answer |
|-----------|--------|
| Round Robin | C |
| Least Connections | A |
| IP Hash | B |

</details>

### 2.2 Implementation

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        least_conn;
        server api1:8000;
        server api2:8000;
    }

    limit_req_zone $binary_remote_addr zone=general:10m rate=60r/m;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    server {
        listen 80;
        server_name localhost;
        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl;
        http2 on;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;

        location /api/v1/auth/login {
            limit_req zone=login burst=3 nodelay;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /api/ {
            limit_req zone=general burst=10 nodelay;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location / {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
        }
    }
}
```

**What this does:** Configures Nginx as reverse proxy with security features.

**Why:** Nginx handles concerns the API should not: TLS encryption, load balancing, rate limiting.

**How it works:**

| Section | Purpose |
|---------|---------|
| `upstream api_backend` | Defines backend servers for load balancing |
| `least_conn` | Routes to server with fewest active connections |
| `limit_req_zone` | Creates rate limiting buckets per IP address |
| `listen 80` | Redirects HTTP to HTTPS |
| `listen 443 ssl` | Handles HTTPS traffic |
| `ssl_protocols TLSv1.2 TLSv1.3` | Only allows secure TLS versions |
| `add_header` | Adds security headers to responses |
| `proxy_pass` | Forwards requests to API servers |

**Rate limits:**
- Login: 5 requests/minute (prevents brute force)
- General API: 60 requests/minute

### 2.3 Generate SSL Certificates

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/CN=localhost"
```

**What this does:** Creates a self-signed SSL certificate for HTTPS.

**Why:** HTTPS encrypts traffic between client and server. Self-signed certificates work for development; production uses certificates from a CA.

**How it works:** OpenSSL generates a 2048-bit RSA key pair valid for 365 days. The `-nodes` flag means no password protection (for automated startup).


### 2.3 Generate SSL
#### What is SSL/TLS?
SSL (Secure Sockets Layer)—and its modern, more secure successor, TLS (Transport Layer Security)—is the standard technology for keeping an internet connection secure.

It does two main things:
- Encryption: It scrambles the data sent between a user and a website (like passwords or credit card numbers) so hackers can't read it.
- Authentication: It ensures that the server you are talking to is actually who it claims to be.

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

**Breaking Down the Command**
The command you provided uses OpenSSL, a robust toolkit for the TLS and SSL protocols. Here is what each part does:
* `openssl req`: This starts the "request" process for a certificate.
* `-x509`: This tells OpenSSL to create a self-signed certificate rather than a certificate signing request (CSR). X.509 is the standard format for public-key certificates.
* `-nodes`: Short for "no DES." This means the private key will not be encrypted with a password. This is common for web servers (like Nginx) so they can restart automatically without someone typing in a password every time.
* `-days 365`: Sets the expiration date. In this case, your certificate is valid for one year.
* `-newkey rsa:2048`: Generates a new certificate and a new RSA key at the same time. 2048 refers to the key length in bits—the current industry standard for security.
* `-keyout .../key.pem`: Specifies where to save the Private Key. Keep this secret!
* `-out .../cert.pem`: Specifies where to save the Public Certificate. This is what the browser sees.
* `-subj "..."`: This skips the interactive prompts by providing the certificate details (Country, State, Location, etc.) directly in the command. `CN=localhost` identifies the "Common Name" or domain this certificate belongs to.

### 2.5 Start the Containers

Now that all infrastructure is configured, build and run the containers:
```bash
docker compose up -d --build
```

This may take some time to build the image the first time. After creation, check what containers are running:
```bash
docker ps
```
You should see containers for: `db`, `redis`, `api1`, `api2`, `nginx`, and `celery_worker`.

### 2.6 Checkpoint

**Self-Assessment:**
- [ ] `nginx/nginx.conf` is created with load balancing configuration
- [ ] SSL certificates are generated in `nginx/ssl/`
- [ ] All containers are running (`docker ps` shows 6 containers)
- [ ] You can explain why Nginx handles TLS instead of the API


## Chapter 3: Database Layer

The database layer persists user accounts, sentiment analysis requests, and background task status. Proper ORM configuration prevents SQL injection and enables database-agnostic code.

### 3.1 What You Will Build

- SQLAlchemy ORM models for Users, SentimentRequests, and BackgroundTasks
- Database session management with connection pooling
- Pydantic settings for configuration management

### 3.2 Think First: Connection Pooling

**Question:** A production API receives 1000 requests per second. Each request needs a database connection. What problem arises if each request creates a new connection?

<details>
<summary>Click to review</summary>

Creating connections is expensive (TCP handshake, authentication, memory allocation). Without pooling, 1000 requests create 1000 connections, overwhelming the database server. Connection pooling maintains a fixed set of reusable connections (e.g., 10-30), dramatically reducing overhead. Requests wait for an available connection rather than creating new ones.

</details>

### 3.3 Implementation

Create `backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Sentiment Analysis API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = ___  # Q1: Token validity in minutes

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://redis:6379/0"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:8000"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

**What this does:** Loads configuration from environment variables and `.env` file using Pydantic.

**Why:** Centralizes all settings in one place. Pydantic validates types automatically (e.g., ensures `POSTGRES_PORT` is an integer).

**How it works:** When `Settings()` is instantiated, Pydantic reads the `.env` file and environment variables, mapping them to class attributes.

**Hint:** The `.env` file sets `ACCESS_TOKEN_EXPIRE_MINUTES=30`.

<details>
<summary>Click to see solution</summary>

```python
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

</details>

Create `backend/app/db/models.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=___)  # Q1: Should new users be active?
    is_superuser = Column(Boolean, default=___)  # Q2: Should new users be superusers?
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SentimentRequest(Base):
    __tablename__ = "sentiment_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    text = Column(Text, nullable=False)
    sentiment = Column(String(50))
    confidence = Column(Float)
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class BackgroundTask(Base):
    __tablename__ = "background_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True)
    user_id = Column(Integer, index=True)
    task_type = Column(String(100))
    status = Column(String(50), default="pending")
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

<details>
<summary>Click to see solution</summary>

```python
is_active = Column(Boolean, default=True)
is_superuser = Column(Boolean, default=False)
```

New users should be active by default (to allow login) but not superusers (principle of least privilege).

</details>

**What this does:** Defines three database tables using SQLAlchemy ORM:
- `User`: Stores account info with hashed passwords
- `SentimentRequest`: Logs each prediction with results
- `BackgroundTask`: Tracks async batch processing jobs

**Why:** ORM maps Python classes to database tables. You write Python, SQLAlchemy generates SQL.

**How it works:** `Base.metadata` collects all table definitions. `index=True` speeds up queries on that column. `default=datetime.utcnow` auto-sets timestamps.

Create `backend/app/db/session.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.app.core.config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=10,        # Maintain 10 connections
    max_overflow=20      # Allow 20 additional connections under load
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**What this does:** Creates a database connection pool and provides sessions to API endpoints.

**Why:** Connection pooling reuses connections instead of creating new ones per request. This dramatically improves performance.

**How it works:**
- `pool_size=10`: Keeps 10 connections ready
- `pool_pre_ping=True`: Tests connections before use (handles stale connections)
- `yield`: Provides session to endpoint, then closes it after response

### 3.4 Understanding the Code

**Scenario:** The `get_db` function uses `yield` instead of `return`. A developer changes it to:

```python
def get_db():
    db = SessionLocal()
    return db
```

**Question:** What problem does this create?

<details>
<summary>Click to review</summary>

Without `yield` and the `finally` block, database sessions never close. Each request opens a new connection that remains open indefinitely. The connection pool exhausts quickly, causing "too many connections" errors. The `yield` pattern ensures cleanup runs after each request, even if an exception occurs.

</details>

### 3.5 Database Migrations with Alembic

#### What is Alembic?

Alembic is a database migration tool for SQLAlchemy. It tracks changes to your database schema over time, allowing you to:
- Version control your database schema alongside your code
- Apply incremental changes to production databases safely
- Roll back changes if something goes wrong
- Collaborate with team members without database conflicts

**Why not just use `Base.metadata.create_all()`?**

While `create_all()` works for initial setup, it cannot:
- Add columns to existing tables
- Modify column types or constraints
- Remove columns or tables
- Track what changes have been applied

Alembic solves all these problems by generating migration scripts that describe exactly what changes to make.

#### 3.5.1 Alembic Project Structure

```
sentiment-api/
├── alembic.ini              # Main configuration file
└── alembic/
    ├── env.py               # Migration environment setup
    ├── script.py.mako       # Template for new migrations
    └── versions/            # Migration files live here
        └── 20260207_1040_48bbdd4ac281_initial_migration.py
```

#### 3.5.2 Initialize Alembic

If starting a new project, initialize Alembic with:

```bash
alembic init alembic
```

This creates the `alembic/` directory and `alembic.ini` file.

#### 2.5.3 Configure alembic.ini

The `alembic.ini` file contains Alembic's configuration. Key settings:

```ini
[alembic]
# Path to migration scripts
script_location = alembic

# Template for migration file names (includes timestamp)
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# Add current directory to Python path
prepend_sys_path = .

# Database connection URL (overridden by env.py in our setup)
sqlalchemy.url = postgresql://sentiment_user:sentiment_pass_123@db:5432/sentiment_db
```

**What this does:**
- `script_location`: Tells Alembic where migration files are stored
- `file_template`: Creates readable filenames like `20260207_1040_abc123_add_user_table.py`
- `prepend_sys_path`: Ensures imports work correctly

#### 3.5.4 Configure env.py

The `env.py` file connects Alembic to your SQLAlchemy models. Create `alembic/env.py`:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your models and settings
from backend.app.db.models import Base
from backend.app.core.config import settings

# Alembic Config object
config = context.config

# Setup Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override database URL from application settings
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

# Point to your models' metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for reviewing changes before applying them.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Connects to the database and applies migrations directly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**What this does:**
- Imports your SQLAlchemy models so Alembic knows your schema
- Uses `settings.DATABASE_URL` from your config (not hardcoded in `alembic.ini`)
- Sets `target_metadata = Base.metadata` to enable autogenerate

**Why:** This setup allows Alembic to compare your Python models against the actual database and generate migration scripts automatically.

#### 3.5.5 Create Migrations

**Generate a new migration automatically:**

```bash
# Inside the container
docker compose exec api1 alembic revision --autogenerate -m "initial migration"
```

**What this does:**
1. Connects to the database
2. Compares `Base.metadata` (your models) with the actual database schema
3. Generates a migration file with the differences

**Example generated migration file:**

```python
"""initial migration

Revision ID: 48bbdd4ac281
Revises:
Create Date: 2026-02-07 10:40:12.989783
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = '48bbdd4ac281'
down_revision = None  # First migration has no parent
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply changes to database."""
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    """Revert changes (rollback)."""
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
```

**Key concepts:**
- `revision`: Unique ID for this migration
- `down_revision`: Links to previous migration (creates a chain)
- `upgrade()`: Applies changes (run with `alembic upgrade`)
- `downgrade()`: Reverts changes (run with `alembic downgrade`)

#### 3.5.6 Run Migrations

**Apply all pending migrations:**

```bash
docker compose exec api1 alembic upgrade head
```

**Other useful commands:**

| Command | Purpose |
|---------|---------|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic upgrade +1` | Apply next migration only |
| `alembic downgrade -1` | Revert last migration |
| `alembic downgrade base` | Revert all migrations |
| `alembic current` | Show current revision |
| `alembic history` | Show migration history |
| `alembic show <revision>` | Show details of a specific migration |

#### 3.5.7 Migration Workflow

When you modify your SQLAlchemy models:

1. **Edit your models** in `backend/app/db/models.py`
   ```python
   # Example: Add a new column
   class User(Base):
       # ... existing columns ...
       phone_number = Column(String(20), nullable=True)  # New!
   ```

2. **Generate migration**
   ```bash
   docker compose exec api1 alembic revision --autogenerate -m "add phone number to users"
   ```

3. **Review the generated migration** in `alembic/versions/`
   - Always check autogenerated migrations before applying
   - Alembic may miss some changes or generate incorrect SQL

4. **Apply the migration**
   ```bash
   docker compose exec api1 alembic upgrade head
   ```

5. **Commit both** the model changes and migration file to version control

#### 3.5.8 Think First: Migration Safety

**Question:** You need to rename a column from `username` to `user_name` in production. What problem might `alembic revision --autogenerate` create?

<details>
<summary>Click to review</summary>

Autogenerate cannot detect renames. It will generate a migration that:
1. Drops the `username` column (losing all data!)
2. Creates a new `user_name` column

**Solution:** Manually write the migration using `op.alter_column()`:

```python
def upgrade():
    op.alter_column('users', 'username', new_column_name='user_name')

def downgrade():
    op.alter_column('users', 'user_name', new_column_name='username')
```

Always review autogenerated migrations before applying to production!

</details>

### 3.6 Checkpoint

**Self-Assessment:**
- [ ] Config class loads settings from `.env` file
- [ ] User model includes password hash (not plain password)
- [ ] Session uses connection pooling (pool_size=10)
- [ ] You can explain why `yield` is used in `get_db`
- [ ] You understand how Alembic migrations work


## Chapter 4: Security Layer

### Real-World Scenario

Imagine you're the lead developer at a growing fintech startup. One morning, you receive an urgent call: your competitor just suffered a massive data breach. Attackers gained access to their database and leaked millions of user passwords online. The cause? They stored passwords in plain text.

Your CEO asks a simple question: "Could this happen to us?"

This scenario plays out regularly across the industry. In 2021, a major social platform exposed 533 million user records. In 2023, a popular password manager was breached, putting encrypted vaults at risk. The common thread? Security was an afterthought, not a foundation.

By the end, you'll understand not just *how* to implement security, but *why* each decision matters when real users trust your system with their data.

### 4.1 What You Will Build

- Password hashing with bcrypt
- JWT token creation and validation
- OAuth2 password bearer authentication flow

### 4.2 Think First: Password Storage

**Question:** A database breach exposes all user records. Why is storing password hashes safer than storing encrypted passwords?

<details>
<summary>Click to review</summary>

Encryption is reversible with the key. If attackers obtain the encryption key (which must be stored somewhere), they decrypt all passwords instantly. Hashes are one-way functions. Even with the hashing algorithm known, attackers must brute-force each password individually. Bcrypt adds per-password salts and intentional slowness, making attacks computationally expensive.

</details>

### 4.3 Implementation

#### What is JWT?

JSON Web Token (JWT) is an open standard for securely transmitting information between parties as a signed token. It contains three parts: a header (algorithm), payload (user data like username), and a signature. The server signs tokens with a secret key, and any server instance can verify them without storing session data. This makes JWT ideal for stateless, horizontally-scaled APIs.

#### Bcrypt

Bcrypt is a password hashing algorithm designed specifically for securing passwords. Unlike regular hash functions, bcrypt adds a random "salt" to each password (preventing rainbow table attacks) and is intentionally slow (making brute-force attacks impractical). It's a one-way function—you cannot reverse a hash back to the original password.


Create `backend/app/core/security.py`:

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from backend.app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.___(plain_password, hashed_password)  # Q1: Which method?


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.___(password)  # Q2: Which method?


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return ___  # Q3: What indicates decoding failure?
```

**Hints:**
- Q1, Q2: CryptContext provides `verify` and `hash` methods
- Q3: Python convention for "no result"

<details>
<summary>Click to see solution</summary>

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

</details>

**What this does:** Provides four security functions:
- `verify_password`: Checks if login password matches stored hash
- `get_password_hash`: Converts plain password to bcrypt hash
- `create_access_token`: Generates JWT with expiration time
- `decode_access_token`: Validates and extracts data from JWT

**Why:** Passwords must never be stored in plain text. JWTs allow stateless authentication - no server-side session storage needed.

**How it works:** Bcrypt adds random salt to each password, making identical passwords produce different hashes. JWT encodes user data + expiration, signed with SECRET_KEY.

#### OAuth2PasswordBearer

OAuth2PasswordBearer is FastAPI's implementation of the OAuth2 "password flow" for authentication. It automatically extracts the JWT token from the `Authorization: Bearer <token>` header in incoming requests. This creates a reusable dependency that protects any endpoint—just add `Depends(get_current_user)` and unauthorized requests are automatically rejected with a 401 error.


Create `backend/app/dependencies/auth.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.db.models import User
from backend.app.db.session import get_db
from backend.app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")  # "sub" is JWT standard for subject
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure the current user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

**What this does:** Extracts and validates user from JWT token in request headers.

**Why:** Protects endpoints by requiring valid authentication. Use `Depends(get_current_active_user)` on any endpoint that needs auth.

**How it works:**
1. `OAuth2PasswordBearer` extracts token from `Authorization: Bearer <token>` header
2. `decode_access_token` verifies signature and extracts username
3. Database lookup finds the user
4. Returns user object or raises 401 error

### 4.4 Understanding the Code

Match each security component to its purpose:

| Component | Purpose (A-E) |
|-----------|---------------|
| `pwd_context.hash()` | ___ |
| `jwt.encode()` | ___ |
| `OAuth2PasswordBearer` | ___ |
| `settings.SECRET_KEY` | ___ |
| `payload.get("sub")` | ___ |

**Options:**
- A: Creates a signed token from data
- B: Converts plain password to irreversible hash
- C: Extracts username from token payload
- D: Defines the authentication scheme for OpenAPI docs
- E: Signs JWT tokens to prevent tampering

<details>
<summary>Click to see answers</summary>

| Component | Answer |
|-----------|--------|
| `pwd_context.hash()` | B |
| `jwt.encode()` | A |
| `OAuth2PasswordBearer` | D |
| `settings.SECRET_KEY` | E |
| `payload.get("sub")` | C |

</details>

### 4.5 Experiment: Token Tampering

After the full system is running, perform this experiment:

1. Login and obtain a valid JWT token
2. Decode the token at jwt.io (do not share production tokens)
3. Modify the username in the payload
4. Re-encode without the secret key
5. Use the modified token in an API request

**Observe:** The request fails with 401 Unauthorized. The signature verification detects tampering.

### 4.6 Checkpoint

**Self-Assessment:**
- [ ] Passwords are hashed with bcrypt, not stored plain
- [ ] JWT tokens include expiration time
- [ ] Token validation checks both signature and expiration
- [ ] You can explain why `SECRET_KEY` must remain secret


## Chapter 5: API Endpoints

Routers organize endpoints by functionality. Pydantic models validate input data before it reaches business logic. Proper HTTP status codes communicate success and failure clearly.

### 5.1 What You Will Build

- Authentication endpoints (register, login)
- User management endpoints
- Protected endpoint demonstrating auth requirement
- Health check endpoints

### 5.2 Think First: Status Codes

**Predict:** What HTTP status code should each scenario return?

| Scenario | Status Code |
|----------|-------------|
| New user created successfully | ___ |
| Login with wrong password | ___ |
| Request to protected endpoint without token | ___ |
| Invalid JSON in request body | ___ |

<details>
<summary>Click to review</summary>

| Scenario | Status Code |
|----------|-------------|
| New user created successfully | 201 Created |
| Login with wrong password | 401 Unauthorized |
| Request to protected endpoint without token | 401 Unauthorized |
| Invalid JSON in request body | 422 Unprocessable Entity |

</details>

### 5.3 Implementation

Create `backend/app/routers/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime

from backend.app.db.models import User
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


class Token(BaseModel):
    access_token: str
    token_type: str


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/register", response_model=UserResponse, status_code=___)  # Q1: Created status
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )

    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token."""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=___,  # Q2: Unauthorized status
            detail="Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

**What this does:** Two endpoints for user authentication:
- `/register`: Creates new user with hashed password
- `/login`: Validates credentials and returns JWT token

**Why:** Registration creates accounts. Login provides tokens for accessing protected endpoints.

**How it works:**
1. `UserRegister` Pydantic model validates input (email format, required fields)
2. Password is hashed before storing
3. `OAuth2PasswordRequestForm` is FastAPI's standard login format
4. Token contains `{"sub": username}` - "sub" is JWT standard for subject

<details>
<summary>Click to see solution</summary>

```python
@router.post("/register", response_model=UserResponse, status_code=201)

# and

raise HTTPException(
    status_code=401,
    detail="Incorrect username or password"
)
```

</details>

Create `backend/app/routers/health.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from backend.app.db.session import get_db
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Check the health of the API and its dependencies."""
    health_status = {
        "status": "healthy",
        "api": "ok",
        "database": "ok",
        "redis": "ok"
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Sentiment Analysis API",
        "version": "1.0.0",
        "docs": "/docs"
    }
```

**What this does:** Provides health monitoring endpoints:
- `/health`: Checks API, database, and Redis status
- `/`: Returns API info and docs link

**Why:** Load balancers use health checks to route traffic only to healthy instances. Operators use them to diagnose issues.

**How it works:** Executes simple queries against each dependency. If any fails, returns `"status": "unhealthy"` with error details.

### 5.4 Checkpoint

**Self-Assessment:**
- [ ] Registration returns 201 status code
- [ ] Login validates password against hash
- [ ] Protected endpoints require valid JWT
- [ ] Health check tests all dependencies


## Chapter 6: ML Model Integration

The sentiment analysis model predicts whether text is positive or negative. Serving ML models in production requires careful consideration of loading time, memory usage, and prediction latency.

#### About the Model: TF-IDF + Naive Bayes

We use a classic yet effective text classification pipeline. **TF-IDF (Term Frequency-Inverse Document Frequency)** converts text into numerical vectors by measuring how important each word is to a document relative to the entire dataset—common words like "the" get low scores, while distinctive words like "amazing" or "terrible" get high scores. **Multinomial Naive Bayes** is a probabilistic classifier that works exceptionally well with text data. It calculates the probability of a text belonging to each class (positive/negative) based on word frequencies. Despite its simplicity, this combination remains a strong baseline that trains in seconds and predicts in milliseconds—perfect for production APIs.

### 6.1 What You Will Build

- Training script for TF-IDF + Naive Bayes classifier
- Sentiment analysis router with sync and async endpoints
- Batch processing with background tasks

### 6.2 Think First: Model Loading

**Question:** A sentiment model takes 5 seconds to load from disk. If the model loads on every request, what is the minimum response time for each prediction?

<details>
<summary>Click to review</summary>

At least 5 seconds per request, just for loading. This is unacceptable for production. The model should load once at startup and remain in memory. Subsequent predictions use the already-loaded model, reducing latency to milliseconds.

</details>

### 6.3 Implementation

Create `train_model.py` in the project root:

```python
#!/usr/bin/env python3
"""Train a simple sentiment analysis model."""

import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import pandas as pd


def create_sample_data():
    """Create sample training data."""
    data = {
        'text': [
            # Positive samples
            "I love this product! It's amazing!",
            "This is the best thing ever!",
            "Absolutely wonderful experience!",
            "Great service and quality!",
            "I'm so happy with this purchase!",
            "Excellent work, highly recommend!",
            "Perfect! Exactly what I needed!",
            "Outstanding quality and fast delivery!",
            "Very satisfied with everything!",
            "Fantastic! Will buy again!",
            "I love it! Very good quality!",
            "Impressive results, very pleased!",
            "Superb! Exceeded my expectations!",
            "Wonderful product, great value!",
            "Amazing! Could not be happier!",

            # Negative samples
            "This is terrible, very disappointed.",
            "Waste of money, poor quality.",
            "I hate this, it's awful.",
            "Very bad experience, not recommended.",
            "Terrible service, will not return.",
            "Poor quality, broke after one use.",
            "Disappointed with the purchase.",
            "Not worth it, complete waste.",
            "Horrible! Do not buy this!",
            "Very unhappy with this product.",
            "Worst purchase ever made.",
            "Terrible quality and service.",
            "Awful experience, avoid this.",
            "Very disappointed, poor value.",
            "Bad product, waste of time."
        ],
        'sentiment': [1] * 15 + [0] * 15  # 1 = positive, 0 = negative
    }
    return pd.DataFrame(data)


def train_model():
    """Train the sentiment analysis model."""
    print("Creating sample training data...")
    df = create_sample_data()

    X_train, X_test, y_train, y_test = train_test_split(
        df['text'],
        df['sentiment'],
        test_size=0.2,
        random_state=42
    )

    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")

    # Create pipeline: TF-IDF vectorizer + Naive Bayes classifier
    model = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('clf', MultinomialNB())
    ])

    print("\nTraining model...")
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nModel Accuracy: {accuracy:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['negative', 'positive']))

    # Save model
    os.makedirs('models', exist_ok=True)
    model_path = 'models/sentiment_model.pkl'
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")


if __name__ == "__main__":
    train_model()
```

**What this does:** Trains a sentiment classification model using sample data.

**Why:** The API needs a trained model to make predictions. This script creates a simple but functional classifier.

**How it works:**
1. Creates 30 labeled examples (15 positive, 15 negative)
2. Splits into 80% training, 20% testing
3. Builds a pipeline: TF-IDF (text to numbers) + Naive Bayes (classifier)
4. Trains on training data, evaluates on test data
5. Saves model to `models/sentiment_model.pkl` using joblib

**Key concepts:**
- **TF-IDF**: Converts text to numerical vectors based on word frequency
- **Naive Bayes**: Fast, simple classifier good for text
- **Pipeline**: Chains preprocessing and model into single object

#### Model Serving Endpoints

Once the model is trained, we expose it through a set of REST API endpoints in `backend/app/routers/sentiment.py`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/sentiment/analyze` | POST | **Synchronous prediction** — Accepts a single text, runs it through the model, and returns the sentiment (positive/negative) with a confidence score. Ideal for real-time use cases where immediate response is needed. |
| `/api/v1/sentiment/analyze/batch` | POST | **Asynchronous batch processing** — Accepts multiple texts, queues them as a Celery background task, and returns a task ID immediately. The client can poll for results without blocking. Perfect for processing large datasets. |
| `/api/v1/sentiment/task/{task_id}` | GET | **Task status check** — Returns the current status of a batch job (pending, processing, completed, or failed) along with results when ready. |
| `/api/v1/sentiment/history` | GET | **Prediction history** — Returns the authenticated user's past predictions, useful for auditing and analytics. |

All endpoints require JWT authentication. The model loads once at application startup and stays in memory, ensuring predictions complete in milliseconds rather than seconds.

### 6.4 Checkpoint

**Self-Assessment:**
- [ ] Model loads once at startup, not per-request
- [ ] Synchronous endpoint returns sentiment with confidence
- [ ] Batch endpoint returns task ID for polling
- [ ] History endpoint shows user's past predictions


## Chapter 7: Run and Test

### 7.1 Start the System

```bash
# Build and start
docker compose build
docker compose up -d

# Initialize database
docker compose exec api1 python init_db.py
docker compose exec api1 alembic upgrade head
docker compose exec api1 python train_model.py
```

**What each command does:**

| Command | Purpose |
|---------|---------|
| `docker compose build` | Builds container images from Dockerfile |
| `docker compose up -d` | Starts all services in background |
| `python init_db.py` | Creates database tables |
| `alembic upgrade head` | Runs any pending migrations |
| `python train_model.py` | Trains and saves the ML model |

### 7.2 Test Endpoints

```bash
# Health check
curl -k https://localhost/health

# Register user
curl -k -X POST https://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'

# Login
TOKEN=$(curl -k -s -X POST https://localhost/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | jq -r '.access_token')

# Analyze sentiment
curl -k -X POST https://localhost/api/v1/sentiment/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product!"}'
```

**What these commands do:**

| Command | Expected Result |
|---------|-----------------|
| Health check | `{"status": "healthy", "api": "ok", ...}` |
| Register | Returns user object with `id`, `username`, `email` |
| Login | Returns `{"access_token": "eyJ...", "token_type": "bearer"}` |
| Analyze | Returns `{"sentiment": "positive", "confidence": 0.85, ...}` |

**Note:** The `-k` flag skips SSL verification (needed for self-signed certificates).


## Chapter 8: Verify Integration Features

This section provides CLI commands to verify that TLS, Rate Limiting, Load Balancing, and Authorization are working correctly.

### 8.1 TLS/HTTPS Verification

**Test 1: Verify HTTPS is working**
```bash
curl -k -v https://localhost/health 2>&1 | grep -E "(SSL|TLS|subject|issuer)"
```

**Expected Output:**
```
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384
* Server certificate:
*  subject: CN=localhost
*  issuer: CN=localhost
```

**Test 2: Verify HTTP redirects to HTTPS**
```bash
curl -I http://localhost/ 2>&1 | head -5
```

**Expected Output:**
```
HTTP/1.1 301 Moved Permanently
Server: nginx
Location: https://localhost/
```

**Test 3: Verify security headers are present**
```bash
curl -k -I https://localhost/health 2>&1 | grep -E "(Strict-Transport|X-Frame|X-Content-Type|X-XSS)"
```

**Expected Output:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

---

### 8.2 Rate Limiting Verification

**Test 1: Verify login rate limit (5 requests/minute)**

Run this command to send 6 rapid login requests:
```bash
for i in {1..6}; do
  echo "Request $i:"
  curl -k -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
    -X POST https://localhost/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=fakeuser&password=fakepass"
done
```

**Expected Output:**
```
Request 1:
HTTP Status: 401
Request 2:
HTTP Status: 401
Request 3:
HTTP Status: 401
Request 4:
HTTP Status: 401
Request 5:
HTTP Status: 429
Request 6:
HTTP Status: 429
```
Note: First 4 requests return 401 (invalid credentials), then 429 (rate limited) after exceeding 5r/m + burst of 3.

**Test 2: Verify general API rate limit (60 requests/minute)**

First, get a valid token:
```bash
# Register a test user (skip if already exists)
curl -k -s -X POST https://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ratelimituser", "email": "ratelimit@test.com", "password": "testpass123"}'

# Login and get token
TOKEN=$(curl -k -s -X POST https://localhost/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ratelimituser&password=testpass123" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
```

Then send 65 rapid requests:
```bash
for i in {1..65}; do
  STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" \
    -X POST https://localhost/api/v1/sentiment/analyze \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"text": "test"}')
  if [ "$STATUS" = "429" ]; then
    echo "Rate limited at request $i (HTTP 429)"
    break
  fi
done
```

**Expected Output:**
```
Rate limited at request 61 (HTTP 429)
```
Note: After 60 requests + burst of 10, you'll receive 429 Too Many Requests.

---

### 8.3 Load Balancer Verification

**Test 1: Verify requests are distributed across API instances**

The load balancer uses `least_conn` algorithm. Send multiple requests and check which instance handles each:
```bash
for i in {1..6}; do
  echo "Request $i:"
  curl -k -s https://localhost/health | grep -o '"api":"[^"]*"'
done
```

**Expected Output:**
```
Request 1:
"api":"ok"
Request 2:
"api":"ok"
...
```

**Test 2: Check both API instances are running**
```bash
echo "API Instance 1 (direct):"
curl -s http://localhost:8001/health | head -c 100

echo -e "\n\nAPI Instance 2 (direct):"
curl -s http://localhost:8002/health | head -c 100
```

**Expected Output:**
```
API Instance 1 (direct):
{"status":"healthy","api":"ok","database":"ok","redis":"ok"}

API Instance 2 (direct):
{"status":"healthy","api":"ok","database":"ok","redis":"ok"}
```

**Test 3: Verify failover (stop one instance)**
```bash
# Stop api2
docker stop sentiment_api2

# Send requests - all should still succeed via api1
for i in {1..3}; do
  curl -k -s -o /dev/null -w "Request $i: HTTP %{http_code}\n" https://localhost/health
done

# Restart api2
docker start sentiment_api2
```

**Expected Output:**
```
Request 1: HTTP 200
Request 2: HTTP 200
Request 3: HTTP 200
```

---

### 8.4 Authorization Verification

**Test 1: Access protected endpoint without token**
```bash
curl -k -s https://localhost/api/v1/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
```

**Expected Output:**
```json
{"detail":"Not authenticated"}
```

**Test 2: Access protected endpoint with invalid token**
```bash
curl -k -s https://localhost/api/v1/sentiment/analyze \
  -H "Authorization: Bearer invalid_token_here" \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
```

**Expected Output:**
```json
{"detail":"Could not validate credentials"}
```

**Test 3: Access protected endpoint with valid token**
```bash
# Login and get token
TOKEN=$(curl -k -s -X POST https://localhost/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

# Access protected endpoint
curl -k -s https://localhost/api/v1/sentiment/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product!"}'
```

**Expected Output:**
```json
{
  "text": "I love this product!",
  "sentiment": "positive",
  "confidence": 0.85,
  "processing_time": 0.002
}
```

**Test 4: Verify user profile endpoint requires authentication**
```bash
# Without token
echo "Without token:"
curl -k -s https://localhost/api/v1/users/me

# With token
echo -e "\n\nWith token:"
curl -k -s https://localhost/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Output:**
```
Without token:
{"detail":"Not authenticated"}

With token:
{"id":1,"email":"test@example.com","username":"testuser","is_active":true,"is_superuser":false,...}
```

**Test 5: Verify token expiration (requires waiting 30 minutes or modifying token)**
```bash
# Decode your token at jwt.io to see the 'exp' claim
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

**Expected Output:**
```json
{
    "sub": "testuser",
    "exp": 1707312000
}
```
The `exp` value is a Unix timestamp showing when the token expires (30 minutes after creation).

---

### 8.5 Quick Verification Script

Run all verification tests at once:
```bash
echo "=== TLS Verification ==="
curl -k -s -o /dev/null -w "HTTPS Health Check: %{http_code}\n" https://localhost/health

echo -e "\n=== HTTP to HTTPS Redirect ==="
curl -s -o /dev/null -w "HTTP Redirect: %{http_code} -> " http://localhost/
curl -k -s -o /dev/null -w "%{redirect_url}\n" http://localhost/

echo -e "\n=== Load Balancer (both instances) ==="
curl -s -o /dev/null -w "API1 Direct: %{http_code}\n" http://localhost:8001/health
curl -s -o /dev/null -w "API2 Direct: %{http_code}\n" http://localhost:8002/health

echo -e "\n=== Authorization ==="
curl -k -s -o /dev/null -w "No Token: %{http_code}\n" https://localhost/api/v1/users/me

TOKEN=$(curl -k -s -X POST https://localhost/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

curl -k -s -o /dev/null -w "With Token: %{http_code}\n" \
  -H "Authorization: Bearer $TOKEN" https://localhost/api/v1/users/me

echo -e "\n=== Rate Limiting (login - expect 429 after burst) ==="
for i in {1..6}; do
  curl -k -s -o /dev/null -w "$i:%{http_code} " \
    -X POST https://localhost/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=fake&password=fake"
done
echo ""
```

**Expected Output:**
```
=== TLS Verification ===
HTTPS Health Check: 200

=== HTTP to HTTPS Redirect ===
HTTP Redirect: 301 -> https://localhost/

=== Load Balancer (both instances) ===
API1 Direct: 200
API2 Direct: 200

=== Authorization ===
No Token: 401
With Token: 200

=== Rate Limiting (login - expect 429 after burst) ===
1:401 2:401 3:401 4:401 5:429 6:429
```

---

## Epilogue: The Complete System

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/login` | User authentication |
| POST | `/api/v1/sentiment/analyze` | Single text analysis |
| POST | `/api/v1/sentiment/analyze/batch` | Batch analysis |
| GET | `/api/v1/sentiment/task/{id}` | Task status |


## The Principles

1. **Validate at the boundary** — Pydantic models reject invalid input before it reaches business logic
2. **Load expensive resources once** — ML models load at startup, not per-request
3. **Offload long-running tasks** — Background processing keeps the API responsive
4. **Scale horizontally** — Stateless design allows multiple instances behind a load balancer
5. **Protect authentication endpoints** — Stricter rate limiting prevents brute-force attacks
6. **Check all dependencies** — Health endpoints verify database and cache connectivity
7. **Encrypt in transit** — TLS protects data between client and server
8. **Hash passwords, never encrypt** — One-way hashing limits breach damage


## Troubleshooting

### Error: Connection refused to database

**Cause:** Database container not ready.

**Solution:**
```bash
docker compose ps
docker compose logs db
docker compose restart db
```

### Error: 401 Unauthorized

**Cause:** Token expired or invalid.

**Solution:**
```bash
# Re-login to get fresh token
TOKEN=$(curl -k -s -X POST https://localhost/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | jq -r '.access_token')
```

## Next Steps

1. Add model versioning and A/B testing
2. Implement request caching with Redis
3. Add Prometheus metrics for monitoring
4. Deploy to Kubernetes for orchestration


## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

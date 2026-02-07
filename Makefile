.PHONY: help build up down restart logs clean init-db train-model migrate revision ssl test

help:
	@echo "Available commands:"
	@echo "  make build        - Build Docker containers"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs"
	@echo "  make clean       - Clean up containers and volumes"
	@echo "  make init-db     - Initialize database"
	@echo "  make train-model - Train ML model"
	@echo "  make migrate     - Apply database migrations"
	@echo "  make revision    - Create new migration"
	@echo "  make ssl         - Generate SSL certificates"
	@echo "  make test        - Run API tests"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started. API available at:"
	@echo "  HTTP:  http://localhost"
	@echo "  HTTPS: https://localhost"
	@echo "  Docs:  https://localhost/docs"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f api

clean:
	docker-compose down -v
	rm -rf models/*.pkl
	rm -rf logs/*.log

init-db:
	docker-compose exec api python init_db.py

train-model:
	docker-compose exec api python train_model.py

migrate:
	docker-compose exec api alembic upgrade head

revision:
	@read -p "Enter migration message: " msg; \
	docker-compose exec api alembic revision --autogenerate -m "$$msg"

ssl:
	mkdir -p nginx/ssl
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout nginx/ssl/key.pem \
		-out nginx/ssl/cert.pem \
		-subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
	@echo "SSL certificates generated in nginx/ssl/"

test:
	chmod +x test_api.sh
	./test_api.sh
# EventFlow Development Makefile
.PHONY: help build up down logs shell migrate seed test clean

# Colors for output
BLUE=\033[34m
GREEN=\033[32m
YELLOW=\033[33m
RED=\033[31m
NC=\033[0m # No Color

help: ## Show this help message
	@echo "${BLUE}EventFlow Development Commands${NC}"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${GREEN}%-20s${NC} %s\n", $$1, $$2}'

build: ## Build all Docker containers
	@echo "${BLUE}Building containers...${NC}"
	docker-compose build

up: ## Start all services in development mode
	@echo "${BLUE}Starting EventFlow services...${NC}"
	docker-compose up -d
	@echo "${GREEN}Services started! Visit:${NC}"
	@echo "  • Backend API: http://localhost:8000/api/"
	@echo "  • Admin Dashboard: http://localhost:3000/"
	@echo "  • API Documentation: http://localhost:8000/api/docs/"

up-tools: ## Start services with development tools (pgAdmin, Redis Commander)
	@echo "${BLUE}Starting EventFlow with development tools...${NC}"
	docker-compose --profile tools up -d
	@echo "${GREEN}Services and tools started! Visit:${NC}"
	@echo "  • Backend API: http://localhost:8000/api/"
	@echo "  • Admin Dashboard: http://localhost:3000/"
	@echo "  • API Documentation: http://localhost:8000/api/docs/"
	@echo "  • pgAdmin: http://localhost:5050/ (admin@eventflow.ug / admin)"
	@echo "  • Redis Commander: http://localhost:8081/"

down: ## Stop all services
	@echo "${BLUE}Stopping services...${NC}"
	docker-compose down

down-volumes: ## Stop all services and remove volumes (WARNING: This will delete all data)
	@echo "${RED}WARNING: This will delete all data including database!${NC}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
	fi

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-admin: ## Show admin dashboard logs
	docker-compose logs -f admin

logs-celery: ## Show Celery worker logs
	docker-compose logs -f celery

shell-backend: ## Open Django shell
	docker-compose exec backend python manage.py shell

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U eventflow_user -d eventflow_db

shell-redis: ## Open Redis CLI
	docker-compose exec redis redis-cli

migrate: ## Run Django migrations
	@echo "${BLUE}Running migrations...${NC}"
	docker-compose exec backend python manage.py migrate

makemigrations: ## Create new Django migrations
	@echo "${BLUE}Creating migrations...${NC}"
	docker-compose exec backend python manage.py makemigrations

seed: ## Load sample data
	@echo "${BLUE}Loading sample data...${NC}"
	docker-compose exec backend python manage.py loaddata fixtures/sample_data.json

createsuperuser: ## Create Django superuser
	@echo "${BLUE}Creating superuser...${NC}"
	docker-compose exec backend python manage.py createsuperuser

collectstatic: ## Collect static files
	docker-compose exec backend python manage.py collectstatic --noinput

test-backend: ## Run backend tests
	@echo "${BLUE}Running backend tests...${NC}"
	docker-compose exec backend python manage.py test

test-admin: ## Run admin dashboard tests
	@echo "${BLUE}Running admin tests...${NC}"
	docker-compose exec admin npm test

test: test-backend test-admin ## Run all tests

lint-backend: ## Run backend linting
	docker-compose exec backend flake8 .
	docker-compose exec backend black --check .

lint-admin: ## Run admin linting
	docker-compose exec admin npm run lint

lint: lint-backend lint-admin ## Run all linting

format-backend: ## Format backend code
	docker-compose exec backend black .

format-admin: ## Format admin code
	docker-compose exec admin npm run format

format: format-backend format-admin ## Format all code

clean: ## Clean up containers, images, and volumes
	@echo "${YELLOW}Cleaning up Docker resources...${NC}"
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

reset: down-volumes build up migrate seed ## Reset everything (WARNING: Deletes all data)
	@echo "${GREEN}EventFlow reset complete!${NC}"

status: ## Show status of all services
	@echo "${BLUE}Service Status:${NC}"
	docker-compose ps

# Development workflow shortcuts
dev: build up migrate seed ## Complete development setup
	@echo "${GREEN}Development environment ready!${NC}"

dev-tools: build up-tools migrate seed ## Development setup with tools
	@echo "${GREEN}Development environment with tools ready!${NC}"

restart: down up ## Restart all services

restart-backend: ## Restart just the backend
	docker-compose restart backend

restart-admin: ## Restart just the admin
	docker-compose restart admin

# Production commands (use with caution)
prod-build: ## Build for production
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up: ## Start in production mode
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Backup and restore
backup-db: ## Backup database
	@echo "${BLUE}Backing up database...${NC}"
	docker-compose exec postgres pg_dump -U eventflow_user eventflow_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database from backup (specify file with FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then echo "${RED}Please specify backup file: make restore-db FILE=backup.sql${NC}"; exit 1; fi
	@echo "${BLUE}Restoring database from $(FILE)...${NC}"
	docker-compose exec -T postgres psql -U eventflow_user -d eventflow_db < $(FILE)

# Mobile development helpers
mobile-deps: ## Install Flutter dependencies
	cd mobile && flutter pub get

mobile-build: ## Build Flutter app
	cd mobile && flutter build apk

mobile-run: ## Run Flutter app (requires device/emulator)
	cd mobile && flutter run

# Quick actions
quick-start: up ## Quick start (alias for up)
quick-stop: down ## Quick stop (alias for down)

# Show running services URLs
urls: ## Show all service URLs
	@echo "${GREEN}EventFlow Service URLs:${NC}"
	@echo "  • Backend API: http://localhost:8000/api/"
	@echo "  • Admin Dashboard: http://localhost:3000/"
	@echo "  • API Documentation: http://localhost:8000/api/docs/"
	@echo "  • Database: postgresql://eventflow_user:eventflow_pass@localhost:5432/eventflow_db"
	@echo "  • Redis: redis://localhost:6379/0"
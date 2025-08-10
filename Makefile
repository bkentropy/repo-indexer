.PHONY: help start stop restart status logs clean env

# Default target
help:
	@echo "Available targets:"
	@echo "  start-embedding  - Start the embedding service"
	@echo "  start-server     - Start the main FastAPI server (depends on embedding service)"
	@echo "  start            - Start both services (default)"
	@echo "  stop             - Stop all services"
	@echo "  restart          - Restart all services"
	@echo "  status           - Show status of all services"
	@echo "  logs             - Show logs for all services"
	@echo "  clean            - Remove log files"
	@echo "  env              - Create or update conda environment from environment-dev.yml"

# Configuration
EMBEDDING_PORT := 8001
SERVER_PORT := 8000
EMBEDDING_PID := .embedding.pid
SERVER_PID := .server.pid
EMBEDDING_LOG := embedding_service.log
SERVER_LOG := server.log
ENV_NAME := repo-indexer-dev

# Check if a command exists
CHECK_CMD := command -v
PYTHON := python3

# Start the embedding service
start-embedding:
	@if [ -f "$(EMBEDDING_PID)" ]; then \
		echo "Embedding service is already running (PID: $$(cat $(EMBEDDING_PID)))"; \
	else \
		echo "Starting embedding service on port $(EMBEDDING_PORT)..."; \
		nohup $(PYTHON) -m uvicorn embedding_service:app --host 0.0.0.0 --port $(EMBEDDING_PORT) > $(EMBEDDING_LOG) 2>&1 & echo $$! > $(EMBEDDING_PID); \
		echo "Embedding service started with PID: $$(cat $(EMBEDDING_PID))"; \
	fi

start-embedding-dev:
	@if [ -f "$(EMBEDDING_PID)" ]; then \
		echo "Embedding service is already running (PID: $$(cat $(EMBEDDING_PID)))"; \
	else \
		echo "Starting embedding service on port $(EMBEDDING_PORT)..."; \
		$(PYTHON) -m uvicorn embedding_service:app --host 0.0.0.0 --port $(EMBEDDING_PORT) --reload; \
	fi

# Wait for the embedding service to be ready
wait-for-embedding:
	@echo "Waiting for embedding service to be ready..."
	@until curl -s http://localhost:$(EMBEDDING_PORT)/health >/dev/null; do \
		echo "Waiting for embedding service..."; \
		sleep 1; \
	done
	@echo "Embedding service is ready!"

# Start the main server
start-server: wait-for-embedding
	@if [ -f "$(SERVER_PID)" ]; then \
		echo "Server is already running (PID: $$(cat $(SERVER_PID)))"; \
	else \
		echo "Starting main server on port $(SERVER_PORT)..."; \
		nohup $(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port $(SERVER_PORT) --reload > $(SERVER_LOG) 2>&1 & echo $$! > $(SERVER_PID); \
		echo "Server started with PID: $$(cat $(SERVER_PID))"; \
		echo "Server is available at http://localhost:$(SERVER_PORT)"; \
	fi

# Start both services (default)
start: start-embedding start-server

# Stop all services
stop:
	@if [ -f "$(SERVER_PID)" ]; then \
		echo "Stopping server (PID: $$(cat $(SERVER_PID)))"; \
		kill $$(cat $(SERVER_PID)) 2>/dev/null || true; \
		rm -f $(SERVER_PID); \
	else \
		echo "Server is not running"; \
	fi
	@if [ -f "$(EMBEDDING_PID)" ]; then \
		echo "Stopping embedding service (PID: $$(cat $(EMBEDDING_PID)))"; \
		kill $$(cat $(EMBEDDING_PID)) 2>/dev/null || true; \
		rm -f $(EMBEDDING_PID); \
	else \
		echo "Embedding service is not running"; \
	fi

# Restart all services
restart: stop start

# Show status of all services
status:
	@echo "=== Service Status ==="
	@if [ -f "$(EMBEDDING_PID)" ] && ps -p $$(cat $(EMBEDDING_PID)) > /dev/null 2>&1; then \
		echo "Embedding service: RUNNING (PID: $$(cat $(EMBEDDING_PID)))"; \
	else \
		echo "Embedding service: NOT RUNNING"; \
	fi
	@if [ -f "$(SERVER_PID)" ] && ps -p $$(cat $(SERVER_PID)) > /dev/null 2>&1; then \
		echo "Main server: RUNNING (PID: $$(cat $(SERVER_PID)))"; \
	else \
		echo "Main server: NOT RUNNING"; \
	fi

# Show logs
tail-logs:
	tail -f $(SERVER_LOG) $(EMBEDDING_LOG)

logs: tail-logs

# Clean up
clean:
	rm -f $(EMBEDDING_PID) $(SERVER_PID) $(EMBEDDING_LOG) $(SERVER_LOG)
	@echo "Cleaned up PID and log files"

# Create or update conda environment
env:
	@echo "Creating/updating conda environment $(ENV_NAME) from environment-dev.yml..."
	@conda env create -f environment-dev.yml -n $(ENV_NAME) || conda env update -f environment-dev.yml -n $(ENV_NAME)
	@echo "Environment $(ENV_NAME) is ready"

# Helpers
check-%:
	@if ! $(CHECK_CMD) $* >/dev/null 2>&1; then \
		echo "$* is required but not installed. Please install it first."; \
		exit 1; \
	fi


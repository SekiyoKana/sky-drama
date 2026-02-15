SHELL := /bin/bash
ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
BACKEND_DIR := $(ROOT_DIR)apps/backend
FRONTEND_DIR := $(ROOT_DIR)apps/frontend
COMPOSE_FILE := $(ROOT_DIR)deploy/docker/docker-compose.yml
DOCKER_ENV_FILE := $(ROOT_DIR)deploy/docker/.env
COMPOSE_PROJECT := sky-drama
NODE_MIN_MAJOR := 20
NODE_MIN_MINOR := 12
PNPM_MIN_MAJOR := 9

.PHONY: help check-node-version check-desktop-tools setup setup-backend setup-frontend dev-backend dev-frontend docker-up docker-down docker-logs desktop-build clean

help:
	@echo "Available targets:"
	@echo "  make check-node-version Verify Node.js version compatibility"
	@echo "  make check-desktop-tools Verify Rust toolchain for desktop build"
	@echo "  make setup           Install backend and frontend dependencies"
	@echo "  make dev-backend     Run FastAPI backend in reload mode"
	@echo "  make dev-frontend    Run Vite frontend dev server"
	@echo "  make docker-up       Build and start containers"
	@echo "  make docker-env      Create deploy/docker/.env from template"
	@echo "  make docker-down     Stop and remove containers"
	@echo "  make docker-logs     Tail Docker logs"
	@echo "  make desktop-build   Build desktop app via scripts/desktop/build.sh (macOS/Linux)"
	@echo "  make clean           Remove local build artifacts"

check-node-version:
	@NODE_BIN=$$(command -v node || true) && \
	if [ -z "$$NODE_BIN" ]; then \
		echo "[ERROR] Node.js is required (>= $(NODE_MIN_MAJOR).$(NODE_MIN_MINOR))."; \
		exit 1; \
	fi && \
	NODE_MAJOR=$$($$NODE_BIN -p "parseInt(process.versions.node.split('.')[0],10)") && \
	NODE_MINOR=$$($$NODE_BIN -p "parseInt(process.versions.node.split('.')[1],10)") && \
	HAS_CRYPTO_HASH=$$($$NODE_BIN -p "typeof require('node:crypto').hash === 'function'") && \
	if [ "$$NODE_MAJOR" -lt "$(NODE_MIN_MAJOR)" ] || \
	   { [ "$$NODE_MAJOR" -eq "$(NODE_MIN_MAJOR)" ] && [ "$$NODE_MINOR" -lt "$(NODE_MIN_MINOR)" ]; } || \
	   [ "$$HAS_CRYPTO_HASH" != "true" ]; then \
		echo "[ERROR] Node.js >= $(NODE_MIN_MAJOR).$(NODE_MIN_MINOR) is required. Current: $$($$NODE_BIN -v)"; \
		echo "[ERROR] Run: nvm install 23 && nvm use 23"; \
		exit 1; \
	fi

check-desktop-tools:
	@if ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then \
		if [ -f "$$HOME/.cargo/env" ]; then \
			. "$$HOME/.cargo/env"; \
		fi; \
	fi; \
	if ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then \
		echo "[ERROR] Rust toolchain is required for desktop build (cargo/rustc missing)."; \
		echo "[ERROR] Install: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"; \
		echo "[ERROR] Then run: source $$HOME/.cargo/env"; \
		exit 1; \
	fi

setup: check-node-version setup-backend setup-frontend

setup-backend:
	cd "$(BACKEND_DIR)" && \
	PY_BIN=$$(command -v python3 >/dev/null 2>&1 && echo python3 || echo python) && \
	if ! command -v $$PY_BIN >/dev/null 2>&1; then echo "Python not found"; exit 1; fi && \
	if [ ! -d ".venv" ]; then $$PY_BIN -m venv .venv; fi && \
	source .venv/bin/activate && \
	python -m pip install --upgrade pip && \
	python -m pip install -r requirements.txt

setup-frontend: check-node-version
ifeq ($(shell [ -f "$(FRONTEND_DIR)/pnpm-lock.yaml" ] && command -v corepack >/dev/null 2>&1; echo $$?),0)
	cd "$(FRONTEND_DIR)" && corepack enable && corepack pnpm install --frozen-lockfile
else ifeq ($(shell [ -f "$(FRONTEND_DIR)/pnpm-lock.yaml" ] && command -v pnpm >/dev/null 2>&1; echo $$?),0)
	cd "$(FRONTEND_DIR)" && \
	PNPM_MAJOR=$$(pnpm --version | cut -d. -f1) && \
	if [ "$$PNPM_MAJOR" -lt "$(PNPM_MIN_MAJOR)" ]; then \
		echo "[ERROR] pnpm >= $(PNPM_MIN_MAJOR) is required for pnpm-lock.yaml (current: $$(pnpm --version))."; \
		echo "[ERROR] Run: corepack enable && corepack prepare pnpm@9 --activate"; \
		exit 1; \
	fi && \
	pnpm install --frozen-lockfile
else ifeq ($(shell [ -f "$(FRONTEND_DIR)/yarn.lock" ] && command -v yarn >/dev/null 2>&1; echo $$?),0)
	cd "$(FRONTEND_DIR)" && yarn install --frozen-lockfile
else
	cd "$(FRONTEND_DIR)" && npm install
endif

dev-backend:
	cd "$(BACKEND_DIR)" && \
	source .venv/bin/activate && \
	uvicorn app.main:app --host 127.0.0.1 --port 11451 --reload

dev-frontend: check-node-version
ifeq ($(shell [ -f "$(FRONTEND_DIR)/pnpm-lock.yaml" ] && command -v corepack >/dev/null 2>&1; echo $$?),0)
	cd "$(FRONTEND_DIR)" && corepack enable && corepack pnpm dev
else ifeq ($(shell [ -f "$(FRONTEND_DIR)/pnpm-lock.yaml" ] && command -v pnpm >/dev/null 2>&1; echo $$?),0)
	cd "$(FRONTEND_DIR)" && \
	PNPM_MAJOR=$$(pnpm --version | cut -d. -f1) && \
	if [ "$$PNPM_MAJOR" -lt "$(PNPM_MIN_MAJOR)" ]; then \
		echo "[ERROR] pnpm >= $(PNPM_MIN_MAJOR) is required for pnpm-lock.yaml (current: $$(pnpm --version))."; \
		echo "[ERROR] Run: corepack enable && corepack prepare pnpm@9 --activate"; \
		exit 1; \
	fi && \
	pnpm dev
else ifeq ($(shell [ -f "$(FRONTEND_DIR)/yarn.lock" ] && command -v yarn >/dev/null 2>&1; echo $$?),0)
	cd "$(FRONTEND_DIR)" && yarn dev
else
	cd "$(FRONTEND_DIR)" && npm run dev
endif

docker-up:
	cd "$(ROOT_DIR)" && \
	if [ -f "$(DOCKER_ENV_FILE)" ]; then \
		docker compose --env-file "$(DOCKER_ENV_FILE)" -p "$(COMPOSE_PROJECT)" -f "$(COMPOSE_FILE)" up -d --build; \
	else \
		docker compose -p "$(COMPOSE_PROJECT)" -f "$(COMPOSE_FILE)" up -d --build; \
	fi

docker-env:
	cd "$(ROOT_DIR)" && \
	if [ -f "$(DOCKER_ENV_FILE)" ]; then \
		echo "deploy/docker/.env already exists"; \
	else \
		cp "$(ROOT_DIR)deploy/docker/.env.example" "$(DOCKER_ENV_FILE)" && \
		echo "Created deploy/docker/.env from template"; \
	fi

docker-down:
	cd "$(ROOT_DIR)" && \
	if [ -f "$(DOCKER_ENV_FILE)" ]; then \
		docker compose --env-file "$(DOCKER_ENV_FILE)" -p "$(COMPOSE_PROJECT)" -f "$(COMPOSE_FILE)" down; \
	else \
		docker compose -p "$(COMPOSE_PROJECT)" -f "$(COMPOSE_FILE)" down; \
	fi

docker-logs:
	cd "$(ROOT_DIR)" && \
	if [ -f "$(DOCKER_ENV_FILE)" ]; then \
		docker compose --env-file "$(DOCKER_ENV_FILE)" -p "$(COMPOSE_PROJECT)" -f "$(COMPOSE_FILE)" logs -f; \
	else \
		docker compose -p "$(COMPOSE_PROJECT)" -f "$(COMPOSE_FILE)" logs -f; \
	fi

desktop-build: check-node-version check-desktop-tools
	cd "$(ROOT_DIR)" && ./scripts/desktop/build.sh

clean:
	rm -rf "$(ROOT_DIR)pkg"
	rm -rf "$(BACKEND_DIR)/build" "$(BACKEND_DIR)/dist" "$(BACKEND_DIR)/backend_api.spec"
	rm -rf "$(FRONTEND_DIR)/dist" "$(FRONTEND_DIR)/src-tauri/target"

# Makefile pour FLAC Downloader

.PHONY: help install dev test lint format clean run setup

help:
	@echo "FLAC Downloader - Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Install with dev dependencies"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run code linting"
	@echo "  make format     - Format code (black, isort)"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make run        - Run the downloader"
	@echo "  make setup      - Run setup script"

install:
	pip install -r requirements.txt

dev: install
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov build dist *.egg-info

run:
	python run.py

setup:
	chmod +x setup.sh
	./setup.sh

.DEFAULT_GOAL := help

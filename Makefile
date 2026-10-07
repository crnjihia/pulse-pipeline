# Makefile
.PHONY: run run-once schedule dashboard test lint migrate

run: run-once

run-once:
	python -m pulse run --pipeline all

schedule:
	python -m pulse schedule

dashboard:
	streamlit run dashboard/app.py

test:
	pytest

lint:
	ruff check .
	mypy .

migrate:
	python -c "from db.session import get_engine; get_engine(); print('Database tables created/verified successfully.')"


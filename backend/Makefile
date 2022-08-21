.PHONY: help venv venv-init lint lint-fix

venv-init:
	python -m venv venv

venv:
	venv\Scripts\activate

lint:
	black --check .
	isort --check-only .
	flake8 .
	mypy .

lint-fix:
	black .
	isort .

run: venv
	python manage.py runserver 0.0.0.0:8000

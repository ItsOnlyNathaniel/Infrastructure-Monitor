.PHONY: dev test lint clean
   
   dev:
   	docker-compose up -d
   	uvicorn src.api.main:app --reload --port 8000
   
   test:
   	pytest tests/ -v
   
   worker:
   	python -m src.workers.remediation_worker
   
   lint:
   	black src/ tests/
   	flake8 src/ tests/
   
   clean:
   	docker-compose down -v
   	find . -type d -name __pycache__ -exec rm -rf {} +
```

4. **Create `.dockerignore`:**
```
   .git
   .gitignore
   .venv
   venv/
   __pycache__
   *.pyc
   .pytest_cache
   .env
   README.md
   docs/
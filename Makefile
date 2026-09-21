.PHONY: run docker smoke seed clean

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8080

docker:
	docker compose up --build -d

smoke:
	python -m pytest -q tests/ || true
	python scripts/smoke.py

seed:
	python data/seed.py

clean:
	rm -f data/app.db data/memory.pkl
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

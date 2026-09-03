.PHONY: dev up down migrate revision test seed api

up:        ## start postgres, redis, minio
	docker compose up -d

down:
	docker compose down

migrate:   ## apply migrations
	cd api && alembic upgrade head

revision:  ## autogenerate a migration: make revision m="add x"
	cd api && alembic revision --autogenerate -m "$(m)"

seed:      ## load corpus/ into the database as sources
	cd api && python scripts/seed_corpus.py

api:       ## run the API with reload
	cd api && uvicorn app.main:app --reload

test:
	cd api && python -m pytest -q

dev: up    ## first-run: bring up services, migrate, seed, then run the API
	sleep 3
	$(MAKE) migrate
	$(MAKE) seed
	$(MAKE) api

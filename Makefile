.PHONY: secrets build deploy inspect clean clean-secrets

# terminate input with EOF / CTRL-Z
secrets:
	docker secret create SECRET_KEY -
	docker secret create DATABASE_PASSWORD -
	docker secret create EMAIL_HOST_PASSWORD -

build:
	docker build ./backend

# supposed to fail after build
deploy-build:
	docker-compose up --build

deploy:
	docker stack deploy --compose-file=docker-compose.yml cryptotax-backend-dev

inspect:
	docker stack ps --no-trunc cryptotax-backend-dev
	docker inspect wjwl7p4hd7gzgq69crewebikp

clean:
	docker service rm cryptotax-backend-dev_celery
	docker service rm cryptotax-backend-dev_celery-beat
	docker service rm cryptotax-backend-dev_redis
	docker service rm cryptotax-backend-dev_api

clean-secrets:
	docker secret rm SECRET_KEY
	docker secret rm DATABASE_PASSWORD
	docker secret rm EMAIL_HOST_PASSWORD
.PHONY: secrets build deploy inspect clean clean-secrets

# terminate input with EOF / CTRL-Z
secrets:
	docker secret create SECRET_KEY -
	docker secret create DATABASE_PASSWORD -
	docker secret create EMAIL_HOST_PASSWORD -

build:
	docker build ./backend

deploy:
	docker stack deploy --compose-file=docker-compose.yml cryptotax-backend-dev

inspect:
	docker stack ps --no-trunc cryptotax-backend-dev
	docker inspect wjwl7p4hd7gzgq69crewebikp

clean:
	docker service rm cryptotax-backend-dev_web

clean-secrets:
	docker secret rm SECRET_KEY
	docker secret rm DATABASE_PASSWORD
	docker secret rm EMAIL_HOST_PASSWORD

# CryptoTax Backend

## Details
Django REST API backend for ReactJS frontend.
Inteded to analyse crypto currency taxation (primarily for Germany)

## Project Structure
```
/cryptotax-backend (main directory containing all deployment specific files, e.g. docker setup, configuration, ...)
|   .gitignore
|   README.MD
|   docker-compose.yml
└── backend (all python/django related things, venv, development environment)
│   │   Makefile
│   │   ...
│   └── ...
...
```

## Setup
### Environment variables (for django)
```
- DEBUG=1
- SECRET_KEY='' (SECRET)
- DEBUG=True
- DATABASE_HOST='db.cryptotax.nerotecs.com'
- DATABASE_NAME='cryptotax'
- DATABASE_USER='cryptotaxx'
- DATABASE_PASSWORD='' (SECRET)
- DATABASE_PORT='7766'
- EMAIL_HOST='smtp.gmail.com'
- EMAIL_PORT=587
- EMAIL_HOST_USER='nerotecs@gmail.com'
- EMAIL_HOST_PASSWORD='' (SECRET)
```

### root makefile usage -> build docker stack
1) ```make secrets``` (terminate with CTRL+Z or EOF then enter)
2) ```make build```
3) ```make deploy-build```
4) ```make deploy```
5) End: ```make clean```

### Related Projects
- [ReactJS Frontend](https://github.com/nerotyc/cryptotax_frontend)
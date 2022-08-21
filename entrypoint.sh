
# get your envs files and export envars
#export $(egrep  -v '^#'  /run/secrets/* | xargs)

# if you need some specific file, where password is the secret name
# export $(egrep  -v '^#'  /run/secrets/password| xargs)

export SECRET_KEY=$(cat /run/secrets/SECRET_KEY)
export DATABASE_PASSWORD=$(cat /run/secrets/DATABASE_PASSWORD)
export EMAIL_HOST_PASSWORD=$(cat /run/secrets/EMAIL_HOST_PASSWORD)

python manage.py runserver 0.0.0.0:8000


# get your envs files and export envars
#export $(egrep  -v '^#'  /run/secrets/* | xargs)

# if you need some specific file, where password is the secret name
# export $(egrep  -v '^#'  /run/secrets/password| xargs)

export SECRET_KEY=$(cat /run/secrets/SECRET_KEY)
export DATABASE_PASSWORD=$(cat /run/secrets/DATABASE_PASSWORD)
export EMAIL_HOST_PASSWORD=$(cat /run/secrets/EMAIL_HOST_PASSWORD)

if [ $CONTAINER == "api" ]
then
    python manage.py runserver 0.0.0.0:8000
fi

if  [ $CONTAINER == "celery" ]
then
    celery -A cryptotax_backend worker -l info
fi

if [ $CONTAINER == "celery-beat" ]
then
    celery -A cryptotax_backend beat -l info
fi

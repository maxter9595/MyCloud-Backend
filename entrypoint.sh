#!/bin/sh

python manage.py makemigrations accounts
python manage.py makemigrations storage
python manage.py migrate
python manage.py migrate django_celery_beat
python manage.py collectstatic --noinput

exec "$@"

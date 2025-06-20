#!/bin/sh

if [ "$DJANGO_ENV" = "production" ]; then
    python manage.py migrate
    gunicorn PFE_VOC.wsgi:application --bind 0.0.0.0:8000
else
    python manage.py migrate
    python manage.py runserver 0.0.0.0:8000
fi
#!/bin/sh

export APP_SETTINGS=app_settings.cfg
./python3.4/bin/uwsgi --uid 33 --socket 127.0.0.1:5001  -w WSGI:app

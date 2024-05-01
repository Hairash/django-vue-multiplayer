python manage.py truncate_tables
daphne -b $APP_HOST -p 8000 django_vue_multiplayer.asgi:application

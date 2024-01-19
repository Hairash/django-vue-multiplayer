from django.apps import AppConfig
from django.db import connection


class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE app_player CASCADE")
            cursor.execute("TRUNCATE TABLE app_game CASCADE")

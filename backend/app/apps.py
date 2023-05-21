from django.apps import AppConfig
from django.db import connection


class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE app_player CASCADE")

        from .models import Game
        try:
            game = Game.objects.get(pk=1)
            game.state = Game.States.WAIT
            game.save()
        except Game.DoesNotExist as e:
            pass

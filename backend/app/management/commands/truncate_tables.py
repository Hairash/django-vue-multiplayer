from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

from app.models import Game, Player


class Command(BaseCommand):
    help = 'Truncates the game and player tables'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Truncating the game and player tables...")
            Game.objects.all().delete()
            Player.objects.all().delete()
            self.stdout.write("Game and player tables truncated successfully.")
        except OperationalError as e:
            self.stderr.write('Failed to delete entries, probably tables were not created yet. Error: {}'.format(str(e)))

from django.db import models
from django.contrib.auth.models import User


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    channel_name = models.CharField(max_length=255)


class Game(models.Model):
    class States(models.TextChoices):
        WAIT = 'wait', 'Wait'
        GAME = 'game', 'Game'

    state = models.CharField(max_length=4, choices=States.choices, default=States.WAIT)
    visitors = models.ManyToManyField(Player, blank=True, related_name="games_as_visitors")
    participants = models.ManyToManyField(Player, blank=True, related_name="games_as_participants")

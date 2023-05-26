from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    channel_name = models.CharField(max_length=255)


class Game(models.Model):
    class States(models.TextChoices):
        WAIT = 'wait', 'Wait'
        GAME = 'game', 'Game'

    class Phases(models.TextChoices):
        ATTACK = 'attack', 'Attack'
        DEFENSE = 'defense', 'Defense'

    class Actions(models.TextChoices):
        PLAY = 'play', 'Play'
        TAKE = 'take', 'Take'
        PASS = 'pass', 'Pass'

    state = models.CharField(max_length=4, choices=States.choices, default=States.WAIT)
    visitors = models.ManyToManyField(Player, blank=True, related_name="games_as_visitors")
    participants = models.ManyToManyField(Player, blank=True, related_name="games_as_participants")
    # current_player - which turn (change after end of turn - beaten or taken, or redirect)
    current_player = models.ForeignKey(
        'Player',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='games_as_current_player',
    )
    phase = models.CharField(max_length=7, choices=Phases.choices, default=Phases.ATTACK)
    active_players = models.ManyToManyField(
        Player,
        blank=True,
        related_name="games_as_active_players"
    )
    allowed_actions = ArrayField(
        models.CharField(max_length=4, choices=Actions.choices, default=Actions.PLAY),
        blank=True,
        default=list,
    )

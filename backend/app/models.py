from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

from app.services.helpers import get_player_user_name


class Card:
    class SUITS:
        HEARTS = 'H'
        DIAMONDS = 'D'
        CLUBS = 'C'
        SPADES = 'S'

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def to_dict(self):
        return {
            'rank': self.rank,
            'suit': self.suit
        }

    @staticmethod
    def suit_to_emoji(suit):
        suit_emoji_dict = {
            'H': '♥',
            'D': '♦',
            'C': '♣',
            'S': '♠',
        }
        return suit_emoji_dict[suit]

    @classmethod
    def from_dict(cls, data):
        return cls(data['rank'], data['suit'])

    def __str__(self):
        return f'{self.rank}{self.suit_to_emoji(self.suit)}'


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    channel_name = models.CharField(max_length=255)
    hand = models.JSONField(default=list)

    def __str__(self):
        return get_player_user_name(self)

class Game(models.Model):
    class States(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not started'
        GAME = 'game', 'Game'
        WAIT = 'wait', 'Wait'  # not used for now

    class Phases(models.TextChoices):
        ATTACK = 'attack', 'Attack'
        DEFENSE = 'defense', 'Defense'
        ADDITION = 'addition', 'Addition'

    class Actions(models.TextChoices):
        PLAY = 'play', 'Play'
        TAKE = 'take', 'Take'
        PASS = 'pass', 'Pass'

    state = models.CharField(max_length=15, choices=States.choices, default=States.NOT_STARTED)
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
    phase = models.CharField(max_length=15, choices=Phases.choices, default=Phases.ATTACK)
    # active_players - who may take actions right now
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
    deck = models.JSONField(default=list)
    table = models.JSONField(default=list)

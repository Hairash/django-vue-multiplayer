from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token

from app.models import Game, Player


@database_sync_to_async
def get_user_by_token(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


@database_sync_to_async
def create_player(channel_name, user=None):
    player = Player(channel_name=channel_name)
    if user:
        player.user = user
    player.save()
    return player


@database_sync_to_async
def get_or_create_game():
    game, _ = Game.objects.get_or_create(pk=1)
    return game


@database_sync_to_async
def add_visitor_to_game(game, player):
    game.visitors.add(player)
    game.save()


@database_sync_to_async
def update_player_user(player, user):
    player.user = user
    player.save()


@database_sync_to_async
def get_player_by_user(game, user):
    for player in game.visitors.all():
        if player.user == user:
            return player


@database_sync_to_async
def get_player_by_channel_name(game, channel_name):
    for player in game.visitors.all():
        if player.channel_name == channel_name:
            return player


@database_sync_to_async
def get_next_player(game, player):
    players = list(game.participants.all())
    idx = players.index(player)
    return players[(idx + 1) % len(players)]


@database_sync_to_async
def get_game_visitors_participants_names(game):
    visitor_names = [player.user.username for player in game.visitors.all()]
    participant_names = [player.user.username for player in game.participants.all()]
    return visitor_names, participant_names


@database_sync_to_async
def set_game_state(game, state):
    game.state = state
    game.save()


@database_sync_to_async
def make_participants(game):
    for user in game.visitors.all():
        game.participants.add(user)
    game.save()


@database_sync_to_async
def remove_player(player):
    player.delete()

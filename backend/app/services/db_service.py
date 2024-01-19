import logging

from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token

from app.models import Game, Player


logger = logging.getLogger('django_vue_multiplayer')


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
    players = list(game.participants.order_by('id').all())
    idx = players.index(player)
    return players[(idx + 1) % len(players)]


@database_sync_to_async
def get_game_visitors_participants_names(game):
    visitor_names = [getattr(getattr(player, 'user'), 'username', '???') for player in game.visitors.all()]
    participant_names = [getattr(getattr(player, 'user'), 'username', '???') for player in game.participants.all()]
    return visitor_names, participant_names


@database_sync_to_async
def set_game_state(game, state):
    game.state = state
    game.save()


@database_sync_to_async
def init_participants(game):
    for user in game.visitors.all():
        game.participants.add(user)
    game.save()


@database_sync_to_async
def remove_player(player):
    player.delete()


@database_sync_to_async
def init_current_player(game):
    game.current_player = game.participants.first()
    game.save()
    return game.current_player


@database_sync_to_async
def get_current_player(game):
    return game.current_player


@database_sync_to_async
def set_current_player(game, player):
    game.current_player = player
    game.save()
    return player


@database_sync_to_async
def get_current_player_user_name(game):
    return getattr(getattr(getattr(game, 'current_player', None), 'user', None), 'username', None)


@database_sync_to_async
def get_phase(game):
    return game.phase


@database_sync_to_async
def get_active_player_names(game):
    active_player_names = [player.user.username for player in game.active_players.all()]
    return active_player_names


@database_sync_to_async
def get_allowed_actions(game):
    return game.allowed_actions


@database_sync_to_async
def set_phase(game, phase):
    game.phase = phase
    game.save()


@database_sync_to_async
def set_active_players(game, players):
    game.active_players.clear()
    for player in players:
        game.active_players.add(player)
    game.save()


@database_sync_to_async
def set_allowed_actions(game, actions):
    game.allowed_actions.clear()
    for action in actions:
        game.allowed_actions.append(action)
    game.save()


@database_sync_to_async
def toggle_phase(game):
    if game.phase == Game.Phases.ATTACK:
        game.phase = Game.Phases.DEFENSE
    else:
        game.phase = Game.Phases.ATTACK
    game.save()
    return game.phase


@database_sync_to_async
def toggle_active_players(game):
    active_players = list(game.participants.exclude(
        id__in=game.active_players.values_list('id', flat=True)
    ))
    game.active_players.clear()
    for player in active_players:
        game.active_players.add(player)
    game.save()


@database_sync_to_async
def get_participants(game):
    return list(game.participants.order_by('id').all())



@database_sync_to_async
def get_player_hand(player):
    return player.hand


@database_sync_to_async
def play_card_to_table(game, player, card_dict):
    player.hand.remove(card_dict)
    game.table.append(card_dict)
    player.save()
    game.save()


@database_sync_to_async
def get_table(game):
    return game.table


@database_sync_to_async
def take_cards_from_table(game, player):
    player.hand += game.table
    game.table = []
    player.save()
    game.save()


@database_sync_to_async
def clear_table(game):
    game.table = []
    game.save()


@database_sync_to_async
def is_player_participant(game, player):
    return game.participants.filter(id=player.id).exists()


@database_sync_to_async
def end_game(game):
    game.state = Game.States.WAIT
    game.participants.update(hand=[])
    game.participants.clear()
    game.current_player = None
    game.phase = Game.Phases.ATTACK
    game.active_players.clear()
    game.allowed_actions = []
    game.deck = []
    game.table = []
    game.save()

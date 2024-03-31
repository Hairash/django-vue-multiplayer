class GameError(Exception):
    pass


def get_player_user_name(player):
    return getattr(getattr(player, 'user'), 'username', '???')

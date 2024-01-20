import random

from channels.db import database_sync_to_async

from app.models import Card, Game
from app.services.db_service import (
    get_deck,
    get_next_player,
    get_player_hand,
    get_participants,
    get_table,
    remove_player_from_participants,
    set_active_players,
    set_allowed_actions,
    set_current_player,
    set_phase,
)


CARDS_IN_HAND = 6


@database_sync_to_async
def generate_deck(game):
    print('generate deck')
    RANKS = list(range(6, 15))
    SUITS = [
        Card.SUITS.SPADES,
        Card.SUITS.CLUBS,
        Card.SUITS.HEARTS,
        Card.SUITS.DIAMONDS,
    ]

    # Generate all combinations of RANKS and SUITS
    all_cards = [(rank, suit) for rank in RANKS for suit in SUITS]
    random.shuffle(all_cards)
    game.deck = [Card(card[0], card[1]).to_dict() for card in all_cards]
    game.save()


@database_sync_to_async
def draw_cards(game, player, n):
    if n == 0:
        return
    card_dicts = game.deck[-n:]
    del game.deck[-n:]
    print('cards to draw:', card_dicts)

    if card_dicts:
        player.hand += card_dicts
        game.save()
        player.save()
    else:
        # The deck is empty, handle according to your game's rules
        pass


async def replenish_hand(game, player):
    print('replenish_hand')
    num_cards_to_draw = max(CARDS_IN_HAND - len(await get_player_hand(player)), 0)
    await draw_cards(game, player, num_cards_to_draw)


async def replenish_all_player_hands(game):
    print('replenish_all_player_hands')
    participants = await get_participants(game)
    for player in participants:
        await replenish_hand(game, player)


async def start_new_turn(game, current_player):
    await replenish_all_player_hands(game)
    print('Cards left:', len(await get_deck(game)))
    # Remove players with no cards
    while not await get_player_hand(current_player) and await get_participants(game):
        next_player = await get_next_player(game, current_player)
        await remove_player_from_participants(game, current_player)
        current_player = await set_current_player(game, next_player)
    for player in await get_participants(game):
        if not await get_player_hand(player):
            await remove_player_from_participants(game, player)

    await set_phase(game, Game.Phases.ATTACK)
    await set_active_players(game, [current_player])
    await set_allowed_actions(game, [Game.Actions.PLAY])


async def check_stop_attack(game, defender):
    if not await get_player_hand(defender):
        return True
    if len(await get_table(game)) >= CARDS_IN_HAND * 2:
        return True
    return False

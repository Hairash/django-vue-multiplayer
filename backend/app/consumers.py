import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from app.services.helpers import GameError

from .services.db_service import (
    end_game,
    get_user_by_token,
    create_player,
    get_or_create_game,
    add_visitor_to_game,
    is_player_in_active_players,
    is_player_participant,
    update_player_user,
    get_player_by_user,
    get_player_by_channel_name,
    get_next_player,
    get_game_visitors_participants_names,
    set_game_state,
    init_participants,
    remove_player,
    init_current_player,
    set_current_player,
    get_current_player,
    get_current_player_user_name,
    get_phase,
    get_active_player_names,
    get_allowed_actions,
    set_phase,
    set_active_players,
    set_allowed_actions,
    toggle_phase,
    toggle_active_players,
    get_participants,
    get_player_hand,
    play_card_to_table,
    get_table,
    take_cards_from_table,
    clear_table,
)
from .services.game_service import (
    generate_deck,
    replenish_all_player_hands,
)
from .models import Game


logger = logging.getLogger('django_vue_multiplayer')


class BroadcastMixin(AsyncWebsocketConsumer):
    async def broadcast_data(self, data):
        await self.channel_layer.group_send(
            'all',
            {
                'type': 'send_message_to_group',
                'message': json.dumps(data),
            },
        )

    async def send_message_to_player(self, player, message):
        await self.channel_layer.group_send(
            self.get_user_group_name(player.channel_name),
            {
                'type': 'send_message_to_group',
                'message': message,
            },
        )

    async def send_message_to_group(self, event):
        message = event['message']
        await self.send(text_data=message)

    @staticmethod
    def get_user_short_name(channel_name):
        return channel_name[-4:]

    def get_user_group_name(self, channel_name):
        return f'group_{self.get_user_short_name(channel_name)}'


class ActionHandlerMixin(BroadcastMixin, AsyncWebsocketConsumer):
    async def handle_authenticate(self, data, game):
        token_key = data['token']
        user = await get_user_by_token(token_key)
        logger.debug(user)

        if user and not await get_player_by_user(game, user):
            self.scope['user'] = user
            player = await get_player_by_channel_name(game, self.channel_name)
            logger.debug(player)
            await update_player_user(player, user)
            await self.send(json.dumps({'action': 'authenticated'}))
            await self.broadcast_server_state(game)
        elif not user:
            await self.send_error('Invalid token. Please re-login')
            await self.close()
        else:
            await self.send_error('User is already connected')
            await self.close()

    async def handle_start(self, data, game):
        if game.state != Game.States.WAIT:
            await self.send_error('Game has been already started')
            return

        await set_game_state(game, Game.States.GAME)
        await init_participants(game)
        await self.broadcast_server_state(game)
        await generate_deck(game)
        await replenish_all_player_hands(game)
        current_player = await init_current_player(game)
        await set_phase(game, Game.Phases.ATTACK)
        await set_active_players(game, [current_player])
        await set_allowed_actions(game, [Game.Actions.PLAY])
        await self.broadcast_game_state(game)
        await self.send_all_player_hands(game)

    async def handle_play(self, data, game):
        active_player = await get_player_by_channel_name(game, self.channel_name)
        if not is_player_participant(game, active_player):
            await self.send_error('Game is already in progress. Please wait for the end of the game.')
            return
        if not is_player_in_active_players(game, active_player):
            await self.send_error('Please wait for your turn')
            return

        card_dict = data['card']
        try:
            await play_card_to_table(game, active_player, card_dict)
        except GameError as e:
            await self.send_error(str(e))
            return

        current_player = await get_current_player(game)
        defender = await get_next_player(game, current_player)

        phase = await toggle_phase(game)
        if phase == Game.Phases.ATTACK:
            await toggle_active_players(game)
            await set_allowed_actions(game, [Game.Actions.PLAY, Game.Actions.PASS])
        else:
            await set_active_players(game, [defender])
            await set_allowed_actions(game, [Game.Actions.PLAY, Game.Actions.TAKE])

        await self.broadcast_game_state(game)
        await self.send_all_player_hands(game)

    # TODO: Logic. If current player out of cards, remove them from participants and change current player

    # TODO: Logic. If state == GAME, ignore messages from watchers
    async def handle_take(self, data, game):
        active_player = await get_player_by_channel_name(game, self.channel_name)
        current_player = await get_current_player(game)
        defender = await get_next_player(game, current_player)
        next_player = await get_next_player(game, defender)
        await take_cards_from_table(game, active_player)
        current_player = await set_current_player(game, next_player)
        # TODO: Refactoring. Move to function
        # Start new turn
        await replenish_all_player_hands(game)
        await set_phase(game, Game.Phases.ATTACK)
        await set_active_players(game, [current_player])
        await set_allowed_actions(game, [Game.Actions.PLAY])
        await self.broadcast_game_state(game)
        await self.send_all_player_hands(game)

    async def handle_pass(self, data, game):
        # TODO: Logic. Make more wise handling - count number of passes
        # Move cards to the discard pile
        await clear_table(game)
        # TODO: Refactoring. Move to functions
        # Change current player
        current_player = await get_current_player(game)
        next_player = await get_next_player(game, current_player)
        current_player = await set_current_player(game, next_player)
        # Start new turn
        await replenish_all_player_hands(game)
        await set_phase(game, Game.Phases.ATTACK)
        await set_active_players(game, [current_player])
        await set_allowed_actions(game, [Game.Actions.PLAY])
        await self.broadcast_game_state(game)
        await self.send_all_player_hands(game)

    async def handle_end(self, data, game):
        await end_game(game)
        await self.broadcast_server_state(game)

    # Messaging helpers

    async def send_player_hand(self, player):
        cards = await get_player_hand(player)
        data = {'action': 'hand', 'cards': cards}
        await self.send_message_to_player(player, json.dumps(data))

    async def send_all_player_hands(self, game):
        players = await get_participants(game)
        for player in players:
            await self.send_player_hand(player)

    async def broadcast_game_state(self, game):
        current_player_user_name = await get_current_player_user_name(game)
        phase = await get_phase(game)
        active_player_names = await get_active_player_names(game)
        allowed_actions = await get_allowed_actions(game)
        table = await get_table(game)
        response_data = {
            'action': 'game_state',
            'current_player': current_player_user_name,
            'phase': phase,
            'active_players': active_player_names,
            'allowed_actions': allowed_actions,
            'table': table,
        }
        await self.broadcast_data(response_data)

    async def send_error(self, error_message):
        data = {'action': 'error', 'message': error_message}
        await self.send(json.dumps(data))


class GameConsumer(ActionHandlerMixin, BroadcastMixin, AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_handler_funcs = {
            'authenticate': self.handle_authenticate,
            'start': self.handle_start,
            'play': self.handle_play,
            'take': self.handle_take,
            'pass': self.handle_pass,
            'end': self.handle_end,
        }

    async def connect(self):
        logger.debug(f'=====> Connected player: {self.channel_name}')
        logger.debug(f'=====> Group: {self.get_user_group_name(self.channel_name)}')

        response_data = {'action': 'connected', 'player': self.get_user_short_name(self.channel_name)}
        await self.broadcast_data(response_data)

        game = await get_or_create_game()
        player = await create_player(self.channel_name)
        await add_visitor_to_game(game, player)

        await self.channel_layer.group_add(
            self.get_user_group_name(self.channel_name),
            self.channel_name,
        )
        await self.channel_layer.group_add(
            'all',
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code, auth_failed=False):
        game = await get_or_create_game()
        player = await get_player_by_channel_name(game, self.channel_name)
        is_end_game = (game.state == Game.States.GAME) and await is_player_participant(game, player)
        await remove_player(player)

        if is_end_game:
            await end_game(game)

        await self.broadcast_server_state(game)

        await self.channel_layer.group_discard(
            self.get_user_group_name(self.channel_name),
            self.channel_name,
        )
        await self.channel_layer.group_discard(
            'all',
            self.channel_name,
        )

        # TODO: Beautify. Send real player's name
        response_data = {'action': 'disconnected', 'player': self.get_user_short_name(self.channel_name)}
        await self.broadcast_data(response_data)
        # TODO: Beautify. Think, maybe we need to send a special message to notify users
        logger.debug(f'=====> Disconnected')
        return

    async def receive(self, text_data):
        data = json.loads(text_data)
        game = await get_or_create_game()

        action = data.get('action', None)
        if not action:
            # TODO: Refactoring. Make list of actions to response
            await self.send_error('Bad message - no "action" field')
            return
        handler_func = self.action_handler_funcs.get(action, None)
        if not handler_func:
            await self.send_error('Bad message - unknown action: {action}')
            return

        await handler_func(data, game)

    async def broadcast_server_state(self, game):
        visitor_names, participant_names = await get_game_visitors_participants_names(game)
        response_data = {
            'action': 'server_state',
            'state': game.state,
            'visitors': visitor_names,
            'participants': participant_names,
        }
        await self.broadcast_data(response_data)

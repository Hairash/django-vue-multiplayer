import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from .services.db_service import (
    get_user_by_token,
    create_player,
    get_or_create_game,
    add_visitor_to_game,
    update_player_user,
    get_player_by_user,
    get_player_by_channel_name,
    get_next_player,
    get_game_visitors_participants_names,
    set_game_state,
    make_participants,
    remove_player,
)
from .models import Game


logger = logging.getLogger('django_vue_multiplayer')


class BroadcastMixin(AsyncWebsocketConsumer):
    async def broadcast_message(self, message):
        await self.channel_layer.group_send(
            'all',
            {
                'type': 'send_message_to_group',
                'message': message,
            },
        )

    async def send_message_to_player(self, message, player):
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
    # TODO: If state == GAME, ignore messages from watchers
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
            await self.broadcast_server_state()
        elif not user:
            await self.send(json.dumps({'action': 'error', 'message': 'Invalid token. Please re-login'}))
            await self.close()
        else:
            await self.send(json.dumps({'action': 'error', 'message': 'User is already connected'}))
            await self.close()
            # logger.debug('Connection closed')

    async def handle_start(self, data, game):
        await set_game_state(game, Game.States.GAME)
        await make_participants(game)
        await self.broadcast_server_state()

    async def handle_question(self, data, game):
        response_data = {'action': 'answer'}
        await self.send(json.dumps(response_data))

    async def handle_everybody(self, data, game):
        response_data = {'action': 'bro'}
        await self.broadcast_message(json.dumps(response_data))

    async def handle_next(self, data, game):
        response_data = {'action': 'just for you'}
        player = await get_player_by_channel_name(game, self.channel_name)
        next_player = await get_next_player(game, player)
        await self.send_message_to_player(json.dumps(response_data), next_player)

    # TODO: Add 'end' action handler


class GameConsumer(ActionHandlerMixin, BroadcastMixin, AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_handler_funcs = {
            'authenticate': self.handle_authenticate,
            'start': self.handle_start,
            'question': self.handle_question,
            'everybody': self.handle_everybody,
            'next': self.handle_next,
        }

    async def connect(self):
        logger.debug(f'=====> Connected player: {self.channel_name}')
        logger.debug(f'=====> Group: {self.get_user_group_name(self.channel_name)}')

        response_data = {'action': 'connected', 'player': self.get_user_short_name(self.channel_name)}
        await self.broadcast_message(json.dumps(response_data))

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
        # logger.debug('Channel added to the groups')

        await self.accept()
        # logger.debug('Connection accepted')
        # logger.debug('Connect finish')

    async def disconnect(self, close_code, auth_failed=False):
        # logger.debug('Disconnect start')
        await self.channel_layer.group_discard(
            self.get_user_group_name(self.channel_name),
            self.channel_name,
        )
        # logger.debug('Disconnect player removed from the personal group')
        await self.channel_layer.group_discard(
            'all',
            self.channel_name,
        )
        # logger.debug('Disconnect player removed from the "all" group')

        # TODO: Send real player's name
        response_data = {'action': 'disconnected', 'player': self.get_user_short_name(self.channel_name)}

        await self.broadcast_message(json.dumps(response_data))

        game = await get_or_create_game()
        player = await get_player_by_channel_name(game, self.channel_name)
        await remove_player(player)
        # TODO: Add check if participant disconnected (if not - don't change state)
        # TODO: If yes - remove players from the game
        await set_game_state(game, Game.States.WAIT)
        # logger.debug('Disconnect player removed from the list')
        await self.broadcast_server_state()
        logger.debug('=======> Disconnected')
        return

    async def receive(self, text_data):
        data = json.loads(text_data)
        game = await get_or_create_game()

        action = data.get('action', None)
        if not action:
            # TODO: Make list of actions to response
            await self.send(json.dumps({'action': 'error', 'message': 'Bad message - no "action" field'}))
            return
        handler_func = self.action_handler_funcs.get(action, None)
        if not handler_func:
            await self.send(json.dumps({'action': 'error', 'message': f'Bad message - unknown action: {action}'}))
            return

        await handler_func(data, game)

    async def broadcast_server_state(self):
        game = await get_or_create_game()
        visitor_names, participant_names = await get_game_visitors_participants_names(game)
        response_data = {
            'action': 'server_state',
            'state': game.state,
            'visitors': visitor_names,
            'participants': participant_names,
        }
        await self.broadcast_message(json.dumps(response_data))

import json
import logging
from enum import Enum

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.apps import apps
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from .models import Game, Player


logger = logging.getLogger('django_vue_multiplayer')


# Database functions
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


class GameConsumer(AsyncWebsocketConsumer):
    class States(Enum):
        WAIT = 'wait'
        GAME = 'game'

    state = States.WAIT
    # players and users are lists because it's necessary to keep order of players
    visitors = []
    participants = []

    async def connect(self):
        logger.debug(f'=====> Connected player: {self.channel_name}')
        logger.debug(f'=====> Group: {self.get_user_group_name(self.channel_name)}')
        logger.debug(f'state: {self.state}')

        response_data = {'action': 'connected', 'player': self.get_user_short_name(self.channel_name)}
        await self.channel_layer.group_send(
            'all',
            {
                'type': 'send_message_to_group',
                'message': json.dumps(response_data),
            },
        )

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
        logger.debug(f'participants: {self.participants}')
        # logger.debug('Channel added to the groups')

        await self.accept()
        logger.debug(f'visitors: {self.visitors}, participants: {self.participants}')
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
        await self.channel_layer.group_send(
            'all',
            {
                'type': 'send_message_to_group',
                'message': json.dumps(response_data),
            },
        )

        game = await get_or_create_game()
        player = await get_player_by_channel_name(game, self.channel_name)
        await remove_player(player)
        # TODO: Add check if player disconnected (if not - don't change state)
        # TODO: If yes - remove players from the game
        await set_game_state(game, Game.States.WAIT)
        # logger.debug('Disconnect player removed from the list')
        await self.broadcast_server_state()
        logger.debug('=======> Disconnected')
        logger.debug(f'=======> participants: {self.participants}')
        return

    async def receive(self, text_data):
        data = json.loads(text_data)
        game = await get_or_create_game()

        # TODO: If state == GAME, ignore messages from watchers

        # Process the received data and generate a response
        # TODO: Make a list with possible messages
        if data['action'] == 'authenticate':
            token_key = data['token']
            user = await get_user_by_token(token_key)
            logger.debug(user)

            if user and not await get_player_by_user(game, user):
                self.scope['user'] = user
                player = await get_player_by_channel_name(game, self.channel_name)
                logger.debug(player)
                await update_player_user(player, user)
                player.user_name = user.username
                await self.send(json.dumps({'action': 'authenticated'}))
                logger.debug(f'visitors: {self.visitors}, participants: {self.participants}')
                await self.broadcast_server_state()
            elif not user:
                await self.send(json.dumps({'action': 'error', 'message': 'Invalid token. Please re-login'}))
                await self.close()
            else:
                await self.send(json.dumps({'action': 'error', 'message': 'User is already connected'}))
                await self.close()
                # logger.debug('Connection closed')

        elif data['action'] == 'start':
            await set_game_state(game, Game.States.GAME)
            await make_participants(game)
            await self.broadcast_server_state()

        elif data['action'] == 'question':
            response_data = {'action': 'answer'}

            # Send the response back to the group (all connected players)
            await self.channel_layer.group_send(
                self.get_user_group_name(self.channel_name),
                {
                    'type': 'send_message_to_group',
                    'message': json.dumps(response_data),
                },
            )

        elif data['action'] == 'everybody':
            response_data = {'action': 'bro'}

            # Send the response back to the group (all connected players)
            await self.channel_layer.group_send(
                'all',
                {
                    'type': 'send_message_to_group',
                    'message': json.dumps(response_data),
                },
            )

        elif data['action'] == 'next':
            response_data = {'action': 'just for you'}

            # keys = list(self.participants.keys())
            # next_player_name = keys[(keys.index(self.channel_name) + 1) % len(keys)]
            player = await get_player_by_channel_name(game, self.channel_name)
            next_player = await get_next_player(game, player)
            # channel_names = [p.channel_name for p in self.participants]
            # next_player_idx = (channel_names.index(self.channel_name) + 1) % len(channel_names)
            # logger.debug(f'=====> Next player id: {next_player_idx}')
            # logger.debug(f'=====> Next player: {self.get_user_short_name(self.participants[next_player_idx].channel_name)}')

            # Send the response back to the group (all connected players)
            await self.channel_layer.group_send(
                self.get_user_group_name(next_player.channel_name),
                {
                    'type': 'send_message_to_group',
                    'message': json.dumps(response_data),
                },
            )

    async def broadcast_server_state(self):
        game = await get_or_create_game()
        visitor_names, participant_names = await get_game_visitors_participants_names(game)
        response_data = {
            'action': 'server_state',
            'state': game.state,
            'visitors': visitor_names,
            'participants': participant_names,
        }
        await self.channel_layer.group_send(
            'all',
            {
                'type': 'send_message_to_group',
                'message': json.dumps(response_data),
            },
        )

    async def send_message_to_group(self, event):
        message = event['message']
        await self.send(text_data=message)

    async def send_game_state(self, game_state):
        await self.send(game_state)
        # await self.send(json.dumps(game_state))

    @staticmethod
    def get_user_short_name(channel_name):
        return channel_name[-4:]

    def get_user_group_name(self, channel_name):
        return f'group_{self.get_user_short_name(channel_name)}'

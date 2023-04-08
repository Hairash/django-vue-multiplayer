import json
import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.apps import apps

logger = logging.getLogger('django_vue_multiplayer')


@database_sync_to_async
def get_user(token_key):
    Token = apps.get_model('authtoken', 'Token')
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


class Player:
    def __init__(self, channel_name, user_name=None):
        self.channel_name = channel_name
        self.user_name = user_name

    def __repr__(self):
        return f"Player(channel_name={self.channel_name}, user_name={self.user_name})"


class GameConsumer(AsyncWebsocketConsumer):
    # players is a list because it's necessary to keep order of players
    players = []

    async def connect(self):
        logger.debug(f'=====> Connected player: {self.channel_name}')
        logger.debug(f'=====> Group: {self.get_player_group_name(self.channel_name)}')

        response_data = {'action': 'connected', 'player': self.get_player_short_name(self.channel_name)}
        await self.channel_layer.group_send(
            'all',
            {
                'type': 'send_message_to_group',
                'message': json.dumps(response_data),
            },
        )

        self.players.append(Player(self.channel_name))
        # logger.debug('Player appended')

        await self.channel_layer.group_add(
            self.get_player_group_name(self.channel_name),
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
            self.get_player_group_name(self.channel_name),
            self.channel_name,
        )
        # logger.debug('Disconnect player removed from the personal group')
        await self.channel_layer.group_discard(
            'all',
            self.channel_name,
        )
        # logger.debug('Disconnect player removed from the "all" group')

        response_data = {'action': 'disconnected', 'player': self.get_player_short_name(self.channel_name)}
        await self.channel_layer.group_send(
            'all',
            {
                'type': 'send_message_to_group',
                'message': json.dumps(response_data),
            },
        )
        # logger.debug('Disconnect send disconnected message')
        self.remove_player(self.channel_name)
        # logger.debug('Disconnect player removed from the list')
        await self.broadcast_list_of_players()
        logger.debug('=======> Disconnected')
        logger.debug(f'=======> Players: {self.players}')
        return

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Process the received data and generate a response
        # TODO: Make a list with possible messages
        if data['action'] == 'authenticate':
            token_key = data['token']
            user = await get_user(token_key)

            if user and not self.get_player_by_user_name(user.username):
                self.scope['user'] = user
                player = self.get_player_by_channel_name(self.channel_name)
                player.user_name = user.username
                await self.send(json.dumps({'action': 'authenticated'}))
                await self.broadcast_list_of_players()
            elif not user:
                await self.send(json.dumps({'action': 'error', 'message': 'Invalid token. Please re-login'}))
                await self.close()
            else:
                await self.send(json.dumps({'action': 'error', 'message': 'User is already connected'}))
                await self.close()
                # logger.debug('Connection closed')

        elif data['action'] == 'question':
            response_data = {'action': 'answer'}

            # Send the response back to the group (all connected players)
            await self.channel_layer.group_send(
                self.get_player_group_name(self.channel_name),
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

            # keys = list(self.players.keys())
            # next_player_name = keys[(keys.index(self.channel_name) + 1) % len(keys)]
            channel_names = [p.channel_name for p in self.players]
            next_player_idx = (channel_names.index(self.channel_name) + 1) % len(channel_names)
            logger.debug(f'=====> Next player id: {next_player_idx}')
            logger.debug(f'=====> Next player: {self.get_player_short_name(self.players[next_player_idx].channel_name)}')

            # Send the response back to the group (all connected players)
            await self.channel_layer.group_send(
                self.get_player_group_name(self.players[next_player_idx].channel_name),
                {
                    'type': 'send_message_to_group',
                    'message': json.dumps(response_data),
                },
            )

    async def broadcast_list_of_players(self):
        response_data = {
            'action': 'list',
            'players': [player.user_name for player in self.players],
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
    def get_player_short_name(channel_name):
        return channel_name[-4:]

    def get_player_group_name(self, channel_name):
        return f'group_{self.get_player_short_name(channel_name)}'

    def get_player_by_channel_name(self, channel_name):
        for player in self.players:
            if player.channel_name == channel_name:
                return player

    def get_player_by_user_name(self, user_name):
        for player in self.players:
            if player.user_name == user_name:
                return player

    def remove_player(self, channel_name):
        for player in self.players:
            if player.channel_name == channel_name:
                self.players.remove(player)

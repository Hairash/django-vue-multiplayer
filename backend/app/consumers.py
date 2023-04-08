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


class GameConsumer(AsyncWebsocketConsumer):
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

        self.players.append(self.channel_name)

        await self.channel_layer.group_add(
            self.get_player_group_name(self.channel_name),
            self.channel_name,
        )
        await self.channel_layer.group_add(
            'all',
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code, auth_failed=False):
        await self.channel_layer.group_discard(
            self.get_player_group_name(self.channel_name),
            self.channel_name,
        )
        await self.channel_layer.group_discard(
            'all',
            self.channel_name,
        )

        response_data = {'action': 'disconnected', 'player': self.get_player_short_name(self.channel_name)}
        await self.channel_layer.group_send(
            'all',
            {
                'type': 'send_message_to_group',
                'message': json.dumps(response_data),
            },
        )
        self.remove_player(self.channel_name)
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

            if user:
                self.scope['user'] = user
                await self.send(json.dumps({'action': 'authenticated'}))
                await self.broadcast_list_of_players()
            else:
                await self.send(json.dumps({'action': 'error', 'message': 'Invalid token. Please re-login'}))
                await self.close()

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
            next_player_idx = (self.players.index(self.channel_name) + 1) % len(self.players)
            logger.debug(f'=====> Next player id: {next_player_idx}')
            logger.debug(f'=====> Next player: {self.get_player_short_name(self.players[next_player_idx])}')

            # Send the response back to the group (all connected players)
            await self.channel_layer.group_send(
                self.get_player_group_name(self.players[next_player_idx]),
                {
                    'type': 'send_message_to_group',
                    'message': json.dumps(response_data),
                },
            )

    async def broadcast_list_of_players(self):
        response_data = {
            'action': 'list',
            'players': [self.get_player_short_name(player) for player in self.players],
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

    def remove_player(self, name):
        self.players.remove(name)

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class GameConsumer(AsyncWebsocketConsumer):
    players = {}

    async def connect(self):
        # Add the player to a group based on the game room
        cur_player = len(self.players)
        self.players[self.channel_name] = f'group{cur_player}'
        print(f'=====> Connected player: {self.channel_name}')
        print(f'=====> Group: {self.players[self.channel_name]}')

        await self.channel_layer.group_add(
            self.players[self.channel_name],
            self.channel_name,
        )
        await self.channel_layer.group_add(
            'all',
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.players[self.channel_name],
            self.channel_name,
        )
        await self.channel_layer.group_discard(
            'all',
            self.channel_name,
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Process the received data and generate a response
        if data['action'] == 'question':
            response_data = {'action': 'answer'}

            # Send the response back to the group (all connected players)
            await self.channel_layer.group_send(
                self.players[self.channel_name],
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

            keys = list(self.players.keys())
            next_player_name = keys[(keys.index(self.channel_name) + 1) % len(keys)]

            # Send the response back to the group (all connected players)
            await self.channel_layer.group_send(
                self.players[next_player_name],
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

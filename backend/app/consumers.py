import json
from channels.generic.websocket import AsyncWebsocketConsumer


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # data = json.loads(text_data)
        print(text_data)
        await self.send_game_state('1')
        # Process the received data and update the game state accordingly
        # Then, send the updated game state to all connected clients

    async def send_game_state(self, game_state):
        await self.send(game_state)
        # await self.send(json.dumps(game_state))

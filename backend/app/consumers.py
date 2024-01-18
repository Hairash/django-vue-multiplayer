import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import transaction

from app.services.helpers import GameError
from app.services.db_service import (
    add_visitor_to_game,
    check_end_game,
    clear_table,
    create_player,
    end_game,
    get_active_player_names,
    get_allowed_actions,
    get_current_player,
    get_current_player_user_name,
    get_game_visitors_participants_names,
    get_game_with_lock,
    get_next_player,
    get_or_create_game,
    get_participants,
    get_phase,
    get_player_by_channel_name,
    get_player_by_user,
    get_player_hand,
    get_table,
    get_user_by_token,
    init_current_player,
    init_participants,
    is_player_in_active_players,
    is_player_participant,
    play_card_to_table,
    prepare_end_game_message,
    remove_player,
    set_active_players,
    set_allowed_actions,
    set_current_player,
    set_game_state,
    set_phase,
    take_cards_from_table,
    toggle_active_players,
    toggle_phase,
    update_player_user,
)
from app.services.game_service import (
    check_stop_attack,
    generate_deck,
    start_new_turn,
)

from app.models import Game


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
    #==========================================#

    async def handle_start(self, data, game):
        if game.state != Game.States.NOT_STARTED:
            await self.send_error('Game has been already started')
            return

        await set_game_state(game, Game.States.GAME)
        await init_participants(game)
        await self.broadcast_server_state(game)

        await generate_deck(game)
        await init_current_player(game)
        await start_new_turn(game)

        await self.broadcast_game_state(game)
        await self.send_all_player_hands(game)
    #==========================================#

    async def handle_play(self, data, game):
        active_player = await get_player_by_channel_name(game, self.channel_name)
        if not await self.check_action_allowed(game, active_player):
            return

        card_dict = data['card']
        try:
            await play_card_to_table(game, active_player, card_dict)
        except GameError as e:
            await self.send_error(str(e))
            return

        current_player = await get_current_player(game)
        defender = await get_next_player(game, current_player)
        next_player = await get_next_player(game, defender)

        # If all allowed cards were played in the round
        if await check_stop_attack(game, defender):
            if game.phase == Game.Phases.DEFENSE:
                await clear_table(game)
                await set_current_player(game, defender)
            elif game.phase == Game.Phases.ADDITION:
                await take_cards_from_table(game, defender)
                await set_current_player(game, next_player)

            await self.process_end_of_turn(game)

        # Attackers add cards to defender's hand
        elif game.phase == Game.Phases.ADDITION:
            pass

        # Usual cases
        else:
            phase = await toggle_phase(game)
            if phase == Game.Phases.ATTACK:
                await toggle_active_players(game)
                await set_allowed_actions(game, [Game.Actions.PLAY, Game.Actions.PASS])
            else:
                await set_active_players(game, [defender])
                await set_allowed_actions(game, [Game.Actions.PLAY, Game.Actions.TAKE])

        await self.broadcast_game_state(game)
        await self.send_all_player_hands(game)
    #==========================================#

    async def handle_take(self, data, game):
        active_player = await get_player_by_channel_name(game, self.channel_name)
        if not await self.check_action_allowed(game, active_player):
            return

        await toggle_active_players(game)
        await set_phase(game, Game.Phases.ADDITION)
        await set_allowed_actions(game, [Game.Actions.PLAY, Game.Actions.PASS])

        await self.broadcast_game_state(game)
        await self.send_all_player_hands(game)
    #==========================================#

    async def handle_pass(self, data, game):
        active_player = await get_player_by_channel_name(game, self.channel_name)
        if not await self.check_action_allowed(game, active_player):
            return

        current_player = await get_current_player(game)
        defender = await get_next_player(game, current_player)
        next_player = await get_next_player(game, defender)

        # TODO: Logic. Make more wise handling - count number of passes
        # Current defender takes cards
        if game.phase == Game.Phases.ADDITION:
            await take_cards_from_table(game, defender)
            current_player = await set_current_player(game, next_player)

        # Current attacker passes
        else:
            await clear_table(game)
            # TODO: Refactoring. Make function to move current_player for 1 or 2 positions
            # (next or next after the next)
            await set_current_player(game, defender)

        await self.process_end_of_turn(game)

        await self.broadcast_game_state(game)
        await self.send_all_player_hands(game)
    #==========================================#

    async def handle_end(self, data, game):
        active_player = await get_player_by_channel_name(game, self.channel_name)
        if not is_player_participant(game, active_player):
            await self.send_error('Game is already in progress. Please wait for the end of the game.')
            return

        await end_game(game)
        await self.broadcast_server_state(game)
    #==========================================#

    # Action helpers

    async def process_end_of_turn(self, game):
        await self.send_all_player_hands(game)
        await start_new_turn(game)
        await self.check_and_process_end_game(game)
        await self.broadcast_server_state(game)

    async def check_and_process_end_game(self, game):
        if await check_end_game(game):
            end_game_message = await prepare_end_game_message(game)
            # await self.broadcast_game_state(game)
            await self.broadcast_data({'action': 'info', 'message': end_game_message})
            await end_game(game)

    async def check_action_allowed(self, game, active_player):
        if not await is_player_participant(game, active_player):
            await self.send_error('Game is already in progress. Please wait for the end of the game.')
            return False
        if not await is_player_in_active_players(game, active_player):
            await self.send_error('Please wait for your turn')
            return False
        return True

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
        # TODO: Add check if participant connected (if not - don't change state)
        # TODO: If yes - restart the game

        # Broadcast not needed here, because it is called on "authenticate" action

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
        with transaction.atomic():
            game = await get_game_with_lock()

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

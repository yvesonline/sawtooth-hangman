#!/usr/bin/env python3.5
# encoding: utf-8

import logging

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction

from state import Game, HmState, HM_NAMESPACE, GAME_STATE_ONGOING, GAME_STATE_WON, GAME_STATE_LOST
from payload import HmPayload

LOGGER = logging.getLogger(__name__)
MAX_GUESSES = 8


class HangmanTransactionHandler(TransactionHandler):
    # Disable invalid-overridden-method. The sawtooth-sdk expects these to be
    # properties.
    # pylint: disable=invalid-overridden-method
    @property
    def family_name(self):
        return "hm"

    @property
    def family_versions(self):
        return ["1.0"]

    @property
    def namespaces(self):
        return [HM_NAMESPACE]

    def apply(self, transaction, context):

        header = transaction.header

        signer = header.signer_public_key

        hm_payload = HmPayload.from_bytes(transaction.payload)

        hm_state = HmState(context)

        if hm_payload.action == "create":
            LOGGER.debug("Action: create")
            game = hm_state.get_game(hm_payload.name)
            if game:
                raise InvalidTransaction("Game '{}' already exists".format(hm_payload.name))
            game = Game(
                name=hm_payload.name,
                word=hm_payload.guess,
                misses="",
                hits="",
                host=signer,
                guesser="",
                state=GAME_STATE_ONGOING
            )
            hm_state.set_game(hm_payload.name, game)
            LOGGER.info("Player '{}' created game '{}'".format(signer, hm_payload.name))
        elif hm_payload.action == "delete":
            LOGGER.debug("Action: delete")
            try:
                hm_state.delete_game(hm_payload.name)
                LOGGER.info("Player '{}' deleted game '{}'".format(signer, hm_payload.name))
            except KeyError:
                raise InvalidTransaction("Game '{}' doesn't exist".format(hm_payload.name))
        elif hm_payload.action == "guess":
            LOGGER.debug("Action: guess")
            # Game doesn't exist
            game = hm_state.get_game(hm_payload.name)
            if not game:
                raise InvalidTransaction("Game '{}' doesn't exists".format(hm_payload.name))
            # Game has ended
            if game.state != GAME_STATE_ONGOING:
                raise InvalidTransaction("Game '{}' has already ended".format(hm_payload.name))
            # Guess already in hits
            if hm_payload.guess in game.hits:
                raise InvalidTransaction("You already guessed '{}' and it was successful".format(hm_payload.guess))
            # Guess already in misses
            if hm_payload.guess in game.misses:
                raise InvalidTransaction("You already guessed '{}' and it was not successful".format(hm_payload.guess))
            LOGGER.debug("Error handling completed")
            # Compute new game
            new_misses = game.misses + hm_payload.guess if hm_payload.guess not in game.word else game.misses
            new_hits = game.hits + hm_payload.guess if hm_payload.guess in game.word else game.hits
            if set(game.word) == set(new_hits):
                new_state = GAME_STATE_WON
            elif len(new_misses) >= MAX_GUESSES:
                new_state = GAME_STATE_LOST
            else:
                new_state = GAME_STATE_ONGOING
            new_game = Game(
                name=game.name,
                word=game.word,
                misses=new_misses,
                hits=new_hits,
                host=game.host,
                guesser=game.guesser,
                state=new_state
            )
            LOGGER.debug("New game computation completed")
            hm_state.set_game(hm_payload.name, new_game)
            LOGGER.info("""Game stats:
                Name: '{}'
                Word: '{}'
                Misses: '{}'
                Hits: '{}'
                Host: '{}'
                Guesser: '{}'
                State: '{}'
                """.format(game.name, game.word, new_misses, new_hits, game.host, game.guesser, new_state))
        else:
            raise InvalidTransaction("Unknown action '{}'".format(hm_payload.action))

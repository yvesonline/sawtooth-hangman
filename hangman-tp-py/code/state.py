#!/usr/bin/env python3.5
# encoding: utf-8

import logging
import hashlib

from cbor2 import dumps, loads

# Set up logging
LOGGER = logging.getLogger(__name__)

# The prefix for the Hangman address space, translates to `b89bcb`
HM_NAMESPACE = hashlib.sha512("hangman".encode("utf-8")).hexdigest()[0:6]

# Timeout used when reading/writing state
TIMEOUT = 3

# Game states, ongoing, won or lost
# We can't use `Enum` as we can't encode `Enum` with CBOR
GAME_STATE_ONGOING = 1
GAME_STATE_WON = 2
GAME_STATE_LOST = 3


def _make_hm_address(name):
    """
    Creates an address in the Hangman address space
    in order to store state information.

    E.g. for the game name "Game of Words":
    - `HM_NAMESPACE`  = `b89bcb`
    - `HM_GAME`       = `ee7c82d3cdfecf6d65c3c81be0c90e7fa015db96aafbe418e197cad7c52f0c34`
    We return `HM_NAMESPACE` + `HM_GAME` to uniquely identify games in the address space.

    Arguments:
        name: The name of the game.
    Returns:
        An address in the Hangman address space (70 characters long).
    """
    return HM_NAMESPACE + \
        hashlib.sha512(name.encode("utf-8")).hexdigest()[:64]


class Game:
    """
    A Hangman Game description, short `Game`.
    Information is stored in Concise Binary Object Representation,
    see https://en.wikipedia.org/wiki/CBOR, so we use `cbor2`
    to decode information here.

    Arguments:
        name: The name of the game.
        word: The word to guess.
        misses: What letters have been guessed and were misses.
        hits: What letters have been guessed and were hits.
        host: The host of the game.
        guesser: The guesser.
        state: The state of the game, see `GAME_STATE_*`
    """

    def __init__(self, name="", word="", misses="",
                 hits="", host="", guesser="", state=GAME_STATE_ONGOING):
        """
        Initializes Game with `name`, `word`,
        `misses`, `hits`, `host`, `guesser` and `state`.
        """
        self.name = name
        self.word = word
        self.misses = misses
        self.hits = hits
        self.host = host
        self.guesser = guesser
        self.state = state

    @classmethod
    def from_dict(cls, d):
        """
        Static method to create a Game instance from a dictionary.
        Be careful no error handling is done here!

        Arguments:
            d: A dictionary with the necessary information to populate a Game.
        Returns:
            A corresponding Game instance.
        """
        return cls(
            name=d["name"],
            word=d["word"],
            misses=d["misses"],
            hits=d["hits"],
            host=d["host"],
            guesser=d["guesser"],
            state=d["state"]
        )

    def to_dict(self):
        """
        Return dictionary presentation of the Game instance.

        Returns:
            A dictionary presentation of the Game instance.
        """
        return {
            "name": self.name,
            "word": self.word,
            "misses": self.misses,
            "hits": self.hits,
            "host": self.host,
            "guesser": self.guesser,
            "state": self.state,
        }


class HmState:
    """
    A Hangman State description, short `HmState`.
    Information is stored in Concise Binary Object Representation,
    see https://en.wikipedia.org/wiki/CBOR, so we use `cbor2`
    to decode information here.

    Arguments:
        context: The Sawtooth Transaction context.
    """

    def __init__(self, context):
        """Initializes Hangman State with `context`."""
        self._context = context

    def delete_game(self, name):
        """
        Delete game from state.

        Arguments:
            name: The name of the game to delete.
        Returns:
            -
        Raises:
            A `KeyError` if the game doesn't exist in the state.
        """
        game = self.get_game(name)
        if game:
            address = _make_hm_address(name)
            self._context.delete_state([address], timeout=TIMEOUT)
        else:
            raise KeyError

    def set_game(self, name, game):
        """
        Set new game information in the state.

        Arguments:
            name: The name of the game to set information for.
            game: The new game information to set.
        Returns:
            -
        """
        address = _make_hm_address(name)
        state_s = self._context.get_state([address], timeout=TIMEOUT)
        LOGGER.debug("Retrieved serialized state: {}".format(state_s))
        LOGGER.debug("length: {}".format(len(state_s)))
        LOGGER.debug("type: {}".format(type(state_s)))
        if len(state_s) > 0:
            state_de = loads(state_s[0].data)
        else:
            state_de = []
        state_de.append(game.to_dict())
        state_s = dumps(state_de)
        LOGGER.debug("Setting state: {} ({})".format(state_de, state_s))
        self._context.set_state({address: state_s}, timeout=TIMEOUT)

    def get_game(self, name):
        """
        Get game information from the state.

        Arguments:
            name: The name of the game to get information for.
        Returns:
            The game information or None if no information available.
        """
        address = _make_hm_address(name)
        state_s = self._context.get_state([address], timeout=TIMEOUT)
        LOGGER.debug("Retrieved serialized state: {}".format(state_s))
        LOGGER.debug("length: {}".format(len(state_s)))
        LOGGER.debug("type: {}".format(type(state_s)))
        if len(state_s) > 0:
            state_de = loads(state_s[0].data)
            LOGGER.debug("Retrieved deserialized state: {}".format(state_de))
            return Game.from_dict(state_de[-1])
        else:
            return None

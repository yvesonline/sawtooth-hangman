#!/usr/bin/env python3.5
# encoding: utf-8

import hashlib

from enum import Enum

from cbor2 import dumps, loads

from sawtooth_sdk.processor.exceptions import InternalError

HM_NAMESPACE = hashlib.sha512("hangman".encode("utf-8")).hexdigest()[0:6]
TIMEOUT = 3


def _make_hm_address(name):
    return HM_NAMESPACE + \
        hashlib.sha512(name.encode("utf-8")).hexdigest()[:64]


class GameState(Enum):
    ongoing = 1
    won = 2
    lost = 3


class Game:
    def __init__(self, name="", word="", misses="", hits="", host="", guesser="", state=GameState.ongoing):
        self.name = name
        self.word = word
        self.misses = misses
        self.hits = hits
        self.host = host
        self.guesser = guesser
        self.state = state

    @classmethod
    def from_dict(cls, d):
        return cls(
            d["name"],
            d["word"],
            d["misses"],
            d["hits"],
            d["host"],
            d["guesser"],
            d["state"]
        )

    def to_dict(self):
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
    def __init__(self, context):
        self._context = context

    def delete_game(self, name):
        game = self.get_game(name)
        if game:
            address = _make_hm_address(name)
            self._context.delete_state([address], timeout=TIMEOUT)
        else:
            raise KeyError

    def set_game(self, name, game):
        address = _make_hm_address(name)
        state_s = self._context.get_state([address], timeout=TIMEOUT)
        if state_s:
            state_de = loads(state_s)
        else:
            state_de = []
        state_de.append(game.to_dict())
        state_s = dumps(state_de)
        self._context.set_state({address: state_s}, timeout=TIMEOUT)

    def get_game(self, name):
        address = _make_hm_address(name)
        state_s = self._context.get_state([address], timeout=TIMEOUT)
        if state_s:
            state_de = loads(state_s)
            return Game.from_dict(state_de[-1])
        else:
            return None

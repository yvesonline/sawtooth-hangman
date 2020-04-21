#!/usr/bin/env python3.5
# encoding: utf-8

import logging

from cbor2 import loads

from sawtooth_sdk.processor.exceptions import InvalidTransaction

LOGGER = logging.getLogger(__name__)


class HmPayload:
    def __init__(self, payload):
        payload_de = loads(payload)
        if "name" not in payload_de:
            raise InvalidTransaction("Name is required")
        if "action" not in payload_de:
            raise InvalidTransaction("Action is required")
        if payload_de["action"] not in ["create", "delete", "guess"]:
            raise InvalidTransaction("Invalid action: '{}'".format(action))
        self._name = payload_de["name"]
        self._action = payload_de["action"]
        self._guess = payload_de["guess"]
        LOGGER.debug("Name: {}".format(payload_de["name"]))
        LOGGER.debug("Action: {}".format(payload_de["action"]))
        LOGGER.debug("Guess: {}".format(payload_de["guess"]))

    @staticmethod
    def from_bytes(payload):
        return HmPayload(payload=payload)

    @property
    def name(self):
        return self._name

    @property
    def action(self):
        return self._action

    @property
    def guess(self):
        return self._guess

#!/usr/bin/env python3.5
# encoding: utf-8

from sawtooth_sdk.processor.exceptions import InvalidTransaction


class HmPayload:
    def __init__(self, payload):
        try:
            # The payload is csv utf-8 encoded string
            name, action, guess = payload.decode().split(",")
        except ValueError:
            raise InvalidTransaction("Invalid payload serialization")
        if not name:
            raise InvalidTransaction("Name is required")
        if "|" in name:
            raise InvalidTransaction("Name cannot contain '|'")
        if not action:
            raise InvalidTransaction("Action is required")
        if action not in ("create", "delete", "guess"):
            raise InvalidTransaction("Invalid action: {}".format(action))
        self._name = name
        self._action = action
        self._guess = guess

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

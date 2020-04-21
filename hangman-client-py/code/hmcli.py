#!/usr/bin/env python3.5
# encoding: utf-8

import logging

import hashlib

import inquirer

import requests

from cbor2 import dumps

from colorlog import ColoredFormatter

from sawtooth_signing import create_context, CryptoFactory
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader, Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader, Batch, BatchList

APP_NAME = "Hangman CLI"

VALIDATOR_URL = "http://rest-api:8008"
VALIDATOR_ENDPOINT = "/batches"

HM_NAMESPACE = hashlib.sha512("hangman".encode("utf-8")).hexdigest()[0:6]

CHOICE_CREATE_GAME = "CREATE_GAME"
CHOICE_DELETE_GAME = "DELETE_GAME"
CHOICE_MAKE_A_GUESS = "MAKE_A_GUESS"
CHOICE_EXIT = "EXIT"
CHOICES = [
    ("Create game", CHOICE_CREATE_GAME),
    ("Delete game", CHOICE_DELETE_GAME),
    ("Make a guess", CHOICE_MAKE_A_GUESS),
    ("Exit", CHOICE_EXIT),
]


def create_console_handler(log_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s.%(msecs)03d "
        "%(levelname)-8s %(module)s %(lineno)d]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red",
        })
    clog.setFormatter(formatter)
    clog.setLevel(log_level)
    return clog


def init_logging(log_level=logging.DEBUG):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(create_console_handler(log_level))
    return logger


def _make_hm_address(name):
    return HM_NAMESPACE + \
        hashlib.sha512(name.encode("utf-8")).hexdigest()[:64]


class HangmanCLI:

    def __init__(self):
        """
        This initialises our main class.
        """
        # String to print in case a command finishes successfully
        self.success_symbol = u"\u2713"
        # String to print in case a command fails
        self.failure_symbol = u"\u2717"
        # The signer and the associated information
        self.private_key = None
        self.signer = None
        # Set up logger
        self.logger = init_logging()

    def send_message(self, name, action, guess):
        batch_list_bytes = self.create_message(name, action, guess)
        headers = {"Content-Type": "application/octet-stream"}
        r = requests.post(
            VALIDATOR_URL + VALIDATOR_ENDPOINT,
            data=batch_list_bytes,
            headers=headers
        )
        r.raise_for_status()

    def create_message(self, name, action, guess):
        payload_bytes = self.create_payload(name, action, guess)
        txn_header_bytes = self.create_txn_header(name, payload_bytes)
        txn_signature = self.signer.sign(txn_header_bytes)
        self.logger.debug("TXN Signature: {}".format(txn_signature))
        txn = Transaction(
            header=txn_header_bytes,
            header_signature=txn_signature,
            payload=payload_bytes
        )
        self.logger.debug("TXN: {}".format(txn))
        txns = [txn]
        batch_header_bytes = self.create_batch_header(txns)
        batch_signature = self.signer.sign(batch_header_bytes)
        self.logger.debug("BATCH Signature: {}".format(batch_signature))
        batch = Batch(
            header=batch_header_bytes,
            header_signature=batch_signature,
            transactions=txns
        )
        self.logger.debug("BATCH: {}".format(batch))
        return BatchList(batches=[batch]).SerializeToString()

    def create_txn_header(self, name, payload_bytes):
        txn_header = TransactionHeader(
            family_name="hm",
            family_version="1.0",
            inputs=[_make_hm_address(name)],
            outputs=[_make_hm_address(name)],
            signer_public_key=self.signer.get_public_key().as_hex(),
            batcher_public_key=self.signer.get_public_key().as_hex(),
            dependencies=[],
            payload_sha512=hashlib.sha512(payload_bytes).hexdigest()
        )
        self.logger.debug("TXN Header: {}".format(txn_header))
        return txn_header.SerializeToString()

    def create_batch_header(self, txns):
        batch_header = BatchHeader(
            signer_public_key=self.signer.get_public_key().as_hex(),
            transaction_ids=[txn.header_signature for txn in txns],
        )
        self.logger.debug("BATCH Header: {}".format(batch_header))
        return batch_header.SerializeToString()

    def create_payload(self, name, action, guess):
        payload = dumps({
            "name": name,
            "action": action,
            "guess": guess,
        })
        self.logger.debug("Payload: {}".format(payload))
        return payload

    def interactive_loop(self):
        context = create_context("secp256k1")
        print("""Provisioning a random private key, this is valid
and remembered until you exit the {}""".format(APP_NAME))
        self.private_key = context.new_random_private_key()
        self.signer = CryptoFactory(context).new_signer(self.private_key)
        choice = ""
        while choice != CHOICE_EXIT:
            choice = inquirer.list_input(
                "Please choose an action",
                choices=CHOICES
            )
            if choice == CHOICE_CREATE_GAME:
                self.interactive_loop_create_game()
            elif choice == CHOICE_DELETE_GAME:
                self.interactive_loop_delete_game()
            elif choice == CHOICE_MAKE_A_GUESS:
                self.interactive_loop_make_a_guess()

    def interactive_loop_create_game(self):
        name = inquirer.text(message="Enter game name")
        word = inquirer.text(message="Enter word to guess")
        self.send_message(name, "create", word)

    def interactive_loop_delete_game(self):
        name = inquirer.text(message="Enter game name")
        self.send_message(name, "delete", "")

    def interactive_loop_make_a_guess(self):
        name = inquirer.text(message="Enter game name")
        guess = ""
        while len(guess) == 0 or len(guess) > 1:
            guess = inquirer.text(message="Type a letter to guess...")
        self.send_message(name, "guess", guess)

    def process(self):
        # Enter interactive loop
        self.interactive_loop()


if __name__ == "__main__":
    hmcli = HangmanCLI()
    hmcli.process()

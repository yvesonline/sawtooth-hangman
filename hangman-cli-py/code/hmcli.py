#!/usr/bin/env python3.5
# encoding: utf-8

import logging

import hashlib

import base64

import re

import string

import inquirer

import requests

from cbor2 import dumps, loads

from colorlog import ColoredFormatter

from time import sleep

from sawtooth_signing import create_context, CryptoFactory
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader, Batch, BatchList

from hmascii import HANGMAN

APP_NAME = "Hangman CLI"

VALIDATOR_URL = "http://rest-api:8008"
VALIDATOR_ENDPOINT_BATCHES = VALIDATOR_URL + "/batches"
VALIDATOR_ENDPOINT_STATE = VALIDATOR_URL + "/state/{}"
VALIDATOR_ENDPOINT_BLOCKS = VALIDATOR_URL + "/blocks?limit={}"

HM_NAMESPACE = hashlib.sha512("hangman".encode("utf-8")).hexdigest()[0:6]

CHOICE_CREATE_GAME = "CREATE_GAME"
CHOICE_DELETE_GAME = "DELETE_GAME"
CHOICE_MAKE_A_GUESS = "MAKE_A_GUESS"
CHOICE_GET_LIST_OF_BLOCKS = "GET_LIST_OF_BLOCKS"
CHOICE_EXIT = "EXIT"
CHOICES = [
    ("Create game", CHOICE_CREATE_GAME),
    ("Delete game", CHOICE_DELETE_GAME),
    ("Make a guess", CHOICE_MAKE_A_GUESS),
    ("Get list of blocks", CHOICE_GET_LIST_OF_BLOCKS),
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

    def send_get_message(self, url):
        r = requests.get(url)
        return r.json()

    def decode(self, data):
        return base64.b64decode(data)

    def send_post_message(self, name, action, guess):
        batch_list_bytes = self.create_message(name, action, guess)
        headers = {"Content-Type": "application/octet-stream"}
        r = requests.post(
            VALIDATOR_ENDPOINT_BATCHES,
            data=batch_list_bytes,
            headers=headers
        )
        ret_json = r.json()
        self.logger.debug("POST RETURN: {}".format(ret_json))
        r.raise_for_status()
        if "link" in ret_json:
            return ret_json["link"]

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
            elif choice == CHOICE_GET_LIST_OF_BLOCKS:
                self.interactive_loop_get_list_of_blocks()

    def interactive_loop_create_game(self):
        name = inquirer.text(message="Enter game name")
        word = inquirer.text(message="Enter word to guess")
        self.send_post_message(name, "create", word)
        print("Created game '{}' {}".format(name, self.success_symbol))

    def interactive_loop_delete_game(self):
        name = inquirer.text(message="Enter game name")
        self.send_post_message(name, "delete", "")
        print("Deleted game '{}' {}".format(name, self.success_symbol))

    def interactive_loop_get_list_of_blocks(self):
        number_of_blocks = 0
        number_of_blocks_to_display = 1000
        blocks = self.send_get_message(
            VALIDATOR_ENDPOINT_BLOCKS.format(number_of_blocks_to_display, 0)
        )
        number_of_blocks += len(blocks["data"])
        if number_of_blocks == number_of_blocks_to_display:
            print("Number of blocks: {}+".format(number_of_blocks))
        else:
            print("Number of blocks: {}".format(number_of_blocks))
        for block in blocks["data"]:
            print(86 * "-")
            print("Block number:      {:s}".format(block["header"]["block_num"]))
            print("Number of batches: {:d} ({})".format(
                len(block["header"]["batch_ids"]),
                ", ".join(["batch {}: {} txn".format(idx, len(tx["transactions"])) for idx, tx in enumerate(block["batches"])])
            ))
            print("Block id:          ...{}".format(
                block["header_signature"][-64:] if len(block["header_signature"]) > 64 else block["header_signature"]
            ))
            print("Previous block id: ...{}".format(
                block["header"]["previous_block_id"][-64:] if len(block["header"]["previous_block_id"]) > 64 else block["header"]["previous_block_id"]
            ))
        print("")

    def interactive_loop_make_a_guess(self):
        name = inquirer.text(message="Enter game name")
        self.sub_interactive_loop_make_a_guess(name)

    def sub_interactive_loop_make_a_guess(self, name):
        guess = ""
        while len(guess) == 0 or len(guess) > 1:
            guess = inquirer.text(message="Type a letter to guess...")
        link = self.send_post_message(name, "guess", guess)
        if link:
            status = "PENDING"
            counter = 0
            while status == "PENDING":
                ret_json = self.send_get_message(link)
                status = ret_json["data"][0]["status"]
                counter += 1
                sleep(1)
                if counter >= 10:
                    break
        state = self.send_get_message(
            VALIDATOR_ENDPOINT_STATE.format(_make_hm_address(name))
        )
        decoded_state = self.decode(state["data"])
        game = loads(decoded_state)
        current_game = game[-1]
        self.print_game(current_game)
        if current_game["state"] == 1:
            again = inquirer.confirm("Guess again?", default=True)
            if again:
                self.sub_interactive_loop_make_a_guess(name)

    def print_game(self, game):
        print("{}".format(HANGMAN[len(game["misses"])]))
        hits = game["hits"]
        hidden_lower = list(set(string.ascii_lowercase) - set(hits))
        hidden_upper = list(set(string.ascii_uppercase) - set(hits.upper()))
        hidden = hidden_lower + hidden_upper
        word = game["word"]
        misses = game["misses"]
        print("Word:\t{}".format(re.sub("|".join([h for h in hidden]), "_", word)))
        print("Misses:\t{}".format(" ".join([m for m in misses])))
        if game["state"] == 1:
            print("State:\tKEEP GOING ;-)")
        elif game["state"] == 2:
            print("State:\tYOU WON :-)")
        elif game["state"] == 3:
            print("State:\tGAME OVER :-(")
        print("")

    def process(self):
        # Enter interactive loop
        self.interactive_loop()


if __name__ == "__main__":
    hmcli = HangmanCLI()
    hmcli.process()

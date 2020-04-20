#!/usr/bin/env python3.5
# encoding: utf-8

import logging
import argparse

import inquirer

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory

APP_NAME = "Hangman CLI"

CHOICE_CREATE_GAME = "CREATE_GAME"
CHOICE_DELETE_GAME = "DELETE_GAME"
CHOICE_TAKE_A_GUESS = "TAKE_A_GUESS"
CHOICE_EXIT = "EXIT"
CHOICES = [
    ("Create game", CHOICE_CREATE_GAME),
    ("Delete game", CHOICE_DELETE_GAME),
    ("Take a guess", CHOICE_TAKE_A_GUESS),
    ("Exit", CHOICE_EXIT),
]


class HangmanCLI:

    def __init__(self):
        """
        This initialises our main class.
        """
        # String to print in case a command finishes successfully
        self.success_symbol = u"\u2713"
        # String to print in case a command fails
        self.failure_symbol = u"\u2717"

    def interactive_loop(self):
        text = inquirer.text(message="Enter your name")
        context = create_context("secp256k1")
        print("""Provisioning a random private key, this is valid
            and remembered until you exit the {}""".format(APP_NAME))
        private_key = context.new_random_private_key()
        signer = CryptoFactory(context).new_signer(private_key)
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
            elif choice == CHOICE_TAKE_A_GUESS:
                self.interactive_loop_take_a_guess()

    def interactive_loop_create_game(self):
        pass

    def interactive_loop_delete_game(self):
        pass

    def interactive_loop_take_a_guess(self):
        pass

    def process(self):
        # Enter interactive loop
        self.interactive_loop()


if __name__ == "__main__":
    hmcli = HangmanCLI()
    hmcli.process()

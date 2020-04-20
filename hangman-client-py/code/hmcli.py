#!/usr/bin/env python3.5
# encoding: utf-8

import logging
import argparse

import inquirer

APP_NAME = "Hangman CLI"


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

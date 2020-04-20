#!/usr/bin/env python3.5
# encoding: utf-8

import logging
import argparse

from colorlog import ColoredFormatter

from sawtooth_sdk.processor.core import TransactionProcessor

from handler import HangmanTransactionHandler

APP_NAME = "Hangman Transaction Processor"


def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s.%(msecs)03d "
        "%(levelname)-8s %(module)s]%(reset)s "
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
    clog.setLevel(logging.DEBUG)
    return clog


def init_logging(log_level=logging.DEBUG):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(create_console_handler(log_level))


if __name__ == "__main__":
    # Declare the arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=APP_NAME)
    parser.add_argument(
        "--validator",
        dest="validator",
        default="tcp://127.0.0.1:4004",
        help="The validator to connect to",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Set up logging
    init_logging()

    # Start listening
    processor = None
    try:
        processor = TransactionProcessor(url=args.validator)
        handler = HangmanTransactionHandler()
        processor.add_handler(handler)
        processor.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:  # pylint: disable=broad-except
        print("Error: {}".format(e))
    finally:
        if processor is not None:
            processor.stop()

#!/usr/bin/env python3.5
# encoding: utf-8

from sawtooth_sdk.processor.handler import TransactionHandler

from state import HM_NAMESPACE


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

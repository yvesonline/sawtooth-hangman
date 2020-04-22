#!/usr/bin/env python3.5
# encoding: utf-8

import logging

import zmq.green as zmq

from flask_sockets import Sockets
from flask import Flask, render_template, send_from_directory

from sawtooth_sdk.protobuf.events_pb2 import EventSubscription, EventFilter, EventList
from sawtooth_sdk.protobuf.client_event_pb2 import ClientEventsSubscribeRequest, ClientEventsSubscribeResponse
from sawtooth_sdk.protobuf.validator_pb2 import Message

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)

app = Flask(__name__)
sockets = Sockets(app)

HOST = "validator"
PORT = 4004

ctx = zmq.Context()
socket = ctx.socket(zmq.DEALER)
socket.connect("tcp://{}:{}".format(HOST, PORT))


def set_up_zmq_subscription():
    subscription = EventSubscription(
        event_type="sawtooth/state-delta",
        filters=[
            EventFilter(
                key="address",
                match_string="b89bcb.*",
                filter_type=EventFilter.REGEX_ANY)
        ])

    request = ClientEventsSubscribeRequest(subscriptions=[subscription]).SerializeToString()

    correlation_id = "123"  # This must be unique for all in-process requests
    msg = Message(
        correlation_id=correlation_id,
        message_type=Message.MessageType.CLIENT_EVENTS_SUBSCRIBE_REQUEST,
        content=request
    )

    socket.send_multipart([msg.SerializeToString()])

    resp = socket.recv_multipart()[-1]

    msg = Message()
    msg.ParseFromString(resp)

    if msg.message_type != Message.MessageType.CLIENT_EVENTS_SUBSCRIBE_RESPONSE:
        print("Unexpected message type")
        exit(1)

    response = ClientEventsSubscribeResponse()
    response.ParseFromString(msg.content)

    if response.status != ClientEventsSubscribeResponse.OK:
        print("Subscription failed: {}".format(response.response_message))
        exit(1)

    LOGGER.debug("Setting up ZMQ subscription successful")


@sockets.route("/zmq")
def zmq_socket(ws):
    LOGGER.debug("Entering ZMQ loop")
    while True:
        resp = socket.recv_multipart()[-1]

        # Parse the message wrapper
        msg = Message()
        msg.ParseFromString(resp)

        # Validate the response type
        if msg.message_type == Message.CLIENT_EVENTS:
            # Parse the response
            events = EventList()
            events.ParseFromString(msg.content)
            LOGGER.debug("Received events")
            LOGGER.debug(events)
            # for event in events:
            #     print(event)
            # Eventually what we want to do here is ws.send(events)
            # But before we have to unpack it!!!
        elif msg.message_type == Message.PING_REQUEST:
            LOGGER.debug("Received ping request")
            ws.send("ping request")
        else:
            LOGGER.warn("Unexpected message type '{}'".format(msg.message_type))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    set_up_zmq_subscription()
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(("", 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()

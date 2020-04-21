#!/usr/bin/env python3.5
# encoding: utf-8

import zmq

from sawtooth_sdk.protobuf.events_pb2 import EventSubscription, EventFilter, EventList
from sawtooth_sdk.protobuf.client_event_pb2 import ClientEventsSubscribeRequest, ClientEventsSubscribeResponse
from sawtooth_sdk.protobuf.validator_pb2 import Message

subscription = EventSubscription(
    event_type="sawtooth/state-delta",
    filters=[
        EventFilter(
            key="address",
            match_string="b89bcb.*",
            filter_type=EventFilter.REGEX_ANY)
    ])

ctx = zmq.Context()
socket = ctx.socket(zmq.DEALER)
socket.connect("tcp://{}:{}".format("validator", 4004))

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
        print(events)
        # for event in events:
        #     print(event)
    elif msg.message_type == Message.PING_REQUEST:
        print("Received ping request")
    else:
        print("Unexpected message type '{}'".format(msg.message_type))

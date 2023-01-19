# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Installable Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2022 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
"""
=======
Toy VTN
=======

This VTN is to be used for testing the VolttronOpenADRVEN agent. This VTN will emit an Event to be polled by the VolttronOpenADRVEN agent, which in
turn will process the Event and then publish the Event on the Volttron message bus.

Events are informational or instructional messages from the server (VTN) which inform you of price changes, request load reduction, et cetera.
The Event to be published has a single signal with an OpenADR name of "simple" and is of OpenADR type "level". This Event will have exactly one interval with a
start time of now and end time of now + five minutes; the payload will be 100.0. When a VolttronOpenADRVEN agent is installed using the
config_toy_ven.json agent configuration, the agent is expected to poll this Event from the toy VTN. Once the VEN has polled the Event, the VTN
will stop sending out the Event.
"""

import os
import asyncio
import time
from datetime import datetime, timezone, timedelta
from openleadr import OpenADRServer, enable_default_logging
from functools import partial

enable_default_logging()

PORT = os.getenv("VTN_PORT", 8080)
VALID_VENS = {
    'ven123': {
        'ven_id': 'ven_id_123',
        'reg_id': 'reg_id_123'
    },
}


async def on_create_party_registration(registration_info):
    """
    Inspect the registration info and return a ven_id and registration_id.
    """
    print("\n\n\n\nREGISTERING VEN...")
    # Check whether this VEN is allowed to register
    # insert your business logic here (e.g. look up the VEN in some database)
    ven_info = VALID_VENS.get(registration_info['ven_name'], None)
    if ven_info is None:
        return False
    return ven_info.get('ven_id'), ven_info.get('reg_id')


async def on_register_report(ven_id, resource_id, measurement, unit, scale,
                             min_sampling_interval, max_sampling_interval):
    """
    Inspect a report offering from the VEN and return a callback and sampling interval for receiving the reports.
    """
    # if necessary, add business logic on whether to register a report
    # the partial function creates a version of your callback with default parameters filled in
    callback = partial(process_individual_report,
                       ven_id=ven_id,
                       resource_id=resource_id,
                       measurement=measurement)
    sampling_interval = min_sampling_interval
    return callback, sampling_interval


async def process_individual_report(data, ven_id, resource_id, measurement):
    """
    Callback that receives report data from the VEN and handles it.
    """
    for time_t, value in data:
        print("\n\n\n\nRECEIVED REPORT FROM VEN")
        print(
            f"ven_id: {ven_id}\n Device: {resource_id}\n Measurement: {measurement}\n Value: {value}\n Time: {time_t}"
        )
        # Add business logic to act on report data
        # For example, you can insert report data into some database
        # or use it as an input to an algorithm that manages energy control
        # In the example below, regardless of the measurement, our VTN server
        # will send an event back to the VEN
        print("\n\n\n\nPROCESSING REPORT DATA")
        time.sleep(3)
        print("\n\n\n\nSENDING EVENT TO VEN")
        server.add_event(ven_id=ven_id,
                         signal_name='simple',
                         signal_type='level',
                         intervals=[{
                             'dtstart':
                             datetime.now(timezone.utc) + timedelta(minutes=5),
                             'duration':
                             timedelta(minutes=60),
                             'signal_payload':
                             100.0
                         }],
                         callback=event_response_callback)


async def event_response_callback(ven_id, event_id, opt_type):
    """
    Callback that receives the response from a VEN to an Event.
    """
    print(
        f"\n\n\n\nVEN {ven_id} RESPONDED TO EVENT {event_id} WITH RESPONSE: {opt_type}"
    )


def ven_lookup(ven_id):
    return {
        'ven_id': 'ven_id_123',
        'ven_name': 'ven123',
    }


# Create the server object
server = OpenADRServer(vtn_id='myvtn', http_port=PORT)

# Add the handler for client (VEN) registrations
server.add_handler('on_create_party_registration',
                   on_create_party_registration)

# Add the handler for report registrations from the VEN
server.add_handler('on_register_report', on_register_report)

# Run the server on the asyncio event loop
loop = asyncio.new_event_loop()
loop.create_task(server.run())
loop.run_forever()

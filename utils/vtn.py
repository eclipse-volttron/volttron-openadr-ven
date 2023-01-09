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

import asyncio
from datetime import datetime, timezone, timedelta
from openleadr import OpenADRServer, enable_default_logging
from functools import partial

enable_default_logging()


async def on_create_party_registration(registration_info):
    """
    Inspect the registration info and return a ven_id and registration_id.
    """
    print(f"PARTY REGISTRTION")
    if registration_info['ven_name'] == 'ven123':
        ven_id = 'ven_id_123'
        registration_id = 'reg_id_123'
        return ven_id, registration_id
    else:
        return False


async def on_register_report(ven_id, resource_id, measurement, unit, scale,
                             min_sampling_interval, max_sampling_interval):
    """
    Inspect a report offering from the VEN and return a callback and sampling interval for receiving the reports.
    """
    callback = partial(on_update_report,
                       ven_id=ven_id,
                       resource_id=resource_id,
                       measurement=measurement)
    sampling_interval = min_sampling_interval
    return callback, sampling_interval


async def on_update_report(data, ven_id, resource_id, measurement):
    """
    Callback that receives report data from the VEN and handles it.
    """
    for time, value in data:
        print(
            f"Ven {ven_id} reported {measurement} = {value} at time {time} for resource {resource_id}"
        )


async def event_response_callback(ven_id, event_id, opt_type):
    """
    Callback that receives the response from a VEN to an Event.
    """
    print(f"VEN {ven_id} responded to Event {event_id} with: {opt_type}")


def ven_lookup(ven_id):
    return {
        'ven_id': 'ven_id_123',
        'ven_name': 'ven123',
    }


# Create the server object
server = OpenADRServer(vtn_id='myvtn')

# Add the handler for client (VEN) registrations
server.add_handler('on_create_party_registration',
                   on_create_party_registration)

# Add the handler for report registrations from the VEN
server.add_handler('on_register_report', on_register_report)

# Add a prepared event for a VEN that will be picked up when it polls for new messages.
server.add_event(ven_id='ven_id_123',
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

# Run the server on the asyncio event loop
loop = asyncio.get_event_loop()
loop.create_task(server.run())
loop.run_forever()

# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright 2020, Battelle Memorial Institute.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This material was prepared as an account of work sponsored by an agency of
# the United States Government. Neither the United States Government nor the
# United States Department of Energy, nor Battelle, nor any of their
# employees, nor any jurisdiction or organization that has cooperated in the
# development of these materials, makes any warranty, express or
# implied, or assumes any legal liability or responsibility for the accuracy,
# completeness, or usefulness or any information, apparatus, product,
# software, or process disclosed, or represents that its use would not infringe
# privately owned rights. Reference herein to any specific commercial product,
# process, or service by trade name, trademark, manufacturer, or otherwise
# does not necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors expressed
# herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY operated by
# BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
# }}}
import logging
import asyncio
import sys
import gevent

from pathlib import Path
from pprint import pformat
from datetime import timedelta
from typing import Callable

from openleadr.enums import OPT, REPORT_NAME, MEASUREMENTS
from openleadr.client import OpenADRClient
from openleadr.objects import Event

from . import (
    get_aware_utc_now,
    setup_logging,
    format_timestamp,
    load_config,
    jsonapi,
    topics,
    headers,
    Agent,
    vip_main,
    RPC,
)

from volttron_openadr_ven.constants import (
    REQUIRED_KEYS,
    VEN_NAME,
    VTN_URL,
    DEBUG,
    CERT,
    KEY,
    PASSPHRASE,
    VTN_FINGERPRINT,
    SHOW_FINGERPRINT,
    CA_FILE,
    VEN_ID,
    DISABLE_SIGNATURE,
    OPENADR_CLIENT_TYPE,
    IDENTITY,
)
from .volttron_openadr_client import openadr_clients

setup_logging()
_log = logging.getLogger(__name__)
__version__ = "1.0"


class OpenADRVenAgent(Agent):
    """This is class is a subclass of the Volttron Agent; it is an OpenADR VEN client and is a wrapper around OpenLEADR,
    an open-source implementation of OpenADR 2.0.b for both servers, VTN, and clients, VEN.
    This agent creates an instance of OpenLEADR's VEN client, which is used to communicated with a VTN.
    OpenADR (Automated Demand Response) is a standard for alerting and responding
    to the need to adjust electric power consumption in response to fluctuations in grid demand.
    OpenADR communications are conducted between Virtual Top Nodes (VTNs) and Virtual End Nodes (VENs).

    :param config_path: The path to the configuration of this agent
    :type config_path: str
    """

    def __init__(self, config_path: str, **kwargs) -> None:
        super(OpenADRVenAgent, self).__init__(enable_web=True, **kwargs)

        self.default_config = self.parse_config(config_path)

        # SubSystem/ConfigStore
        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(
            self.configure_ven_client,
            actions=["NEW", "UPDATE"],
            pattern="config",
        )

        self.ven_client: OpenADRClient

    def configure_ven_client(
        self, config_name: str, action: str, contents: dict
    ) -> None:
        """Initializes the agent's configuration and creates an OpenADR Client using OpenLeadr.

        :param config_name:
        :type config_name: str
        :param action: the action
        :type action: str
        :param contents: the configuration used to update the agent's configuration
        :type contents: dict

        :return: None
        :rtype: None
        """
        config = self.default_config.copy()
        config.update(contents)

        _log.info(f"config_name: {config_name}, action: {action}")
        _log.info(f"Configuring agent with: \n {pformat(config)} ")

        # instantiate VEN client
        client_type = config.get(OPENADR_CLIENT_TYPE)
        openADRClient = openadr_clients().get(client_type)
        if openADRClient is None:
            msg = f"Invalid client type: {client_type}. Please use valid client types: {list(openadr_clients().keys())}"
            _log.debug(msg)
            raise KeyError(msg)

        _log.info(f"Creating OpenADRClient type: {client_type}...")
        self.ven_client = openADRClient(
            config.get(VEN_NAME),
            config.get(VTN_URL),
            debug=config.get(DEBUG),
            cert=config.get(CERT),
            key=config.get(KEY),
            passphrase=config.get(PASSPHRASE),
            vtn_fingerprint=config.get(VTN_FINGERPRINT),
            show_fingerprint=config.get(SHOW_FINGERPRINT),
            ca_file=config.get(CA_FILE),
            ven_id=config.get(VEN_ID),
            disable_signature=config.get(DISABLE_SIGNATURE),
        )
        _log.info(f"{client_type} successfully created.")

        _log.info(
            f"Adding capabilities (e.g. handlers, reports) to {client_type}..."
        )
        # Add event handling capability to the client
        # if you want to add more handlers on a specific event, you must create a coroutine in this class
        # and then add it as the second input for 'self.ven_client.add_handler(<some event>, <coroutine>)'
        self.ven_client.add_handler("on_event", self.handle_event)

        _log.info("Capabilities successfully added.")
        gevent.spawn_later(3, self.start_asyncio_loop)

    def start_asyncio_loop(self):
        """ Starts event loop

        :return: None
        :rtype: None
        """
        _log.info("Starting agent...")
        loop = asyncio.get_event_loop()
        loop.create_task(self.ven_client.run())
        loop.run_forever()

    # ***************** Methods for Servicing VTN Requests ********************

    async def handle_event(self, event: Event) -> OPT:
        """Publish event to the Volttron message bus. This coroutine will be called when there is an event to be handled.

        :param event: The event sent from a VTN
        :Example:

        {
            'event_id': '123786-129831',
            'active_period': {'dtstart': datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                              'duration': datetime.timedelta(minutes=30)}
            'event_signals': [{'signal_name': 'simple',
                               'signal_type': 'level',
                               'intervals': [{'dtstart': datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                                              'duration': datetime.timedelta(minutes=10),
                                              'signal_payload': 1},
                                              {'dtstart': datetime.datetime(2020, 1, 1, 12, 10, 0, tzinfo=timezone.utc),
                                              'duration': datetime.timedelta(minutes=10),
                                              'signal_payload': 0},
                                              {'dtstart': datetime.datetime(2020, 1, 1, 12, 20, 0, tzinfo=timezone.utc),
                                              'duration': datetime.timedelta(minutes=10),
                                              'signal_payload': 1}],
           'targets': [{'resource_id': 'Device001'}],
           'targets_by_type': {'resource_id': ['Device001']}
        }

        :return: Message to VTN to opt in to the event.
        :rtype: openleadr.enums.OPT
        """
        try:
            _log.debug("Received event. Processing event now...")
            signal = event.get("event_signals")[0]
            _log.info(f"Event signal:\n {pformat(signal)}")
        except IndexError as e:
            _log.debug(
                f"Event signals is empty. {e} \n Showing whole event: {pformat(event)}"
            )
            pass

        self.publish_event(event)

        return OPT.OPT_IN

    @RPC
    def add_report_capability(
        self,
        callback: Callable,
        report_name: REPORT_NAME,
        resource_id: str,
        measurement: MEASUREMENTS,
    ) -> tuple:
        """Add a new reporting capability to the client.

        :param callback: A callback or coroutine that will fetch the value for a specific report. This callback will be passed the report_id and the r_id of the requested value.
        :type callback: Callable
        :param report_name: An OpenADR name for this report
        :type report_name: REPORT_NAME
        :param resource_id: A specific name for this resource within this report.
        :type resource_id: str
        :param measurement: The quantity that is being measured
        :type measurement: MEASUREMENTS
        :return: Returns a report_specifier_id (str) and an r_id (str) an identifier for OpenADR messages
        :rtype: tuple
        """
        report_specifier_id, r_id = self.ven_client.add_report(
            callback=callback,
            report_name=report_name,
            resource_id=resource_id,
            measurement=measurement,
        )
        _log.info(
            f"Output from add_report: report_specifier_id: {report_specifier_id}, r_id: {r_id}"
        )
        return report_specifier_id, r_id

    # ***************** VOLTTRON Pub/Sub Requests ********************
    def publish_event(self, event: Event) -> None:
        """Publish an event to the Volttron message bus. When an event is created/updated, it is published to the VOLTTRON bus with a topic that includes 'openadr/event_update'.

        :param event: The Event received from the VTN
        :type event: Event
        :return: None
        :rtype: None
        """
        # OADR rule 6: If testEvent is present and != "false", handle the event as a test event.
        try:
            if event["event_descriptor"]["test_event"]:
                _log.debug("Suppressing publication of test event")
                return
        except KeyError as e:
            _log.debug(f"Key error: {e}")
            pass

        _log.debug(f"Publishing real/non-test event \n {pformat(event)}")
        self.vip.pubsub.publish(
            peer="pubsub",
            topic=f"{topics.OPENADR_EVENT}/{self.ven_client.ven_name}",
            headers={headers.TIMESTAMP: format_timestamp(get_aware_utc_now())},
            message=OpenADRVenAgent.to_json_object(event),
        )

        return

    # ***************** Helper methods ********************
    @staticmethod
    def to_json_object(obj: Event):
        """Ensure that an object is valid JSON by dumping it with json_converter and then reloading it.

        :param obj: The event received from a VTN
        :type obj: Event
        :return: A deserialized Event that is converted into a python object
        :rtype: Any
        """
        obj_string = jsonapi.dumps(
            obj,
            default=lambda x: int(x.total_seconds())
            if isinstance(x, timedelta)
            else None,
        )
        return jsonapi.loads(obj_string)

    def parse_config(self, config_path: str) -> dict:
        """Parses the OpenADR agent's configuration file.

        :param config_path: The path to the configuration file
        :type config_path: str
        :return: The configuration
        :rtype: dict
        """
        try:
            config = load_config(config_path)
        except NameError as err:
            _log.exception(err)
            raise
        except Exception as err:
            _log.error("Error loading configuration: {}".format(err))
            config = {}

        if not config:
            raise Exception("Configuration cannot be empty.")

        req_keys_actual = {k: "" for k in REQUIRED_KEYS}
        for required_key in REQUIRED_KEYS:
            key_actual = config.get(required_key)
            self.check_required_key(required_key, key_actual)
            req_keys_actual[required_key] = key_actual

            # optional configurations
        debug = config.get(DEBUG)

        # keypair paths
        cert = config.get(CERT)
        if cert:
            cert = str(Path(cert).expanduser().resolve(strict=True))
        key = config.get(KEY)
        if key:
            key = str(Path(key).expanduser().resolve(strict=True))

        ven_name = config.get(VEN_NAME)
        vtn_url = config.get(VTN_URL)
        passphrase = config.get(PASSPHRASE)
        vtn_fingerprint = config.get(VTN_FINGERPRINT)
        show_fingerprint = bool(config.get(SHOW_FINGERPRINT))
        ca_file = config.get(CA_FILE)
        ven_id = config.get(VEN_ID)
        disable_signature = bool(config.get(DISABLE_SIGNATURE))
        openadr_client_type = config.get(OPENADR_CLIENT_TYPE)

        return {
            VEN_NAME: ven_name,
            VTN_URL: vtn_url,
            DEBUG: debug,
            CERT: cert,
            KEY: key,
            PASSPHRASE: passphrase,
            VTN_FINGERPRINT: vtn_fingerprint,
            SHOW_FINGERPRINT: show_fingerprint,
            CA_FILE: ca_file,
            VEN_ID: ven_id,
            DISABLE_SIGNATURE: disable_signature,
            OPENADR_CLIENT_TYPE: openadr_client_type,
        }

    def check_required_key(self, required_key: str, key_actual: str) -> None:
        """Checks if the given key and its value are required by this agent

        :param required_key: the key that is being checked
        :type required_key: str
        :param key_actual: the key value being checked
        :type key_actual: str
        :raises KeyError:
        :return: None
        :rtype: None
        """
        if required_key == VEN_NAME and not key_actual:
            raise KeyError(f"{VEN_NAME} is required.")
        elif required_key == VTN_URL and not key_actual:
            raise KeyError(
                f"{VTN_URL} is required. Ensure {VTN_URL} is given a URL to the VTN."
            )
        elif required_key == OPENADR_CLIENT_TYPE and not key_actual:
            raise KeyError(
                f"{OPENADR_CLIENT_TYPE} is required. Specify one of the following valid client types: {list(openadr_clients().keys())}"
            )
        return


def main():
    """Main method called to start the agent."""
    vip_main(OpenADRVenAgent, IDENTITY)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass

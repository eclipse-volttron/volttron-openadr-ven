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

from pathlib import Path
from pprint import pformat
from typing import Callable, Dict
from functools import partial

from volttron.client.messaging import (headers)
from volttron.client.vip.agent import Agent
from volttron.client.vip.agent.subsystems.rpc import RPC
from volttron.utils import (format_timestamp, get_aware_utc_now, load_config,
                            setup_logging, vip_main)

from openadr_ven.volttron_openadr_client import (
    VolttronOpenADRClient,
    OpenADRClientInterface,
    OpenADREvent,
    OpenADRReportName,
    OpenADRMeasurements,
    OpenADROpt,
)

from openadr_ven.constants import (REQUIRED_KEYS, VEN_NAME, VTN_URL, DEBUG,
                                   CERT, KEY, PASSPHRASE, VTN_FINGERPRINT,
                                   SHOW_FINGERPRINT, CA_FILE, VEN_ID,
                                   DISABLE_SIGNATURE, OPENADR_EVENT, DEMO_VEN)

from openleadr.objects import Event

import logging
import asyncio
import sys
import gevent

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

    :param config_path: path to agent config
    """

    def __init__(self, config_path: str, **kwargs) -> None:
        # adding 'fake_ven_client' to support dependency injection and preventing call to super class for unit testing
        self.ven_client: OpenADRClientInterface
        if kwargs.get("fake_ven_client"):
            self.ven_client = kwargs["fake_ven_client"]
        else:
            super(OpenADRVenAgent, self).__init__(enable_web=True, **kwargs)

        self.default_config = self._parse_config(config_path)

        # SubSystem/ConfigStore
        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(
            self._configure_ven_client,
            actions=["NEW", "UPDATE"],
            pattern="config",
        )

    def _configure_ven_client(self, config_name: str, action: str,
                              contents: Dict) -> None:
        """Initializes the agent's configuration, creates and starts VolttronOpenADRClient.

        :param config_name:
        :param action: the action
        :param contents: the configuration used to update the agent's configuration
        """
        config = self.default_config.copy()
        config.update(contents)

        _log.info(f"config_name: {config_name}, action: {action}")
        _log.info(f"Configuring VEN client with: \n {pformat(config)} ")

        self.ven_client = VolttronOpenADRClient.build_client(config)

        # Add event handling capability to the client
        # if you want to add more handlers on a specific event, you must create a coroutine in this class
        # and then add it as the second input for 'self.ven_client.add_handler(<some event>, <coroutine>)'
        _log.info("Adding handlers...")
        self.ven_client.add_handler("on_event", self.handle_event)

        # add reports
        _log.info("Adding reports...")
        self.add_reports(demo_report=config.get(DEMO_VEN, False))

        _log.info("Starting OpenADRVen agent...")
        gevent.spawn_later(3, self._start_asyncio_loop)

    def _start_asyncio_loop(self) -> None:
        loop = asyncio.new_event_loop()
        loop.create_task(self.ven_client.run())
        loop.run_forever()

    # ***************** Methods for Servicing VTN Events ********************

    async def handle_event(self, event: Event) -> OpenADROpt:
        """Publish event to the Volttron message bus. This coroutine will be called when there is an event to be handled.

        :param event: The event sent from a VTN
        :return: Message to VTN to opt in to the event.
        """
        openadr_event = OpenADREvent(event)
        try:
            _log.info(
                f"Received event. Processing event now...\n Event signal:\n {pformat(openadr_event.get_event_signals())}"
            )
        except IndexError as e:
            _log.debug(
                f"Event signals is empty. {e} \n Showing whole event: {pformat(openadr_event)}"
            )
            pass

        self.publish_event(openadr_event)

        return OpenADROpt.OPT_IN

    # ***************** Methods for Offering Reports to a VTN ********************

    def add_reports(self, demo_report=False):
        # add reports at startup of this agent
        # Insert your custom reports that you want to offer to the VTN at startup

        # If you are testing out the agent using the provided toy VTN, you should enable adding the demo report
        if demo_report:
            self._add_report_demo()
        return

    def _add_report_demo(self):
        device = 'Device001'
        self.ven_client.add_report(
            callback=partial(self._read_voltage_demo, device=device),
            resource_id=device,
            report_name=OpenADRReportName.TELEMETRY_USAGE,
            measurement=OpenADRMeasurements.VOLTAGE,
            unit="V")

    # Adding reports requires a callback; below is an example of a callboack for the report example above
    async def _read_voltage_demo(self, device):
        _log.info(f"Reading voltage from device {device}")
        ## Add logic to read voltage from a device
        await asyncio.sleep(5)
        return 42

    @RPC.export
    def add_report_capability(self, callback: Callable,
                              report_name: OpenADRReportName, resource_id: str,
                              measurement: OpenADRMeasurements,
                              unit: str) -> None:
        """Add a new reporting capability to the client.

        This method is remotely accessible by other agents through Volttron's feature Remote Procedure Call (RPC);
        for reference on RPC, see https://volttron.readthedocs.io/en/develop/platform-features/message-bus/vip/vip-json-rpc.html?highlight=remote%20procedure%20call

        :param callback: A callback or coroutine that will fetch the value for a specific report. This callback will be passed the report_id and the r_id of the requested value.
        :param report_name: An OpenADR name for this report
        :param resource_id: A specific name for this resource within this report.
        :param measurement: The quantity that is being measured
        :return: Returns a tuple consisting of a report_specifier_id (str) and an r_id (str) an identifier for OpenADR messages
        """
        self.ven_client.add_report(callback=callback,
                                   report_name=report_name,
                                   resource_id=resource_id,
                                   measurement=measurement,
                                   unit=unit)
        return

    # ***************** VOLTTRON Pub/Sub Requests ********************
    def publish_event(self, event: OpenADREvent) -> None:
        """Publish an event to the Volttron message bus. When an event is created/updated, it is published to the VOLTTRON bus with a topic that includes 'openadr/event_update'.

        :param event: The Event received from the VTN
        """
        # OADR rule 6: If testEvent is present and != "false", handle the event as a test event.
        try:
            if event.isTestEvent():
                _log.debug("Suppressing publication of test event")
                return
        except KeyError as e:
            _log.debug(f"Key error: {e}")
            pass
        _log.debug(
            f"Publishing real/non-test event \n {pformat(event.parse_event())}"
        )
        self.vip.pubsub.publish(
            peer="pubsub",
            topic=
            f"{OPENADR_EVENT}/{event.get_event_id()}/{self.ven_client.get_ven_name()}",
            headers={headers.TIMESTAMP: format_timestamp(get_aware_utc_now())},
            message=event.parse_event(),
        )

        return

    # ***************** Helper methods ********************
    def _parse_config(self, config_path: str) -> Dict:
        """Parses the OpenADR agent's configuration file.

        :param config_path: The path to the configuration file
        :return: The configuration
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
            self._check_required_key(required_key, key_actual)
            req_keys_actual[required_key] = key_actual

        # optional configurations
        cert = config.get(CERT)
        if cert:
            cert = str(Path(cert).expanduser().resolve(strict=True))
        key = config.get(KEY)
        if key:
            key = str(Path(key).expanduser().resolve(strict=True))
        ca_file = config.get(CA_FILE)
        if ca_file:
            ca_file = str(Path(ca_file).expanduser().resolve(strict=True))
        debug = config.get(DEBUG)
        ven_name = config.get(VEN_NAME)
        vtn_url = config.get(VTN_URL)
        passphrase = config.get(PASSPHRASE)
        vtn_fingerprint = config.get(VTN_FINGERPRINT)
        show_fingerprint = bool(config.get(SHOW_FINGERPRINT, True))
        ven_id = config.get(VEN_ID)
        disable_signature = bool(config.get(DISABLE_SIGNATURE))
        demo_ven = config.get(DEMO_VEN, False)

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
            DEMO_VEN: demo_ven
        }

    def _check_required_key(self, required_key: str, key_actual: str) -> None:
        """Checks if the given key and its value are required by this agent

        :param required_key: the key that is being checked
        :param key_actual: the key value being checked
        :raises KeyError:
        """
        if required_key == VEN_NAME and not key_actual:
            raise KeyError(f"{VEN_NAME} is required.")
        elif required_key == VTN_URL and not key_actual:
            raise KeyError(
                f"{VTN_URL} is required. Ensure {VTN_URL} is given a URL to the VTN."
            )
        return


def main():
    """Main method called to start the agent."""
    vip_main(OpenADRVenAgent)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass

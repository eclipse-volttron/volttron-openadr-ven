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
import importlib
import logging
import asyncio
import sys
import os
import gevent

from pathlib import Path
from pprint import pformat
from datetime import timedelta

from openleadr.enums import OPT, REPORT_NAME, MEASUREMENTS
from openleadr.client import OpenADRClient

from . import (
    get_aware_utc_now,
    setup_logging,
    format_timestamp,
    load_config,
    isapipe,
    jsonapi,
    topics,
    headers,
    Agent,
)

from volttron_openadr_ven import volttron_openadr_client
from volttron_openadr_ven.constants import (
    REQUIRED_KEYS,
    VEN_NAME,
    VTN_URL,
    VIP_ADDRESS,
    SERVER_KEY,
    AGENT_PUBLIC,
    AGENT_SECRET,
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
from .volttron_openadr_client import openadr_client_type_class_names


setup_logging()
_log = logging.getLogger(__name__)
__version__ = "1.0"


class OpenADRVenAgent(Agent):
    """
    OpenADR (Automated Demand Response) is a standard for alerting and responding
    to the need to adjust electric power consumption in response to fluctuations in grid demand.
    OpenADR communications are conducted between Virtual Top Nodes (VTNs) and Virtual End Nodes (VENs).
    This agent is a wrapper around OpenLEADR, an open-source implementation of OpenADR 2.0.b for both servers, VTN, and clients, VEN.
    This agent creates an instance of OpenLEADR's VEN client, which is used to communicated with a VTN.
    """

    def __init__(
        self,
        ven_name: str,
        vtn_url: str,
        openadr_client_type: str,
        debug: bool = False,
        cert: str = None,
        key: str = None,
        passphrase: str = None,
        vtn_fingerprint: str = None,
        show_fingerprint: str = None,
        ca_file: str = None,
        ven_id: str = None,
        disable_signature: bool = None,
        **kwargs,
    ) -> None:
        """
                Initialize the agent's configuration. Create an OpenADR Client using OpenLeadr.
                Configuration parameters (see config for a sample config file):

                str ven_name: The name for this VEN
                str vtn_url: The URL of the VTN (Server) to connect to
                bool debug: Whether or not to print debugging messages
                str cert: The path to a PEM-formatted Certificate file to use
                                 for signing messages.
                str key: The path to a PEM-formatted Private Key file to use
                                for signing messages.
                str passphrase: The passphrase for the Private Key
                str vtn_fingerprint: The fingerprint for the VTN's certificate to
                                        verify incomnig messages
                str show_fingerprint: Whether to print your own fingerprint
                                             on startup. Defaults to True.
                str ca_file: The path to the PEM-formatted CA file for validating the VTN server's
                                    certificate.
                str ven_id: The ID for this VEN. If you leave this blank, a VEN_ID will be assigned by the VTN.
                bool disable_signature: Whether to disable digital signatures
                str openadr_client_type: The type of openadr client to use. Valid client types are defined in 'openadr_client_types' from ~/volttron_openadr_ven/volttron_openadr_client.py
                """
        super(OpenADRVenAgent, self).__init__(enable_web=True, **kwargs)

        # client will be initialized in configure_agent()
        self.ven_client: OpenADRClient
        self.default_config = {
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

        # SubSystem/ConfigStore
        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(
            self._configure, actions=["NEW", "UPDATE"], pattern="config"
        )

        # initialize all attributes of this class
        self.configure_agent(self.default_config)

    def configure_agent(self, config) -> None:
        """
            Initialize the agent's configuration. Create an OpenADR Client using OpenLeadr.
        """
        _log.info(f"Configuring agent with: \n {pformat(config)} ")

        # instantiate and add handlers to the OpenADR Client
        client_type = config.get(OPENADR_CLIENT_TYPE)
        class_client_type = openadr_client_type_class_names[client_type]
        _log.info(
            f"Creating openadr client type: {client_type}, using class: {class_client_type}"
        )

        openadr_client = getattr(
            importlib.import_module(volttron_openadr_client.__name__),
            class_client_type,
        )

        self.ven_client = openadr_client(
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
        _log.info("OpenADRClient successfully created.")

        _log.info(
            "Adding capabilities (e.g. handlers, reports) to OpenADRClient..."
        )
        # Add event handling capability to the client
        # if you want to add more handlers on a specific event, you must create a coroutine in this class
        # and then add it as the second input for 'self.ven_client.add_handler(<some event>, <coroutine>)'
        self.ven_client.add_handler("on_event", self.handle_event)

        # Add the report capability to the client
        # the following is a report to be sent to a IPKeys test VTN
        self.ven_client.add_report(
            callback=self.collect_report_value,
            report_name=REPORT_NAME.TELEMETRY_USAGE,
            resource_id="device001",
            measurement=MEASUREMENTS.VOLTAGE,
        )

        _log.info("Capabilities successfully added.")
        gevent.spawn_later(3, self.start_asyncio_loop)

    def _configure(self, config_name, action, contents: dict) -> None:
        """The agent's config may have changed. Re-initialize it."""
        config = self.default_config.copy()
        config.update(contents)
        self.configure_agent(config)

    def start_asyncio_loop(self):
        _log.info("Starting agent...")
        loop = asyncio.get_event_loop()
        loop.create_task(self.ven_client.run())
        loop.run_forever()

    # ***************** Methods for Servicing VTN Requests ********************

    async def handle_event(self, event: dict) -> OPT:
        """
        Publish event to the Volttron message bus. Return OPT response.
        This coroutine will be called when there is an event to be handled.

        :param event: dict
        Example of event:
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
        :return: openleadr.enums.OPT
        """
        try:
            _log.debug("Received event. Processing event now...")
            signal = event.get("event_signals")[0]  # type: ignore[index]
            _log.info(f"Event signal:\n {pformat(signal)}")
        except IndexError as e:
            _log.debug(
                f"Event signals is empty. {e} \n Showing whole event: {pformat(event)}"
            )
            pass

        self.publish_event(event)

        return OPT.OPT_IN

    async def collect_report_value(self):
        # This callback is called when you need to collect a value for your Report
        # below is dummy code; replace with your business logic
        return 1.23

    # ***************** VOLTTRON Pub/Sub Requests ********************
    def publish_event(self, event: dict) -> None:
        """Publish an event to the Volttron message bus. When an event is created/updated, it is published to the VOLTTRON bus with a topic that includes 'openadr/event_update'.
        :param event: dict
        :return: None
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
            message=self._json_object(event),
        )

        return

    # ***************** Helper methods ********************
    def _json_object(self, obj: dict):
        """Ensure that an object is valid JSON by dumping it with json_converter and then reloading it."""
        obj_string = jsonapi.dumps(
            obj,
            default=lambda x: int(x.total_seconds())
            if isinstance(x, timedelta)
            else None,
        )
        return jsonapi.loads(obj_string)


def main():
    """Main method called to start the agent."""
    # TODO: when volttron.utils gets fixed by https://github.com/VOLTTRON/volttron-utils/issues/6, uncomment the line below and remove vip_main_tmp
    # vip_main(ven_agent, version=__version__)
    vip_main_tmp()


def vip_main_tmp():
    config_path = os.environ.get("AGENT_CONFIG")
    if not config_path:
        # this function borrows code from volttron.utils.commands.vip_main
        # it allows the user of this agent to set the certificates so that the remote volttron platform can authenticate this agent
        import argparse

        # Instantiate the parser
        parser = argparse.ArgumentParser()
        parser.add_argument("config_path")
        args = parser.parse_args()
        config_path = args.config_path

    if isapipe(sys.stdout):
        # Hold a reference to the previous file object so it doesn't
        # get garbage collected and close the underlying descriptor.
        stdout = sys.stdout
        sys.stdout = os.fdopen(stdout.fileno(), "w", 1)

    agent = ven_agent(config_path)

    try:
        run = agent.run
    except AttributeError:
        run = agent.core.run
    task = gevent.spawn(run)
    try:
        task.join()
    finally:
        task.kill()


def check_required_key(required_key, key_actual):
    if required_key == VEN_NAME and not key_actual:
        raise KeyError(f"{VEN_NAME} is required.")
    elif required_key == VTN_URL and not key_actual:
        raise KeyError(
            f"{VTN_URL} is required. Ensure {VTN_URL} is given a URL to the VTN."
        )
    elif required_key == VIP_ADDRESS and not key_actual:
        raise KeyError(
            f"{VIP_ADDRESS} is required. For example, if running volttron instance locally, use tcp://127.0.0.1"
        )
    elif required_key == SERVER_KEY and not key_actual:
        raise KeyError(
            f"{SERVER_KEY} is required. To get the server key from the volttron instance that this agent will be connected to, use the command: vctl auth serverkey"
        )
    elif required_key == AGENT_PUBLIC and not key_actual:
        raise KeyError(
            f"{AGENT_PUBLIC} is required. To generate a public key and associated secret key from the volttron instance that this agent will be connected to, run the command: vctl auth keypair"
        )
    elif required_key == AGENT_SECRET and not key_actual:
        raise KeyError(
            f"{AGENT_SECRET} is required. To generate a public key and associated secret key from the volttron instance that this agent will be connected to, run the command: vctl auth keypair"
        )
    elif required_key == OPENADR_CLIENT_TYPE and not key_actual:
        raise KeyError(
            f"{OPENADR_CLIENT_TYPE} is required. Specify one of the following valid client types: {list(openadr_client_type_class_names.keys())}"
        )


def ven_agent(config_path: str, **kwargs) -> OpenADRVenAgent:
    """
        Parse the OpenADRVenAgent configuration file and return an instance of
        the agent that has been created using that configuration.
        See initialize_config() method documentation for a description of each configurable parameter.

    :param config_path: (str) Path to a configuration file.

    :returns: OpenADRVenAgent
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
        check_required_key(required_key, key_actual)
        req_keys_actual[required_key] = key_actual

    remote_url = (
        f"{req_keys_actual[VIP_ADDRESS]}"
        f"?serverkey={req_keys_actual[SERVER_KEY]}"
        f"&publickey={req_keys_actual[AGENT_PUBLIC]}"
        f"&secretkey={req_keys_actual[AGENT_SECRET]}"
    )

    # optional configurations
    debug = config.get(DEBUG)

    # keypair paths
    cert = config.get(CERT)
    if cert:
        cert = str(Path(cert).expanduser().resolve(strict=True))
    key = config.get(KEY)
    if key:
        key = str(Path(key).expanduser().resolve(strict=True))

    passphrase = config.get(PASSPHRASE)
    vtn_fingerprint = config.get(VTN_FINGERPRINT)
    show_fingerprint = config.get(SHOW_FINGERPRINT)
    ca_file = config.get(CA_FILE)
    ven_id = config.get(VEN_ID)
    disable_signature = bool(config.get(DISABLE_SIGNATURE))
    openadr_client_type = req_keys_actual[OPENADR_CLIENT_TYPE]

    return OpenADRVenAgent(
        req_keys_actual[VEN_NAME],
        req_keys_actual[VTN_URL],
        openadr_client_type,
        debug=debug,
        cert=cert,
        key=key,
        passphrase=passphrase,
        vtn_fingerprint=vtn_fingerprint,
        show_fingerprint=show_fingerprint,
        ca_file=ca_file,
        ven_id=ven_id,
        disable_signature=disable_signature,
        identity=IDENTITY,
        # TODO: when volttron.utils gets fixed by https://github.com/VOLTTRON/volttron-utils/issues/6, remove the input 'address'
        address=remote_url,
        **kwargs,
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass

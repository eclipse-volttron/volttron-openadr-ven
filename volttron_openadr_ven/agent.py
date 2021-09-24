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
import openleadr.enums

from pprint import pformat
from datetime import datetime

from openleadr.enums import OPT
from openleadr import OpenADRClient

from volttron.utils import (
    get_aware_utc_now,
    jsonapi,
    setup_logging,
    vip_main,
    format_timestamp,
    load_config,
)
from volttron.client.vip.agent import Agent, Core
from volttron.client.messaging import topics, headers

setup_logging(level=logging.DEBUG)
_log = logging.getLogger(__name__)
__version__ = "1.0"

VEN_NAME = "ven_name"
VTN_URL = "vtn_url"
DEBUG = "debug"
CERT = "cert"
KEY = "key"
PASSPHRASE = "passphrase"
VTN_FINGERPRINT = "vtn_fingerprint"
SHOW_FINGERPRINT = "show_fingerprint"
CA_FILE = "ca_file"
VEN_ID = "ven_id"
DISABLE_SIGNATURE = "disable_signature"


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
        }

        # SubSystem/ConfigStore
        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(
            self._configure, actions=["NEW", "UPDATE"], pattern="config"
        )

        # initialize all attributes of this class
        self.configure_agent(self.default_config)

    def configure_agent(self, config: dict) -> None:
        """
            Initialize the agent's configuration. Create an OpenADR Client using OpenLeadr.
        """
        _log.debug(f"Configuring agent with: \n {pformat(config)} ")

        # instantiate and add handlers to the OpenADR Client
        _log.info("Creating OpenLeadrVen Client...")
        self.ven_client = OpenADRClient(
            ven_name=config.get(VEN_NAME),
            vtn_url=config.get(VTN_URL),
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

        # if you want to add more handlers on a specific event, you must create a coroutine in this class
        # and then add it as the second input for 'self.ven_client.add_handler(<some event>, <coroutine>)'
        self.ven_client.add_handler("on_event", self.handle_event)

        _log.info("Configuration complete.")

    def _configure(self, config_name, action, contents: dict) -> None:
        """The agent's config may have changed. Re-initialize it."""
        config = self.default_config.copy()
        config.update(contents)
        self.configure_agent(config)

    # ***************** Methods for Managing the Agent on Volttron ********************

    @Core.receiver("onstart")
    def onstart(self, sender) -> None:
        """The agent has started."""
        _log.info(f"Sender {sender}")
        _log.info("Starting agent...")
        loop = asyncio.get_event_loop()
        loop.create_task(self.ven_client.run())
        loop.run_forever()

    # # TODO: Identify actions needed to be done before shutdown
    # @Core.receiver("onstop")
    # def onstop(self, sender, **kwargs):
    #     """
    #     This method is called when the Agent is about to shutdown, but before it disconnects from
    #     the message bus.
    #     """
    #     pass
    #
    # # TODO: Identify what, if at all, RPC methods should be available to other Agents
    # @RPC.export
    # def rpc_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
    #     """
    #     RPC method
    #
    #     May be called from another agent via self.vip.rpc.call
    #     """
    #     pass

    # ***************** Methods for Servicing VTN Requests ********************

    async def handle_event(self, event: dict) -> openleadr.enums.OPT:
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
            default=lambda x: x.__str__() if isinstance(x, datetime) else None,
        )
        return jsonapi.loads(obj_string)


def main():
    """Main method called to start the agent."""
    vip_main(ven_agent, version=__version__)


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

    ven_name = config.get(VEN_NAME)
    if not ven_name:
        raise Exception(f"{VEN_NAME} is required.")
    vtn_url = config.get(VTN_URL)
    if not vtn_url:
        raise Exception(
            f"{VTN_URL} is required. Ensure {VTN_URL} is given a URL to the VTN."
        )
    debug = config.get(DEBUG)
    cert = config.get(CERT)
    key = config.get(KEY)
    passphrase = config.get(PASSPHRASE)
    vtn_fingerprint = config.get(VTN_FINGERPRINT)
    show_fingerprint = config.get(SHOW_FINGERPRINT)
    ca_file = config.get(CA_FILE)
    ven_id = config.get(VEN_ID)
    disable_signature = bool(config.get(DISABLE_SIGNATURE))

    return OpenADRVenAgent(
        ven_name,
        vtn_url,
        debug=debug,
        cert=cert,
        key=key,
        passphrase=passphrase,
        vtn_fingerprint=vtn_fingerprint,
        show_fingerprint=show_fingerprint,
        ca_file=ca_file,
        ven_id=ven_id,
        disable_signature=disable_signature,
        **kwargs,
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass

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

from pprint import pformat
from typing import Dict
from datetime import datetime as dt

from openleadr import OpenADRClient
from openleadr.enums import OPT
from openleadr.objects import Event

from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core
from volttron.platform.messaging import topics, headers
from volttron.utils import jsonapi

utils.setup_logging()
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
        debug: bool,
        cert: str,
        key: str,
        fingerprint: str,
        show_fingerprint: str,
        ca_file: str,
        **kwargs,
    ) -> None:
        super(OpenADRVenAgent, self).__init__(enable_web=True, **kwargs)
        self.ven_name = None
        self.vtn_url = None
        self.debug = None
        self.cert = None
        self.key = None
        self.fingerprint = None
        self.show_fingerprint = None
        self.ca_file = None
        self.ven_id = None

        self.default_config = {
            "ven_name": ven_name,
            "vtn_url": vtn_url,
            "debug": debug,
            "cert": cert,
            "key": key,
            "fingerprint": fingerprint,
            "show_fingerprint": show_fingerprint,
            "ca_file": ca_file,
        }
        self.vip.config.set_default("config", self.default_config)
        self.vip.config.subscribe(
            self._configure, actions=["NEW", "UPDATE"], pattern="config"
        )

        # properties of the this class will be initialized in initialize_config
        # self.ven_client is an instance of OpenLeadr's OpenADRClient, an implementation of OpenADR; this will be instantiated in initialize_config
        self.initialize_config(self.default_config)

    def initialize_config(self, config: Dict) -> None:
        """
            Initialize the agent's configuration.
            Configuration parameters (see config for a sample config file):

        str ven_name: The name for this VEN
        str vtn_url: The URL of the VTN (Server) to connect to
        bool debug: Whether or not to print debugging messages
        str cert: The path to a PEM-formatted Certificate file to use
                         for signing messages.
        str key: The path to a PEM-formatted Private Key file to use
                        for signing messages.
        str fingerprint: The fingerprint for the VTN's certificate to
                                verify incomnig messages
        str show_fingerprint: Whether to print your own fingerprint
                                     on startup. Defaults to True.
        str ca_file: The path to the PEM-formatted CA file for validating the VTN server's
                            certificate.
        """
        _log.debug("Configuring agent")
        self.ven_name = config.get("ven_name")
        self.vtn_url = config.get("vtn_url")
        self.debug = config.get("debug", False)
        self.cert = config.get("cert")
        self.key = config.get("key")
        self.fingerprint = config.get("fingerprint")
        self.show_fingerprint = config.get("show_fingerprint", True)
        self.ca_file = config.get("ca_file")

        _log.info("Configuration parameters:")
        _log.info(pformat(config))

        # instantiate and add handlers to the openadrclient
        self.ven_client = OpenADRClient(
            ven_name=self.ven_name,
            vtn_url=self.vtn_url,
            debug=self.debug,
            cert=self.cert,
            key=self.key,
            show_fingerprint=self.show_fingerprint,
            ca_file=self.ca_file,
        )

        # if you want to add more handlers on a specific event, you must create a callback function in this class and then add it as the second input for 'add_handler'
        self.ven_client.add_handler("on_event", self.handle_event)

    def _configure(self, contents: Dict) -> None:
        """The agent's config may have changed. Re-initialize it."""
        config = self.default_config.copy()
        config.update(contents)
        self.initialize_config(config)

    # # TODO: Investigate how to run async methods within Volttron Agent Framework
    # @Core.receiver("onstart")
    # def onstart_method(self) -> None:
    #     """The agent has started."""
    #     _log.debug("Starting agent")
    #     # Running the ven_client in the Python AsyncIO Event Loop
    #     # the client will automagically register with the VTN and then start polling the VTN for new messages
    #     loop = asyncio.get_event_loop()
    #     loop.create_task(self.ven_client.run())
    #     loop.run_forever()

    # ***************** Methods for Servicing VTN Requests ********************

    async def handle_event(self, event: Event) -> OPT:
        """
        Publish event to the Volttron message bus. Return OPT response.

        :param event: Event
        For more info on shape of 'event', see https://openleadr.org/docs/client.html#dealing-with-events and https://openleadr.org/docs/api/openleadr.html#openleadr.objects.Event
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
        :return: OPT
        """
        _log.info(f"Event: {pformat(event)}")
        self.publish_event(event)
        return OPT.OPT_IN

    # ***************** VOLTTRON Pub/Sub Requests ********************
    def publish_event(self, event: Event) -> None:
        """Publish an event to the Volttron message bus. When an event is created/updated, it is published to the VOLTTRON bus with a topic that includes 'openadr/event_update'.
        :param event:
        :return: None
        """
        # OADR rule 6: If testEvent is present and != "false", handle the event as a test event.
        if event.event_descriptor.test_event != "false":
            _log.debug(f"Suppressing publication of test event {event}")
            return

        _log.debug("Publishing event {}".format(event))
        self.vip.pubsub.publish(
            peer="pubsub",
            topic=f"{topics.OPENADR_EVENT}/{self.ven_id}",
            headers={
                headers.TIMESTAMP: utils.format_timestamp(utils.get_aware_utc_now())
            },
            message=self._json_object(event.__dict__),
        )
        return

    # ***************** Helper methods ********************
    def _json_object(self, obj: Dict):
        """Ensure that an object is valid JSON by dumping it with json_converter and then reloading it."""
        obj_string = jsonapi.dumps(obj, default=self.json_converter)
        obj_json = jsonapi.loads(obj_string)
        return obj_json

    @staticmethod
    def json_converter(object_to_dump):
        """When calling jsonapi.dumps, convert datetime instances to strings."""
        if isinstance(object_to_dump, dt):
            return object_to_dump.__str__()


def ven_agent(config_path: str, **kwargs) -> OpenADRVenAgent:
    """
        Parse the OpenADRVenAgent configuration file and return an instance of
        the agent that has been created using that configuration.
        See initialize_config() method documentation for a description of each configurable parameter.

    :param config_path: (str) Path to a configuration file.

    :returns: OpenADRVenAgent instance
    """
    try:
        config = utils.load_config(config_path)
    except Exception as err:
        _log.error("Error loading configuration: {}".format(err))
        config = {}

    if not config:
        raise Exception("Configuration cannot be empty.")

    ven_name = config.get("ven_name")
    if not ven_name:
        raise Exception("ven_name is required.")
    vtn_url = config.get("vtn_url")
    if not vtn_url:
        raise Exception(
            "vtn_url is required. Ensure vtn_url is given a URL to the VTN."
        )

    # below are optional configurations
    debug = config.get("debug")
    cert = config.get("cert")
    key = config.get("key")
    fingerprint = config.get("fingerprint")
    show_fingerprint = config.get("show_fingerprint")
    ca_file = config.get("ca_file")

    return OpenADRVenAgent(
        ven_name,
        vtn_url,
        debug,
        cert,
        key,
        fingerprint,
        show_fingerprint,
        ca_file,
        **kwargs,
    )

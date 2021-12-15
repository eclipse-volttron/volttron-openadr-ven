import logging
import asyncio

from abc import ABC
from functools import partial
from lxml import etree

from openleadr.client import OpenADRClient
from openleadr.preflight import preflight_message
from openleadr.messaging import TEMPLATES, SIGNER, _create_replay_protect
from openleadr import utils, enums

from . import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


"""
The VolttronOpenADR VEN agent uses the python library OpenLEADR https://github.com/openleadr/openleadr-python to create
an OpenADR VEN client. This agent extends the OpenADRClient class from OpenLEADR so that it can have the flexibility
to connect to any implementation of and OpenADR VTN. For example, to connect to an IPKeys VTN that was implemented
on an old OpenADR protocol, the IPKeysDemoVTNOpenADRClient is created so that it can successfully connect to an IPKeys VTN.

If you have a specific VTN that you want to connect to and require further customization of the VEN client, create your
own OpenADRClient by extending the base class VolttronOpenADRClientBase, updating your client with your business logic, and putting that subclass in this module
"""


class OpenADRClientBase(OpenADRClient, ABC):
    def __init__(self, ven_name, vtn_url, disable_signature=False, **kwargs):
        super().__init__(ven_name, vtn_url, **kwargs)
        self.disable_signature = disable_signature


class IPKeysClient(OpenADRClientBase, ABC):
    def __init__(self, ven_name, vtn_url, disable_signature, **kwargs):
        super().__init__(ven_name, vtn_url, disable_signature, **kwargs)

        self._create_message = partial(
            self.create_message_ipkeys,
            cert=self.cert_path,
            key=self.key_path,
            passphrase=self.passphrase,
            disable_signature=self.disable_signature,
        )

    async def _on_event(self, message):
        logger.debug("The VEN received an event")
        events = message["events"]
        try:
            results = []

            for event in message["events"]:
                event_id = event["event_descriptor"]["event_id"]
                event_status = event["event_descriptor"]["event_status"]
                modification_number = event["event_descriptor"][
                    "modification_number"
                ]
                received_event = utils.find_by(
                    self.received_events, "event_descriptor.event_id", event_id
                )

                if received_event:
                    if (
                        received_event["event_descriptor"][
                            "modification_number"
                        ]
                        == modification_number
                    ):
                        # Re-submit the same opt type as we already had previously
                        result = self.responded_events[event_id]
                    else:
                        # Replace the event with the fresh copy
                        utils.pop_by(
                            self.received_events,
                            "event_descriptor.event_id",
                            event_id,
                        )
                        self.received_events.append(event)
                        # Wait for the result of the on_update_event handler
                        result = await utils.await_if_required(
                            self.on_update_event(event)
                        )
                else:
                    # Wait for the result of the on_event
                    self.received_events.append(event)
                    result = self.on_event(event)
                if asyncio.iscoroutine(result):
                    result = await result
                results.append(result)
                if (
                    event_status
                    in (
                        enums.EVENT_STATUS.COMPLETED,
                        enums.EVENT_STATUS.CANCELLED,
                    )
                    and event_id in self.responded_events
                ):
                    self.responded_events.pop(event_id)
                else:
                    self.responded_events[event_id] = result
            for i, result in enumerate(results):
                if (
                    result not in ("optIn", "optOut")
                    and events[i]["response_required"] == "always"
                ):
                    logger.error(
                        "Your on_event or on_update_event handler must return 'optIn' or 'optOut'; "
                        f"you supplied {result}. Please fix your on_event handler."
                    )
                    results[i] = "optOut"
        except Exception as err:
            logger.error(
                "Your on_event handler encountered an error. Will Opt Out of the event. "
                f"The error was {err.__class__.__name__}: {str(err)}"
            )
            results = ["optOut"] * len(events)

        event_responses = [
            {
                "response_code": 200,
                "response_description": "OK",
                "opt_type": results[i],
                "request_id": message["request_id"],
                "modification_number": events[i]["event_descriptor"][
                    "modification_number"
                ],
                "event_id": events[i]["event_descriptor"]["event_id"],
            }
            for i, event in enumerate(events)
            if event["response_required"] == "always"
            and not utils.determine_event_status(event["active_period"])
            == "completed"
        ]

        if len(event_responses) > 0:
            response = {
                "response_code": 200,
                "response_description": "OK",
                "request_id": message["request_id"],
            }
            message = self._create_message(
                "oadrCreatedEvent",
                response=response,
                event_responses=event_responses,
                ven_id=self.ven_id,
            )
            service = "EiEvent"
            response_type, response_payload = await self._perform_request(
                service, message
            )
            logger.info(response_type, response_payload)
        else:
            logger.info(
                "Not sending any event responses, because a response was not required/allowed by the VTN."
            )

    @staticmethod
    def create_message_ipkeys(
        message_type,
        cert=None,
        key=None,
        passphrase=None,
        disable_signature=False,
        **message_payload,
    ):
        """
        Create and optionally sign an OpenADR message. Returns an XML string.
        """
        message_payload = preflight_message(message_type, message_payload)
        template = TEMPLATES.get_template(f"{message_type}.xml")
        signed_object = utils.flatten_xml(template.render(**message_payload))
        envelope = TEMPLATES.get_template("oadrPayload.xml")
        if cert and key and not disable_signature:
            tree = etree.fromstring(signed_object)
            signature_tree = SIGNER.sign(
                tree,
                key=key,
                cert=cert,
                passphrase=utils.ensure_bytes(passphrase),
                reference_uri="#oadrSignedObject",
                signature_properties=_create_replay_protect(),
            )
            signature = etree.tostring(signature_tree).decode("utf-8")
        else:
            signature = None
        msg = envelope.render(
            template=f"{message_type}",
            signature=signature,
            signed_object=signed_object,
        )
        return msg


def openadr_clients():
    clients = {}
    work = [OpenADRClient]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            child_name = child.__name__
            if child_name not in clients:
                clients[child_name] = child
                work.append(child)
    return clients

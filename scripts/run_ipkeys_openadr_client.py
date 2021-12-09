import logging
import asyncio

from pprint import pformat
from openleadr.enums import OPT
from volttron_openadr_ven.volttron_openadr_client import (
    IPKeysDemoVTNOpenADRClient,
)
from volttron_openadr_ven.constants import (
    VEN_NAME,
    VTN_URL,
    DEBUG,
    DISABLE_SIGNATURE,
    CERT,
    KEY,
)

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)
__version__ = "1.0"


def handle_event(event):
    _log.info(f"Received event:\n {pformat(event)}")
    return OPT.OPT_IN


config = {
    # Change the paths to the location of the cert and key to the paths of the cert and key in your local machine
    CERT: "secret/TEST_RSA_VEN_210923215148_certs/TEST_RSA_VEN_210923215148_cert.pem",
    KEY: "secret/TEST_RSA_VEN_210923215148_certs/TEST_RSA_VEN_210923215148_privkey.pem",
    # Do not change these values
    VEN_NAME: "PNNLVEN",
    VTN_URL: "https://eiss2demo.ipkeys.com/oadr2/OpenADR2/Simple/2.0b",
    DEBUG: True,
    DISABLE_SIGNATURE: True,
}


ven = IPKeysDemoVTNOpenADRClient(
    ven_name=config[VEN_NAME],
    vtn_url=config[VTN_URL],
    debug=True,
    disable_signature=True,
    cert=config[CERT],
    key=config[KEY],
)
ven.add_handler("on_event", handle_event)


loop = asyncio.get_event_loop()
loop.create_task(ven.run())
loop.run_forever()

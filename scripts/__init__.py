import logging
import asyncio

from pprint import pformat
from openleadr.enums import OPT
from volttron_openadr_ven.volttron_openleadr import VolttronOpenADRClient

_log = logging.getLogger(__name__)
__version__ = "1.0"


def handle_event(event):
    try:
        _log.debug("Received event. Processing event now...")
        signal = event.get("event_signals")[0]  # type: ignore[index]
        _log.info(f"Event signal:\n {pformat(signal)}")
    except IndexError as e:
        _log.debug(
            f"Event signals is empty. {e} \n Showing whole event: {pformat(event)}"
        )
        pass

    return OPT.OPT_IN


config = {
    "ven_name": "PNNLVEN",
    "vtn_url": "https://eiss2demo.ipkeys.com/oadr2/OpenADR2/Simple/2.0b",
    "cert": "secret/TEST_RSA_VEN_210923215148_certs/TEST_RSA_VEN_210923215148_cert.pem",
    "key": "secret/TEST_RSA_VEN_210923215148_certs/TEST_RSA_VEN_210923215148_privkey.pem",
    "debug": True,
    "disable_signature": True,
}


ven = VolttronOpenADRClient(
    ven_name=config["ven_name"],
    vtn_url=config["vtn_url"],
    debug=True,
    disable_signature=True,
    cert=config["cert"],
    key=config["key"],
)
ven.add_handler("on_event", handle_event)


loop = asyncio.get_event_loop()
loop.create_task(ven.run())
loop.run_forever()

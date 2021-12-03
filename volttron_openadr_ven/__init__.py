# key names for processing config file for OpenADR VEN agent
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

# The parameters dictionary is used to populate the agent's
# remote vip address.
_params = {
    # The root of the address.
    # Note:
    # 1. volttron instance should be configured to use tcp. use command vcfg
    # to configure
    "vip_address": "tcp://127.0.0.1",
    "port": 22916,
    # public and secret key for the openadrvenagent.
    # These can be created using the command:  volttron-ctl auth keypair
    # public key should also be added to the volttron instance auth
    # configuration to enable standalone agent access to volttron instance. Use
    # command 'vctl auth add' Provide this agent's public key when prompted
    # for credential.
    "agent_public": "csJBQqQDZ-pP_8E9FIgM9hvkAak6HriLkIQhP46ZFl4",
    "agent_secret": "4rv_l3oEzgmRxbPkGma2-tMhfPu47yyhi48ygF5hVQY",
    # Public server key from the remote platform.  This can be
    # obtained using the command:
    # volttron-ctl auth serverkey
    "server_key": "FDIH6OBg0m3L2T6Jv_zUuQlSxYdgvTD3QOEye-vM-iI",
}

REMOTE_URL = (
    f"{_params['vip_address']}:{_params['port']}"
    f"?serverkey={_params['server_key']}"
    f"&publickey={_params['agent_public']}"
    f"&secretkey={_params['agent_secret']}"
)

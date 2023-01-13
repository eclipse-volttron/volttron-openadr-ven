# OpenADRVen Agent


[![Passing?](https://github.com/eclipse-volttron/volttron-openadr-ven/actions/workflows/run-tests.yml/badge.svg)](https://github.com/eclipse-volttron/volttron-openadr-ven/actions/workflows/run-tests.yml?query=branch%3Adevelop)
[![pypi version](https://img.shields.io/pypi/v/volttron-openadr-ven.svg)](https://pypi.org/project/volttron-openadr-ven/)


OpenADR (Automated Demand Response) is a standard for alerting and responding to the need to adjust electric power consumption in response to fluctuations in grid demand.


# Prerequisites


* Python 3.8


# Installation


1. Create and activate a virtual environment.

   ```shell
   python -m venv env
   source env/bin/activate
   ```

1. Install volttron and start the platform.

    ```shell
    pip install volttron


    # Start platform with output going to volttron.log
    volttron -vv -l volttron.log &
    ```

1.  Install and start the Volttron OpenADRVen Agent.


    ```shell
    vctl install volttron-openadr-ven --agent-config <path to agent config> \
    --vip-identity openadr.ven \
    --start
    ```

1. View the status of the installed agent


    ```shell
    vctl status
    ```

1. Observe Data

    The OpenADR publishes events on the message bus. To see these events in the Volttron log file, install a [Listener Agent](https://pypi.org/project/volttron-listener/):


    ```
    vctl install volttron-listener --start
    ```


    Once installed, you should see the data being published by viewing the Volttron logs file that was created in step 2.

    To watch the logs, open a separate terminal and run the following command:


    ```
    tail -f <path to folder containing volttron.log>/volttron.log
    ```


# Agent Configuration


The required parameters for this agent are "ven_name" and "vtn_url". Below is an example of a correct configuration with optional parameters added.


```json
    {
        "ven_name": "PNNLVEN",
        "vtn_url": "https://eiss2demo.ipkeys.com/oadr2/OpenADR2/Simple/2.0b",
        "cert_path": "~/.ssh/secret/TEST_RSA_VEN_210923215148_cert.pem",
        "key_path": "~/.ssh/secret/TEST_RSA_VEN_210923215148_privkey.pem",
        "debug": true,
        "disable_signature": true
    }
```


Save this configuration in a JSON file in your preferred location. An example of such a configuration is saved in the
root of this repository; the file is named `config_example1.json`

# Testing


If you don't have a dedicated VTN to test the VolttronOpenADR against, you can setup a local VTN instead. This VTN will be hosted at localhost on port 8080 (i.e. 127.0.0.1:8080). This VTN will accept registrations from a VEN named 'ven123', requests all reports that the VEN offers, and create an Event for the VEN. After setting up a local VTN, configure an VolttronOpenADRVen Agent against that local VTN and then install the agent on your VOLTTRON instance. Ensure that the VOLTTRON instance is running on the same host that the VTN is running on.

To setup a local VTN, we have provided a script and a custom agent configuration for convenience. Follow the steps below to setup a local VTN and corresponding Volttron OpenADRVen Agent:


## Setup VTN

Setup a dedicated environment for the VTN.


1. Clone this repo.


1. Create a dedicated virtual environment for the VTN:


    ```shell
    python -m venv env
    source env/bin/activate
    ```


1. Install [openleadr](https://pypi.org/project/openleadr/):

    ```shell
    pip install openleadr
    ```

1. At the top level of this repo, run the VTN server in the foreground so that we can observe logs:

    ```shell
    python utils/vtn.py
    ```

    This VTN uses port 8080 by default. If you want to use a custom port, set the environment variable "VTN_PORT" to your desired port and start the VTN. For example:

    ```shell
    VTN_PORT=8081 python utils/vtn.py
    ```

    After you start the VTN, you should see the following logs:

    ```shell

    If you provide a 'ven_lookup' to your OpenADRServer() init, OpenLEADR can automatically issue ReregistrationRequests for VENs that don't exist in your system.

    Please see https://openleadr.org/docs/server.html#things-you-should-implement.

    ************************************************************************
            Your VTN Server is now running at
        http://127.0.0.1:8080/OpenADR2/Simple/2.0b
    ************************************************************************
    ```


## Setup VolttronOpenADR Ven

Setup a dedicated environment for the Volttron platform and VolttronOpenADRVen Agent.

1. Open up another terminal, create a folder called temp, and create another virtual environment:

    ```shell
    mkdir temp
    cd temp
    python -m venv env
    source env/bin/activate
    ```

1. Install volttron:

    ```shell
    pip install volttron
    ```

1. Run volttron in the background:

    ```shell
    volttron -vv -l volttron.log &
    ```

1. Install the VolttronOpenADRVEN Agent using the configuration provided under `utils`:

    ```shell
    vctl install volttron-openadr-ven --agent-config utils/config_toy_ven.json --tag openadr --start
    ```

1. Observe the logs to verify that the Event from the local VTN was received by the VolttronOpenADRVEN agent. The topic follows this format "openadr/event/<event_id>/<ven-name>".

    ```shell
    tail -f volttron.log
    ```

    You should expect to see the following in the logs:

    ```shell
        2023-01-12 12:01:36,222 (volttron-listener-0.2.0rc0 31258) listener.agent(104) INFO: Peer: pubsub, Sender: volttron-openadr-ven-1.0.1a1_1:, Bus: ,
        Topic: openadr/event/2ab3526f-235b-4c66-8b31-e04a95406913/ven123, Headers: {'TimeStamp': '2023-01-12T20:01:36.215472+00:00', 'min_compatible_version': '3.0', 'max_compatible_version': ''
        }, Message:
        {'active_period': {'dtstart': '2023-01-12T20:05:47.204310+00:00',
                        'duration': 3600},
        'event_descriptor': {'created_date_time': '2023-01-12T20:00:47.204940+00:00',
                            'event_id': '2ab3526f-235b-4c66-8b31-e04a95406913',
                            'event_status': 'far',
                            'market_context': 'oadr://unknown.context',
                            'modification_date_time': '2023-01-12T20:00:47.204950+00:00',
                            'modification_number': 0,
                            'priority': 0,
                            'test_event': False},
        'event_signals': [{'intervals': [{'dtstart': '2023-01-12T20:05:47.204310+00:00',
                                        'duration': 3600,
                                        'signal_payload': 100.0,
                                        'uid': 0}],
                            'signal_id': '9e3cda6b-9d09-4f5a-99e5-00b41e480d2f',
                            'signal_name': 'simple',
                            'signal_type': 'level'}],
        'response_required': 'always',
        'targets': [{'ven_id': 'ven_id_123'}],
        'targets_by_type': {'ven_id': ['ven_id_123']}}
    ```


# Development


Please see the following for contributing guidelines [contributing](https://github.com/eclipse-volttron/volttron-core/blob/develop/CONTRIBUTING.md).


Please see the following helpful guide about [developing modular VOLTTRON agents](https://github.com/eclipse-volttron/volttron-core/blob/develop/DEVELOPING_ON_MODULAR.md)


# Disclaimer Notice


This material was prepared as an account of work sponsored by an agency of the
United States Government.  Neither the United States Government nor the United
States Department of Energy, nor Battelle, nor any of their employees, nor any
jurisdiction or organization that has cooperated in the development of these
materials, makes any warranty, express or implied, or assumes any legal
liability or responsibility for the accuracy, completeness, or usefulness or any
information, apparatus, product, software, or process disclosed, or represents
that its use would not infringe privately owned rights.


Reference herein to any specific commercial product, process, or service by
trade name, trademark, manufacturer, or otherwise does not necessarily
constitute or imply its endorsement, recommendation, or favoring by the United
States Government or any agency thereof, or Battelle Memorial Institute. The
views and opinions of authors expressed herein do not necessarily state or
reflect those of the United States Government or any agency thereof.

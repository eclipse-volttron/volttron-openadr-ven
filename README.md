# OpenADRVen Agent


[![Passing?](https://github.com/VOLTTRON/volttron-openadr-ven/actions/workflows/run-tests.yml/badge.svg)](https://github.com/VOLTTRON/volttron-openadr-ven/actions/workflows/run-tests.yml)
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

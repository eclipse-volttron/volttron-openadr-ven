# OpenADRVen Agent

[![Pytests](https://github.com/VOLTTRON/volttron-openadr-ven/actions/workflows/run-tests.yml/badge.svg)](https://github.com/VOLTTRON/volttron-openadr-ven/actions/workflows/run-tests.yml)
[![pypi version](https://img.shields.io/pypi/v/volttron-openadr-ven.svg)](https://pypi.org/project/volttron-openadr-ven/)


OpenADR (Automated Demand Response) is a standard for alerting and responding to the need to adjust electric power consumption in response to fluctuations in grid demand.


# Prerequisites

* Python 3.8

## Python

<details>
<summary>To install Python 3.8, we recommend using <a href="https://github.com/pyenv/pyenv"><code>pyenv</code></a>.</summary>

```bash
# install pyenv
git clone https://github.com/pyenv/pyenv ~/.pyenv

# setup pyenv (you should also put these three lines in .bashrc or similar)
export PATH="${HOME}/.pyenv/bin:${PATH}"
export PYENV_ROOT="${HOME}/.pyenv"
eval "$(pyenv init -)"

# install Python 3.8
pyenv install 3.8.10

# make it available globally
pyenv global system 3.8.10
```
</details>

# Installation

Create and activate a virtual environment.

```shell
python -m venv env
source env/bin/activate
```

Installing volttron-platform-driver requires a running volttron instance.

```shell
pip install volttron

# Start platform with output going to volttron.log
volttron -vv -l volttron.log &
```

Install and start the volttron-openadr-ven.

```shell
vctl install volttron-openadr-ven --agent-config <path to agent config> --start
```

View the status of the installed agent

```shell
vctl status
```

# Agent Configuration

The required parameters for this agent are "ven_name" and "vtn_url". Below is an example of a correct configuration with optional parameters added.

```jsonpath
    {
        "ven_name": "PNNLVEN",
        "vtn_url": "https://eiss2demo.ipkeys.com/oadr2/OpenADR2/Simple/2.0b",

        # below are optional configurations

        # if you want/need to sign outgoing messages using a public-private key pair, provide the relative path to the cert_path and key_path
        # in this example, the keypair is stored in the directory named '~/.ssh/secret'
        "cert_path": "~/.ssh/secret/TEST_RSA_VEN_210923215148_cert.pem",
        "key_path": "~/.ssh/secret/TEST_RSA_VEN_210923215148_privkey.pem",

        # other optional configurations
        "debug": true,
        # if you are connecting to a legacy VTN (i.e. not conformant to OpenADR 2.0) you might want
        # to disable signatures when creating messages to be sent to a legacy VTN.
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

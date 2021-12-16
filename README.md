# OpenADRVen Agent

OpenADR (Automated Demand Response) is a standard for alerting and responding to the need to adjust electric power
consumption in response to fluctuations in grid demand.

## Agent Configuration

The required parameters for this agent are "ven_name", "vtn_url", and "openadr_client_type". Below is an example of a
correct configuration with optional parameters added.

```jsonpath
    {
        "ven_name": "PNNLVEN",
        "vtn_url": "https://eiss2demo.ipkeys.com/oadr2/OpenADR2/Simple/2.0b",
        "openadr_client_type": "IPKeysClient" # the list of valid client types are the class names of the OpenADRClient subclasses in ~volttron_openadr_ven/volttron_openadr_client.py

        # below are optional configurations

        # if you want/need to sign outgoing messages using a public-private key pair, provide the relative path to the cert_path and key_path
        # in this example, the keypair is stored in the directory named '~/.ssh/secret'
        "cert_path": "~/.ssh/secret/TEST_RSA_VEN_210923215148_cert.pem",
        "key_path": "~/.ssh/secret/TEST_RSA_VEN_210923215148_privkey.pem",

        # other optional configurations
        "debug": true,
        "disable_signature": true
    }
```

Save this configuration in a JSON file in your preferred location. An example of such a configuration is saved in the
root of this repository; the file is named `config_example1.json`


# Running the Agent

## Prerequisites

### VTN Server setup

Depending on the type of VTN that you are using, you need to configure your VTN to send events so that the OpenADRVen agent
can receive such events from your VTN.

#### IPKeys VTN setup

The community is currently testing this OpenADRVen agent against a IPKeys VTN. To configure the agent with the right
certificates, follow the instructions below:

Get VEN certificates at https://testcerts.kyrio.com/#/. Certificates can be stored anywhere on your machine, however,
it is recommended to place your keypair files in your ~/.ssh/ folder and make those files read-only.

* IPKeys VTN web browser console: https://eiss2demo.ipkeys.com/ui/home/#/login

To create an event, click "Events" tab. Then click the "+" icon to create an event. Use the template "PNNLTestEvent" or
"PNNLnontestevent" to create an event.

![Alt text](screenshots/test_event_screenshot_ipkeys.png?raw=true "Screenshot of Events page of IPKeys GUI")


## Installing the agent on Volttron 8.x

1. Start the Volttron platform on your machine.

```shell
volttron -vv -l volttron.log &
```

2. Tail the logs so that you can observe the logs coming from the Volttron OpenADR VEN agent.

```shell
tail -f volttron.log
```

3. Install the agent on Volttron.

```shell
vctl install <path to root directory of volttron-openadr-ven> \
--tag openadr \
--agent-config <path to agent config>
```

4. Verify status of agent.

```shell
vctl status
```

5.  Start the agent.
```shell
vctl start --tag openadr
```

## Installing the agent on Modular Volttron

1. Install the volttron server.

```shell
pip install volttron-server
```

2. Follow the same installation steps in the **Installing the agent on Volttron 8.x** section above.


# Development, Code Quality, and Standardization

### Prerequisites

* Python >=3.7
* Pip >=20.1
* Poetry >=1.16

## Environment setup

Note: This repo uses [Poetry](https://python-poetry.org/), a dependency management and packaging tool for Python. If you don't have Poetry installed on your machine, follow [these steps](https://python-poetry.org/docs/#installation) to install it on your machine.
To check if Poetry is installed, run `poetry --version`. If you receive the error 'command not found: poetry', add the following line to your '~/.bashrc' script: ```export PATH=$PATH:$HOME/.poetry/bin```.

1. Create virtual environment

By default, poetry creates a virtual environment in {cache-dir}/virtualenvs
({cache-dir}\virtualenvs on Windows). To configure 'poetry' to create the virtualenv inside this project's root
directory, run the following command:

[```poetry config virtualenvs.in-project true```](https://python-poetry.org/docs/configuration
)

Then to create the virtual environment itself, run the following command:

```shell
poetry shell
```

2. Install requirements

```shell
poetry install
```

Pro-tip: Later in your development, if you want update any of the dependencies using Poetry, use the following command:

```shell
poetry add <name of package>@latest

# example of updating volttron-client to newest release
poetry add volttron-client@latest
```

## OpenLeadr Notes (IMPORTANT)

The OpenADRVen agent uses a third-party library, OpenLeader[https://openleadr.org/docs/index.html], as the actual client.
However, the OpenADRVen agent had to modify some parts of that client in order to connect to the IPKeys VTN for testing. Specifically,
OpenADRVen agent extends the OpenLeadr client class and overrides some class methods.

Those parts that were modified are located in ~/volttron_openadr_ven/volttron_openleadr.py. Future releases of OpenLeadr could potentially and adversely
affect OpenADRVen agent if those releases directly or indirectly affect the modified code blocks. Thus, maintenance of this agent should closely monitor future changes to OpenLeadr.


## Git Hooks and Pre-commit

This repo provides pre-commit hooks to enforce code quality and standardization before pushing any commit to the repo. To use this tool locally,
run the following command.

```shell
pre-commit install
```

To check that pre-commit scripts are installed and properly run, run pre-commit on all the files:

```
pre-commit run --all
```

With pre-commit installed and configured, every time you run `git commit`, git will check your commit against a set of code linters. For details, see .pre-commit-config.yaml

This project installs the following tools to aid in code standardization and best practices:

## Black

This repo uses [Black](https://pypi.org/project/black/), an opinionated Python code formatter. To use Black to check and automagically reformat your code,
run the following command on your chosen Python file:

```shell
black <path to file>
```

## MyPy

This repo uses [MyPy](https://mypy.readthedocs.io/en/stable/), a static type checker for Python. To use MyPy on a Python file, run the following command:
```shell
mypy <path to file>
```

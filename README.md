# OpenADRVen Agent

OpenADR (Automated Demand Response) is a standard for alerting and responding to the need to adjust electric power
consumption in response to fluctuations in grid demand.

For further information about OpenADR and this agent, please see the OpenADR documentation in VOLTTRON ReadTheDocs.

## Agent Configuration

The only required parameters for this agent are "ven_name" and "vtn_url". Below is an example of a
correct configuration with optional parameters added.

```jsonpath
    {
        "ven_name": "PNNLVEN",
        "vtn_url": "https://eiss2demo.ipkeys.com/oadr2/OpenADR2/Simple/2.0b",

        # below are optional parameters

        # if you want/need to sign outgoing messages using a public-private key pair, you need to add a directory named "secret" in the top level
        # of this repo; then provide the relative path to the cert and key
        # below is an example
        # test certificates for IP Keys VTN's can be obtained at https://testcerts.kyrio.com/#/
        "cert_path": "secret/TEST_RSA_VEN_210923215148_certs/TEST_RSA_VEN_210923215148_cert.pem",
        "key_path": "secret/TEST_RSA_VEN_210923215148_certs/TEST_RSA_VEN_210923215148_privkey.pem",

        # other optional parameters
        "debug": true,
        "disable_signature": true,
        "openadr_client_type": "ipkeys" # defaults to "openleadr", for a list of valid client types see 'openadr_client_types' dictionary in ~volttron_openadr_ven/volttron_openadr_client.py
    }
```

Save this configuration in a JSON file in your preferred location; we recommend saving it in the `volttron_openadr_ven` directory.
An example of such a configuration is saved in the root of this repository; the file is named `config_example1.json`


# Quickstart

## Prerequisites

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

# Starting the agent

## Prerequisites

Now that we have the environment setup to run the OpenADRVen agent, we need to setup a local Volttron platform and configure the
remote VTN server that this OpenADRVen agent will connect to.

## Local Volttron platform setup

We need to start a local Volttron platform on the same machine that is hosting this OpenADRVen agent. Follow the [installation steps](https://volttron.readthedocs.io/en/develop/introduction/platform-install.html)
for installing a single instance of the Volttron platform. After you have installed and started the Volttron platform, we need
to get the platform's server key and create a public and secret keys. We will use these keys to configure the credentials of the
OpenADRVen agent so that the local Volttron platform can successfully authenticate the OpenADRVen agent.

**Steps**

1. With the local Volttron platform running, open a new shell and run `vctl auth serverkey`. Copy and paste output in the agent's config file. See example below:

```shell
$ vctl auth serverkey
FDIH6OBg0m3L2T6Jv_zUuQlSxYdgvTD3QOEye-vM-iI

# Paste the output in config file for agent

{
  {
  "ven_name": "PNNLVEN",
  ...
  "server_key": "FDIH6OBg0m3L2T6Jv_zUuQlSxYdgvTD3QOEye-vM-iI"
  }
}
```

2. On the same shell, run `vctl auth keypair`. Copy the values of `public` and `secret` and paste them in the agent's config file. See example below:

```shell
$ vctl auth keypair
{
  "public": "dyMf8g58ptiQTqI7EHbNr7PPFsAr2y-OIy1J-he_DCU",
  "secret": "iJa4mlZBomb3bDP8oRAN4IK8uXEqpl1MDg_te3aJzMo"
}

# Paste the output in config file for agent

{
  {
  "ven_name": "PNNLVEN",
  ...
  "server_key": "FDIH6OBg0m3L2T6Jv_zUuQlSxYdgvTD3QOEye-vM-iI",
  "agent_public": "csJBQqQDZ-pP_8E9FIgM9hvkAak6HriLkIQhP46ZFl4",
  "agent_secret": "4rv_l3oEzgmRxbPkGma2-tMhfPu47yyhi48ygF5hVQY"
  }
}
```

3. Add the public key, which was generated in the previous step, to the Volttron platform. Use `vctl auth add --credentials <public key>'.
An example of the command being run is shown below:

```shell
$ vctl auth add --credentials 'csJBQqQDZ-pP_8E9FIgM9hvkAak6HriLkIQhP46ZFl4'
```

## VTN Server setup

Depending on the type of VTN that you are using, you need to configure your VTN to send events so that the OpenADRVen agent
can receive such events from your VTN.


### IPKeys VTN configuration

The community is currently testing this OpenADRVen agent against a IPKeys VTN. To configure the agent with the right
certificates, follow the instructions below:

Get VEN certificates at https://testcerts.kyrio.com/#/. Store these certificates anywhere on your machine; it is highly
recommended to put these certificates in a directory called 'secret' that is located at the root level of this repo.

* IPKeys VTN web browser console: https://eiss2demo.ipkeys.com/ui/home/#/login

To create an event, click "Events" tab. Then click the "+" icon to create an event. Use the template "PNNLTestEvent" or
"PNNLnontestevent" to create an event.

![Alt text](screenshots/test_event_screenshot_ipkeys.png?raw=true "Screenshot of Events page of IPKeys GUI")

## Starting the OpenADRVen agent

Now that we have both the environment for OpenADRVen agent setup and the Volttron platform and VTN's configured properly,
we can finally run our OpenADRVen agent. Note: we are NOT installing this agent on the local Volttron platform. We will
simply run this agent on the host machine. Navigate to the root level of this repo. Then run the ~/volttron_openadr_ven/agent.py
module with the path to the agent configuration file that you created as noted in the "Agent Configuration" section at the beginning of this README.


```shell
poetry run python volttron_openadr_ven/agent.py <path to the config file>
```


# Development, Code Quality, and Standardization

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

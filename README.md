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

        # if you want/need to sign outgoing messages using a public-private key pair, use the following
        "cert": "/home/bono/Workplace/volttron-project/volttron-openadr-ven/secret/TEST_RSA_VEN_210923215148_certs/TEST_RSA_VEN_210923215148_cert.pem",
        "key": "/home/bono/Workplace/volttron-project/volttron-openadr-ven/secret/TEST_RSA_VEN_210923215148_certs/TEST_RSA_VEN_210923215148_privkey.pem",

        # other optional parameters
        "debug": true,
        "disable_signature": true
    }
```

## Volttron integration

To ensure that this agent is created within the Volttron framework, ensure that you set the following environmental variable
to the absolute path of the configuration JSON file for this agent. For example, on Linux, use the following example to set
the environmental variable AGENT_CONFIG to a path to your JSON config file:

`export AGENT_CONFIG /home/usr/path-to-my-config-file`

# Development

## Prerequisites

* Python >=3.7
* Pip >=20.1
* Poetry >=1.16


## Environment setup

Note: This repo uses [Poetry](https://python-poetry.org/), a dependency management and packaging tool for Python. If you don't have Poetry installed on your machine, follow [these steps](https://python-poetry.org/docs/#installation) to install it on your machine.
To check if Poetry is installed, run `poetry --version`. If you receive the error 'command not found: poetry', add the following line to your '~/.bashrc' script: ```export PATH=$PATH:$HOME/.poetry/bin```.

0. Install the required submodules

```git submodule update --init --recursive```

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

NOTE: Poetry needs the command 'python' in order to create a new shell. On Linux, if you only have python3 installed, run the following to link 'python' to 'python3':
```shell
sudo apt install python-is-python3
```

2. Install requirements

```shell
poetry install
```


## Code Quality and Standardization

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

# CI/CD

TODO:

# Building Wheel and Publishing to PyPi

TODO:

Build wheel
```python setup.py -q sdist bdist_wheel```

Check wheel
```check-wheel-contents dist/*.whl```
```tar tzf <>```

Test uploading
```twine upload --repository-url https://test.pypi.org/legacy/ dist/*```

Upload to PyPi
```python -m twin upload dist/*```


# Testing

## Ven Certificates

https://testcerts.kyrio.com/#/

## Test VTN's

* IPKeys: https://eiss2demo.ipkeys.com/ui/home/#/login

# Other

## Installing dependencies behind a proxy

If running this behind a PNNL VPN, run the following so Poetry can install all the dependencies:
See: https://leifengblog.net/blog/how-to-use-pip-behind-a-proxy/

```export https_proxy=http://proxy01.pnl.gov:3128```

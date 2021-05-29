# Prerequisites

* Python 3.7 >=
* Pip 20.1 >=

# Development

## Environment setup

* Create virtual environment

```shell
$ python -m venv env
$ source env/bin/activate
(env) $ pip install --upgrade pip
```

* Install requirements

```shell
(env) $ pip install -r requirements.txt
```

* Build volttron wheels (these packages are needed to provide the volttron-specific dependencies for this agent)

```shell
(env) $ pip install volttron_utils-0.1.1-py3-none-any.whl volttron_client-0.1.2-py3-none-any.whl
```


## Code Quality and Standardization

## Git Hooks and Pre-commit

This repo provides pre-commit hooks to enforce code quality and standardization before pushing any commit to the repo. To use this tool locally,
run the following commands:

```shell
(env) $ pre-commit install

# To check that pre-commit scripts are installed and properly run, run pre-commit on all the files
(env) $ pre-commit run --all
```

With pre-commit setup, every time you run "git commit", git will check your commit against a set of code linters. For details, see .pre-commit-config.yaml

## Black

This repo uses [Black](https://pypi.org/project/black/), an opinionated Python code formatter. To use Black to check and automagically reformat your code,
run the following command on your chosen Python file:

```shell
(env) $ black <path to file>
```

## MyPy

This repo uses [MyPy](https://mypy.readthedocs.io/en/stable/), a static type checker for Python. To use MyPy on a Python file, run the following command:
```shell
(env) $ mypy <path to file>
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

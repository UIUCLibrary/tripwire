+++++++++++
Development
+++++++++++

-----------------------
Development environment
-----------------------

Set up development environment on Mac and Linux

Using UV instead of pip
-----------------------

This way is better and faster than using pip.

.. code-block:: shell-session

    user@DEVMACHINE123 % uv venv
    user@DEVMACHINE123 % source ./venv/bin/activate
    (venv) user@DEVMACHINE123 % uv pip sync requirements-dev.txt
    (venv) user@DEVMACHINE123 % uv pip install -e .
    (venv) user@DEVMACHINE123 % pre-commit install

Using pip
---------

If you don't have uv installed:

.. code-block:: shell-session

    user@DEVMACHINE123 % python -m venv .venv
    user@DEVMACHINE123 % source .venv/bin/activate
    (venv) user@DEVMACHINE123 % pip install -r requirements-dev.txt
    (venv) user@DEVMACHINE123 % pip install -e .
    (venv) user@DEVMACHINE123 % pre-commit install

-------------
Running tests
-------------

To run test, you need to have pytest installed. If you are using the development environment, it should already be
installed. Tests are run by executing the pytest command.

.. code-block:: shell-session

    (venv) user@DEVMACHINE123 tripwire % pytest
    ================== test session starts ===================
    platform darwin -- Python 3.11.10, pytest-8.3.5, pluggy-1.5.0
    rootdir: /Users/user/PycharmProjects/UIUCLibrary/tripwire
    configfile: pyproject.toml
    collected 19 items

    tests/test_avtool.py .                             [  5%]
    tests/test_main.py .....                           [ 31%]
    tests/test_utils.py .........                      [ 78%]
    tests/test_validation.py ....                      [100%]

    =================== 19 passed in 0.17s ===================

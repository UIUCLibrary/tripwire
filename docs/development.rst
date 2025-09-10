+++++++++++
Development
+++++++++++

-----------------------
Development environment
-----------------------

Set up development environment on Mac and Linux

This project uses `uv <https://docs.astral.sh/uv/>`_ for project development. This is not a runtime requirements but it
is the primary development configuration so you will need to have
`uv installed <https://docs.astral.sh/uv/getting-started/installation/>`_ to get the
`dependency locks <https://docs.astral.sh/uv/concepts/projects/sync/>`_.

.. code-block:: shell-session

    user@DEVMACHINE123 % uv sync --group dev
    user@DEVMACHINE123 % source .venv/bin/activate
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

======================
Using the Command Line
======================

Getting Help
============

To get help at any point you can use the `--help` flag

.. code-block:: shell-session

    user@WORKMACHINE123 tripwire % tripwire --help
    usage: tripwire [-h] [--version] {get-hash,validate-checksums} ...

    options:
      -h, --help            show this help message and exit
      --version             show program's version number and exit

    subcommands:
      {get-hash,manifest-check,validate-checksums}


Tripwire Commands
=================

.. toctree::
   :maxdepth: 3
   :caption: Commands:
   :hidden:

   commands/get_hash
   commands/validate_checksums
   commands/manifest_check
   commands/metadata

Below is the hierarchy of commands that are available in Tripwire.

.. parsed-literal::
    tripwire
        ├── :ref:`get-hash <get_hash_command>`
        ├── :ref:`validate-checksums <validate_checksums>`
        ├── :ref:`manifest-check <manifest_check>`
        └── :ref:`metadata <metadata_subcommand>`
            ├── :ref:`show <metadata_show_command>`
            └── :ref:`validate <metadata_validate_command>`



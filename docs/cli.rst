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
      {get-hash,validate-checksums}


Get Hash
========

To get the hash value of a file, use the `get-hash` command. This will return the hash value of the file in the format
`<filename> --> <hash type>: <hash value>`.

.. code-block:: shell-session

    user@WORKMACHINE123 % tripwire get-hash somefile.wav
    somefile.wav --> md5: d41d8cd98f00b204e9800998ecf8427e


Validate Checksums
==================

To validate checksums for files in a directory, use the `validate-checksums` command. This search for all files within
a given path and search for a checksum file. The checksum file must be in the same directory as the files to be
validated. If the checksum does not match the expected value, you will get notified.

.. code-block:: shell-session

    user@WORKMACHINE123 % tripwire validate-checksums /path/to/directory

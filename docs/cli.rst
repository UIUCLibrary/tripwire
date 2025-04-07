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

Manifest Check
==============

Added in version 0.2.1

To check a manifest file against a directory, use the `manifest-check` command. This will check the files in the
manifest are present in the directory and show any files that are not supposed to be there.

Usage format: tripwire manifest-check <manifest_file> <search_path>

example:

.. code-block:: shell-session

    user@WORKMACHINE123 % tripwire manifest-check ./manifest-film.tsv ./sample_package/film
    Line: 7. Unable to locate: 2803015_film2of5_UIUCvUSC_FB_Sept1989_label.jpg

    Files found that were not included in manifest:
    * otherfile.txt

.. note::
    This will not use a excel file as a manifest. You will have to export the Excel file to a tab separated file first.
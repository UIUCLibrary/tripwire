.. _validate_checksums:

------------------
validate-checksums
------------------

To validate checksums for files in a directory, use the `validate-checksums` command. This search for all files within
a given path and search for a checksum file. The checksum file must be in the same directory as the files to be
validated. If the checksum does not match the expected value, you will get notified.

.. code-block:: shell-session

    user@WORKMACHINE123 % tripwire validate-checksums /path/to/directory

.. _get_hash_command:

--------
get-hash
--------

To get the hash value of a file, use the `get-hash` command. This will return the hash value of the file in the format
`<filename> --> <hash type>: <hash value>`.

.. code-block:: shell-session

    user@WORKMACHINE123 % tripwire get-hash somefile.wav
    somefile.wav --> md5: d41d8cd98f00b204e9800998ecf8427e


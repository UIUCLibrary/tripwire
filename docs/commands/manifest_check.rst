.. _manifest_check:

--------------
manifest-check
--------------

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


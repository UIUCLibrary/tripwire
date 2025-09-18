=========
Workflows
=========

Check Files in Manifest
========================

To verify all the files referenced in the manifest file are present, the
command :ref:`manifest-check <manifest_check>` can be used.

In order to do this, the manifest must be a single table tsv file encoded in
UTF-8. Excel files will NOT work on their own. It must be first converted.

Once converted, the command `tripwire manifest-check` followed by the path
to the .tsv file and the path to where the files are located, will initiate
the check.

The order of operations:

1. convert excel file into batches of .tsv files. One format per .tsv file
2. Use `tripwire manifest-check` command

Convert Excel to .tsv file
--------------------------

This has become increasing more challanging to do with more recent version of
Microsoft Excel. Here is how I was able to get it.

1. Open the manifest Excel document.
2. Copy the data for a single format into a new Excel document and using
   "Save As", save it using the File Format "UTF-16 Unicode Text".
3. Open that file in Microsoft Visual Studio Code (aka VS Code). **This is
   not the same as Microsoft Visual Studio**.
4. In the bottom right hand corner of VS Code, click the text that says
   "UTF-16". A text box will pop up, and select "Save With Encoding".
5. Select UTF-8.
6. Optionally change the extension of the file from .txt to .tsv.

You should now have a tsv that you can work with.

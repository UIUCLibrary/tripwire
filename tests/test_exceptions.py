import pytest
from uiucprescon.tripwire import exceptions as my_exceptions

class TestInvalidFileFormat:
    def test_with_file_named(self):
        with pytest.raises(my_exceptions.InvalidFileFormat) as error:
            raise my_exceptions.InvalidFileFormat("my_file.xlsx")
        assert str(error.value) == "Invalid file format. File: my_file.xlsx"

    def test_without_file_named(self):
        with pytest.raises(my_exceptions.InvalidFileFormat) as error:
            raise my_exceptions.InvalidFileFormat
        assert str(error.value) == "Invalid file format"

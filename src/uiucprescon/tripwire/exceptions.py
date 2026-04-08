"""Exceptions used in the tripwire package.

.. versionadded:: 0.3.7
    Added Exceptions module and relocated InvalidFileFormat to here
"""


class TripwireException(Exception):
    """Base class for all exceptions raised by this module."""


class InvalidFileFormat(TripwireException):
    """Invalid file format exception.

    .. versionchanged:: 0.3.7
        relocate from uiucprescon.tripwire.files to here
    """

    def __init__(self, file: str = "", details: str = "") -> None:
        """Initialize exception.

        Args:
            file: path of the file that caused the exception. Optional.
            details: details of the exception. Optional.
        """
        message = (
            f"Invalid file format. File: {file}"
            if file
            else "Invalid file format"
        )
        if details:
            message = f"{message}. Details: {details}"
        super().__init__(message)
        self.file_name = file
        self.details = details

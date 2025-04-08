"""Use for bootstrapping the standalone version of the application.

This is only used for freezing the application using PyInstaller.
"""
import multiprocessing

multiprocessing.freeze_support()
from uiucprescon.tripwire.main import main

if __name__ == "__main__":
    main()

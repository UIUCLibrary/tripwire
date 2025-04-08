from PyInstaller.utils.hooks import copy_metadata  # noqa: D100

datas = copy_metadata("uiucprescon-tripwire", recursive=True)

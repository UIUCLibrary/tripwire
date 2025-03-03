from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata("uiucprescon-tripwire", recursive=True)

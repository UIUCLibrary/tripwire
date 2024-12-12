from PyInstaller.utils.hooks import copy_metadata, collect_all

datas = copy_metadata("avtool", recursive=True)

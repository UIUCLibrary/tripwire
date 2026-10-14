import importlib.metadata
from PyInstaller.utils.hooks import copy_metadata, collect_all  # noqa: D100

try:
    datas, binaries, hiddenimports = collect_all('uiucprescon.tripwire')
    datas += copy_metadata("uiucprescon-tripwire", recursive=True)
except importlib.metadata.PackageNotFoundError as e:
    print("Package 'uiucprescon-tripwire' not found. Available packages:")
    for dist in importlib.metadata.distributions():
        print(dist.metadata['Name'])
    raise e

"""Keep tkinter importable when PyInstaller's Tcl auto-detection fails."""


def pre_find_module_path(_api) -> None:
    return

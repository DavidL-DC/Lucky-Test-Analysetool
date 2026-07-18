from pathlib import Path
import sys
import sysconfig


python_root = Path(sys.base_prefix)
stdlib_root = Path(sysconfig.get_path("stdlib"))
tcl_root = python_root / "tcl"
dll_root = python_root / "DLLs"

datas = [
    (str(stdlib_root / "tkinter"), "tkinter"),
    (str(tcl_root / "tcl8.6"), "_tcl_data"),
    (str(tcl_root / "tk8.6"), "_tk_data"),
]

binaries = [
    (str(dll_root / "_tkinter.pyd"), "."),
    (str(dll_root / "tcl86t.dll"), "."),
    (str(dll_root / "tk86t.dll"), "."),
]

hiddenimports = [
    "tkinter.constants",
    "tkinter.filedialog",
    "tkinter.font",
    "tkinter.messagebox",
    "tkinter.simpledialog",
    "tkinter.ttk",
]

# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "app" / "theme" / "theme.qss"), "app/theme"),
        (str(ROOT / "config" / "app.example.json"), "config"),
        (str(ROOT / "resources" / "app.ico"), "resources"),
        (str(ROOT / "packaging" / "Version.txt"), "."),
        (str(ROOT / "packaging" / "LICENSE.txt"), "."),
        (str(ROOT / "updates" / "latest.json"), "updates"),
    ],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "openpyxl",
        "reportlab",
        "reportlab.pdfbase",
        "reportlab.platypus",
        "app.windows.first_run_wizard",
        "app.core.update",
        "app.core.setup_state",
        "app.core.deploy_paths",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["flask", "sqlalchemy", "alembic"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JU-TAN-Office",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ROOT / "resources" / "app.ico"),
    version=str(ROOT / "packaging" / "file_version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="JU-TAN-Office",
)

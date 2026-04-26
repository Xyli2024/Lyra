# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["apple_lyrics/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.sip",
        "requests",
        "rich",
        "rich.live",
        "rich.panel",
        "rich.text",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "email", "html", "http", "urllib"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="apple-lyrics",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,        # no terminal window
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="apple-lyrics",
)

app = BUNDLE(
    coll,
    name="Apple Lyrics.app",
    icon="assets/icon.icns",
    bundle_identifier="com.xinyuli.apple-lyrics",
    info_plist={
        "CFBundleName": "Apple Lyrics",
        "CFBundleDisplayName": "Apple Lyrics",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "1",
        "LSUIElement": True,           # menu-bar only, no Dock icon
        "NSHighResolutionCapable": True,
        "NSAppleEventsUsageDescription": "Apple Lyrics needs to read the current track from Music.app.",
    },
)

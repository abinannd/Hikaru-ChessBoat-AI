# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

torch_datas, torch_binaries, torch_hiddenimports = collect_all('torch')
src_hiddenimports = collect_submodules('src')

a = Analysis(
    ['Main\\gui\\app.py'],
    pathex=['C:\\BRAIN-STORM\\chess-game-app\\Hikaru'],
    binaries=torch_binaries,
    datas=[
        ('Main/gui/assets', 'Main/gui/assets'), 
        ('models/best_model.pth', 'models'), 
        ('Main/gui/settings.json', 'Main/gui')
    ] + torch_datas,
    hiddenimports=src_hiddenimports + torch_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ChessAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Main\\gui\\assets\\icons\\chess_icon.ico'],
)

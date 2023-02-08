# -*- mode: python ; coding: utf-8 -*-


datas = []
hiddenimports = []


# add icon
datas.extend([
    ('../res/sparamviewer.ico', './res/'),
    ('../res/sparamviewer.png', './res/'),
    ('../res/sparamviewer.xbm', './res/'),
])


# Fix to get skrf required data folder included, see <https://github.com/scikit-rf/scikit-rf/issues/276>
import os, skrf as rf
skrf_data_dir = os.path.join(os.path.dirname(rf.__file__), 'data/*')
datas.extend([(skrf_data_dir, 'skrf/data/')])


# Fix for PIL, see <https://stackoverflow.com/a/46720070>
hiddenimports.extend(['PIL._tkinter_finder'])


# TODO: fix for Matplotlib, which does not find <share/matplotlib/mpl-data>...


hiddenimports.append('lib')
hiddenimports.append('gui')


block_cipher = None


a = Analysis(
    ['sparamviewer.py'],
    pathex=['./gui', './lib'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sparamviewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
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
    upx=True,
    upx_exclude=[],
    name='sparamviewer',
)

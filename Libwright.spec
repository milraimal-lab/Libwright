# -*- mode: python ; coding: utf-8 -*-
# Build with:  pyinstaller --noconfirm Libwright.spec   (or build.bat)

block_cipher = None

# Libwright is a plain Qt Widgets app. These parts of Qt are bundled by
# default but never loaded, so they are left out of the exe:
#   - software OpenGL fallback (no OpenGL/QML is used)
#   - PDF and SVG image/icon plugins and their libraries
#   - Qt networking and its own copy of OpenSSL (HTTP goes through
#     `requests`, which uses Python's ssl module and Python's OpenSSL)
#   - touch-input plugin and the ~100 Qt translation files (UI is English)
QT_UNUSED = (
    'opengl32sw.dll',
    'qt6pdf.dll', '/imageformats/qpdf.dll',
    'qt6svg.dll', '/imageformats/qsvg.dll', '/iconengines/qsvgicon.dll',
    'qt6network.dll', '/plugins/tls/', '/plugins/networkinformation/',
    'libcrypto-3-x64.dll', 'libssl-3-x64.dll',
    '/plugins/generic/',
    '/qt6/translations/',
)


def _wanted(entry):
    dest = entry[0].replace('\\', '/').lower()
    return not any(part in dest for part in QT_UNUSED)


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # mutagen formats
        'mutagen',
        'mutagen.mp3',
        'mutagen.mp4',
        'mutagen.flac',
        'mutagen.ogg',
        'mutagen.oggvorbis',
        'mutagen.oggopus',
        'mutagen.id3',
        'mutagen.id3._tags',
        'mutagen.id3._frames',
        'mutagen.id3._specs',
        'mutagen._util',
        # PyQt6 modules the app uses
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # never used
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'PyQt6.QtNetwork',
        # packaging / dev tools PyInstaller would otherwise drag in
        'setuptools',
        'pkg_resources',
        'wheel',
        'packaging',
        'unittest',
        'pydoc',
        'pydoc_data',
        '_pyrepl',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.binaries = [b for b in a.binaries if _wanted(b)]
a.datas = [d for d in a.datas if _wanted(d)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Libwright',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no black console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

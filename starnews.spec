# PyInstaller spec — run: python -m PyInstaller starnews.spec
# Produces dist/starnews/ folder (onedir — more reliable than onefile for Flask).

block_cipher = None

a = Analysis(
    ["starnews/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("config.yaml", "."),
        ("prompts", "prompts"),
        ("starnews/web/templates", "starnews/web/templates"),
    ],
    hiddenimports=[
        "google.genai",
        "flask",
        "click",
        "yaml",
        "docx",
        "trafilatura",
        "httpx",
    ],
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
    name="starnews",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name="starnews",
)

"""PyInstaller spec for packaging the Python backend into a single executable.

Usage:
  pip install pyinstaller
  pyinstaller backend.spec

This produces a standalone `backend.exe` (Windows) or `backend` (macOS/Linux)
that bundles the FastAPI server, SQLAlchemy, and all dependencies.
ML models (HuggingFace) are excluded from the bundle — they load on first use.
"""

# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["backend/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "backend.config",
        "backend.database",
        "backend.main",
        "backend.models.models",
        "backend.schemas.schemas",
        "backend.routers.intercept",
        "backend.routers.events",
        "backend.routers.essentials",
        "backend.routers.summary",
        "backend.routers.profile",
        "backend.routers.wishlist_digest",
        "backend.services.impulsivity_score",
        "backend.services.llm_router",
        "backend.services.product_classifier",
        "backend.services.challenge_generator",
        "backend.services.dark_pattern_detector",
        "backend.ml_services.classifier",
        "backend.ml_services.embeddings",
        "backend.ml_services.sentiment",
        "backend.ml_services.tasks",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "transformers",
        "sentence_transformers",
        "torch",
        "tensorflow",
        "onnxruntime",
    ],  # Exclude ML models from bundle (load at runtime)
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="anti-impulse-buyer-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

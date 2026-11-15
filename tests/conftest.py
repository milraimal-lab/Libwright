import os
import sys
from pathlib import Path

import pytest

# Make the app modules importable when running `pytest` from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Qt tests never need a real display
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


@pytest.fixture(scope='session')
def qapp():
    """One QApplication for the whole run (tests are skipped without PyQt6)."""
    widgets = pytest.importorskip('PyQt6.QtWidgets')
    return widgets.QApplication.instance() or widgets.QApplication([])


@pytest.fixture
def win(qapp, monkeypatch):
    """A fully isolated MainWindow: no remembered folders (so it never scans a
    real library), no writes to the user's settings file, and no modal dialogs
    (which would block forever with no event loop running)."""
    from PyQt6.QtWidgets import QMessageBox
    import mainwindow as mw
    monkeypatch.setattr(mw, '_load_settings', lambda: {})
    monkeypatch.setattr(mw, '_save_settings', lambda d: None)
    monkeypatch.setattr(QMessageBox, 'information', staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, 'warning', staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    w = mw.MainWindow()
    w.books.clear()
    w.import_books.clear()
    yield w
    # Clear the unsaved flags so closing can't stall on a confirmation
    for b in w.books + w.import_books:
        b.modified = False
    w.close()

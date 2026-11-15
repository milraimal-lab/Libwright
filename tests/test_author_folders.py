"""Author folders are created in the Library only for books that live there.

Books sitting in the Import inbox carry unvetted tags, so scanning or renaming
them must not leave empty author folders behind in the Library. The folder for
an imported book is created by the move itself.
"""
from pathlib import Path

import pytest

import scanner as sc


def _book(folder: Path, author: str, title: str = 'A Book') -> sc.Book:
    folder.mkdir(parents=True, exist_ok=True)
    f = folder / f'{title}.mp3'
    f.write_bytes(b'x')
    b = sc.Book()
    b.title, b.author = title, author
    b.files.append(sc.AudioFile(path=f, hydrated=True))
    return b


@pytest.fixture
def lib(win, tmp_path):
    """The window pointed at an empty temp Library."""
    root = tmp_path / 'Library'
    root.mkdir()
    win.last_folder = str(root)
    return root


def test_import_scan_leaves_the_library_alone(win, lib, tmp_path):
    win._on_import_book_ready(_book(tmp_path / 'Import' / 'x', 'Wrong Tagged Author'))
    assert len(win.import_books) == 1               # the book still shows up in Import
    assert list(lib.iterdir()) == []                # ...and nothing appeared in the Library


def test_library_scan_still_creates_the_author_folder(win, lib):
    win._on_book_ready(_book(lib / 'loose', 'Real Author'))
    assert (lib / 'Real Author').is_dir()


def test_renaming_an_import_author_creates_no_library_folder(win, lib, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QInputDialog
    monkeypatch.setattr(QInputDialog, 'getText', staticmethod(lambda *a, **k: ('New Name', True)))
    book = _book(tmp_path / 'Import' / 'x', 'Old Name')
    win.import_books.append(book)
    win._rename_author_group([book], 'Old Name')
    assert book.author == 'New Name'                # the rename itself still happens
    assert not (lib / 'New Name').exists()


def test_renaming_a_library_author_still_creates_the_folder(win, lib, monkeypatch):
    from PyQt6.QtWidgets import QInputDialog
    monkeypatch.setattr(QInputDialog, 'getText', staticmethod(lambda *a, **k: ('New Name', True)))
    book = _book(lib / 'loose', 'Old Name')
    win.books.append(book)
    win._rename_author_group([book], 'Old Name')
    assert (lib / 'New Name').is_dir()


def test_mixed_rename_only_touches_library_books(win, lib, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QInputDialog
    names = iter(['Library Author', 'Import Author'])
    monkeypatch.setattr(QInputDialog, 'getText', staticmethod(lambda *a, **k: (next(names), True)))
    in_lib = _book(lib / 'loose', 'A'); in_import = _book(tmp_path / 'Import' / 'x', 'B')
    win.books.append(in_lib); win.import_books.append(in_import)
    win._rename_author_group([in_lib], 'A')
    win._rename_author_group([in_import], 'B')
    assert sorted(p.name for p in lib.iterdir() if p.is_dir()) == ['Library Author', 'loose']


def test_moving_an_import_book_in_creates_its_author_folder(lib, tmp_path):
    """The folder an import book needs is made by the move, not by the scan."""
    import organizer as org
    book = _book(tmp_path / 'Import' / 'x', 'Moved Author', 'Moved Book')
    dest = org.build_folder_path(str(lib), book.author, '', '', book.title)
    src = book.files[0].path
    done, errors, *_ = org.apply_moves([(src, dest / src.name)], copy=False, skip_existing=True)
    assert (done, errors) == (1, [])
    assert (lib / 'Moved Author' / 'Moved Book' / 'Moved Book.mp3').is_file()

"""Every path the app builds must be cleaned the same way.

Auto-organise, the misplacement check and author folders use
organizer.sanitize (illegal characters removed). The Files-tab rename and the
Move / Organise tab used to use a second helper that turned them into '_'
instead, so one title could end up with two different folder names, and the
second helper turned an empty series into a literal "Unknown" folder.
"""
from pathlib import Path

import pytest

import organizer as org
import scanner as sc


def _book(tmp: Path, title='Title: The Sequel', author='Smith/Jones', series='', num=''):
    f = tmp / 'src' / 'a.mp3'
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(b'x')
    b = sc.Book()
    b.title, b.author, b.series, b.series_num = title, author, series, num
    b.files.append(sc.AudioFile(path=f, hydrated=True))
    return b


@pytest.fixture
def move_tab(qapp, tmp_path, monkeypatch):
    """Move/Organise tab whose worker thread just records the planned moves."""
    import tabs
    planned = []

    class FakeThread:
        def __init__(self, moves, copy, skip):
            planned.extend(moves)
            self.finished = self.progress = self.error = type(
                'S', (), {'connect': lambda *a: None})()
        def start(self): pass
        def isRunning(self): return False

    monkeypatch.setattr(tabs, 'OrganizeThread', FakeThread)
    t = tabs.MoveOrganiseTab()
    t.set_default_destination(str(tmp_path / 'Lib'))
    t.planned = planned
    return t


def test_move_tab_without_series_has_no_unknown_folder(move_tab, tmp_path):
    book = _book(tmp_path, title='Standalone', author='Ann Author')
    move_tab.set_books([book], [book])
    move_tab._move_files()
    (_, dst), = move_tab.planned
    assert 'Unknown' not in dst.parts
    assert dst == tmp_path / 'Lib' / 'Ann Author' / 'Standalone' / 'Standalone.mp3'


def test_move_tab_matches_auto_organise(move_tab, tmp_path):
    book = _book(tmp_path, series='Saga: Part', num='3')
    move_tab.set_books([book], [book])
    move_tab._move_files()
    (_, dst), = move_tab.planned
    auto = org.build_folder_path(str(tmp_path / 'Lib'), book.author, book.series,
                                 book.series_num, book.title)
    assert dst.parent == auto                      # same folder the auto-organiser picks
    assert '_' not in str(dst.relative_to(tmp_path / 'Lib'))


def test_move_tab_preview_shows_the_real_destination(move_tab, tmp_path):
    book = _book(tmp_path, series='Saga', num='3')
    move_tab.set_books([book], [book])
    preview = move_tab._group_rows[0]['preview'].text()
    move_tab._move_files()
    (_, dst), = move_tab.planned
    assert preview == '→  ' + str(dst.parent)


def test_files_tab_rename_uses_the_same_cleaning(qapp, tmp_path):
    from tabs import FilesTab
    book = _book(tmp_path, title='Title: The Sequel')
    tab = FilesTab()
    tab.set_book(book)
    tab._use_counter.setChecked(False)
    assert tab._new_names_for(book) == [org.sanitize('Title: The Sequel')]   # 'Title The Sequel'


def test_rename_to_nothing_keeps_the_original_name(qapp, tmp_path):
    from tabs import FilesTab
    book = _book(tmp_path, title='Anything')
    book.narrator = ''
    tab = FilesTab()
    tab.set_book(book)
    tab._pattern_edit.setText('{narrator}')
    tab._use_counter.setChecked(False)
    assert tab._new_names_for(book) == ['a']        # not a file literally named "Unknown"

import asyncio
from types import SimpleNamespace

import pytest

from streamrip import Handle, ProgressManager, set_progress_manager
from streamrip.media.album import Album
from streamrip.media.track import Track
from streamrip.progress import (
    RichProgressManager,
    add_title,
    clear_progress,
    get_progress_callback,
    get_progress_manager,
    remove_title,
)


class RecordingManager:
    """Minimal custom backend that records every call."""

    def __init__(self):
        self.calls = []

    def get_callback(self, total: int, desc: str) -> Handle:
        self.calls.append(("get_callback", total, desc))
        updates = []
        return Handle(
            updates.append,
            lambda: self.calls.append(("done", tuple(updates))),
        )

    def add_title(self, title: str) -> None:
        self.calls.append(("add_title", title))

    def remove_title(self, title: str) -> None:
        self.calls.append(("remove_title", title))

    def cleanup(self) -> None:
        self.calls.append(("cleanup",))


@pytest.fixture(autouse=True)
def restore_default_manager():
    yield
    set_progress_manager(None)


def test_default_manager_is_rich_and_satisfies_protocol():
    manager = get_progress_manager()
    assert isinstance(manager, RichProgressManager)
    assert isinstance(manager, ProgressManager)


def test_custom_manager_receives_callbacks():
    manager = RecordingManager()
    set_progress_manager(manager)

    with get_progress_callback(True, 100, "Track 1") as update:
        update(40)
        update(60)

    assert manager.calls == [
        ("get_callback", 100, "Track 1"),
        ("done", (40, 60)),
    ]


def test_disabled_callback_skips_custom_manager():
    manager = RecordingManager()
    set_progress_manager(manager)

    with get_progress_callback(False, 100, "Track 1") as update:
        update(40)

    assert manager.calls == []


def test_custom_manager_receives_title_and_cleanup_calls():
    manager = RecordingManager()
    set_progress_manager(manager)

    add_title("An Album")
    remove_title("An Album")
    clear_progress()

    assert manager.calls == [
        ("add_title", "An Album"),
        ("remove_title", "An Album"),
        ("cleanup",),
    ]


def test_none_restores_default_manager():
    set_progress_manager(RecordingManager())
    assert isinstance(get_progress_manager(), RecordingManager)

    set_progress_manager(None)
    assert isinstance(get_progress_manager(), RichProgressManager)


def test_custom_manager_receives_album_download_calls():
    manager = RecordingManager()
    set_progress_manager(manager)

    class FakeDownloadable:
        extension = "flac"
        source = "qobuz"

        async def size(self):
            return 100

        async def download(self, path, callback):
            callback(100)

    config = SimpleNamespace(
        session=SimpleNamespace(
            downloads=SimpleNamespace(concurrency=False, max_connections=1),
            conversion=SimpleNamespace(enabled=False),
            cli=SimpleNamespace(progress_bars=True),
        )
    )
    track = Track(
        SimpleNamespace(title="Track 1", tracknumber=1),
        FakeDownloadable(),
        config,
        "/tmp",
        None,
        db=None,
    )
    album = Album(SimpleNamespace(album="Rumours"), [], config, "/tmp", db=None)

    async def run():
        await album.preprocess()
        await track.download()
        await album.postprocess()

    asyncio.run(run())

    assert manager.calls == [
        ("add_title", "Rumours"),
        ("get_callback", 100, "Track 1"),
        ("done", (100,)),
        ("remove_title", "Rumours"),
    ]

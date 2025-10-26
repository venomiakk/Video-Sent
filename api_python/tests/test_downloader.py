import sys
from pathlib import Path

# Ensure `app` package (located in api_python/) is on sys.path so imports inside the module work
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.modules.v1.downloader import downloader
from app.core.exceptions import DownloadError


class FakeYTDLP:
    def __init__(self, opts=None):
        self.opts = opts or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        # metadata-only call (quiet): return a title
        if not download and self.opts.get("quiet"):
            return {"title": "Test Title"}

        # download call: try using outtmpl to write a fake file and return info
        outtmpl = self.opts.get("outtmpl")
        if outtmpl and "%(ext)s" in outtmpl:
            ext = "wav"
            # pick codec if provided in postprocessors
            try:
                pp = self.opts.get("postprocessors", [])
                if pp and isinstance(pp, list):
                    codec = pp[0].get("preferredcodec")
                    if codec:
                        ext = codec
            except Exception:
                pass

            path_str = outtmpl.replace("%(ext)s", ext)
            Path(path_str).parent.mkdir(parents=True, exist_ok=True)
            Path(path_str).write_text("FAKE AUDIO")
            return {"title": "DL Title"}

        # fallback
        return {}


def test_download_audio_existing_file_fetch_metadata(tmp_path, monkeypatch):
    url = "https://example.com/video"
    filename_hash = "hash123"
    # create existing file
    file_path = tmp_path / f"{filename_hash}.wav"
    file_path.write_text("exists")

    # monkeypatch yt_dlp.YoutubeDL used in downloader to our fake
    monkeypatch.setattr(downloader, "yt_dlp", type("m", (), {"YoutubeDL": FakeYTDLP}))

    base, path, title = downloader.download_audio(url, filename_hash, out_dir=tmp_path)

    assert base == filename_hash
    assert Path(path) == file_path
    assert title == "Test Title"


def test_download_audio_download_and_create_file(tmp_path, monkeypatch):
    url = "https://example.com/video"
    filename_hash = "hash456"

    # ensure no file exists initially
    assert not any(tmp_path.glob(f"{filename_hash}.*"))

    monkeypatch.setattr(downloader, "yt_dlp", type("m", (), {"YoutubeDL": FakeYTDLP}))

    base, path, title = downloader.download_audio(
        url,
        filename_hash,
        out_dir=tmp_path,
        audio_codec="wav",
        sample_rate=16000,
        channels=1,
    )

    assert base == filename_hash
    p = Path(path)
    assert p.exists()
    assert title == "DL Title"


def test_download_audio_raises_download_error(tmp_path, monkeypatch):
    url = "https://example.com/video"
    filename_hash = "hash789"

    class BrokenYTDLP(FakeYTDLP):
        def extract_info(self, url, download=False):
            raise RuntimeError("yt-dlp failed")

    monkeypatch.setattr(downloader, "yt_dlp", type("m", (), {"YoutubeDL": BrokenYTDLP}))

    with pytest.raises(DownloadError):
        downloader.download_audio(url, filename_hash, out_dir=tmp_path)

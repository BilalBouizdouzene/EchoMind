import io
import tarfile
import wave

from scripts.download_corpus import (
    _audio_source,
    _download_archive_subset,
    _select_rows,
)


class _FakeResponse:
    def __init__(self, payload: bytes):
        self.content = payload
        self.raw = io.BytesIO(payload)

    def raise_for_status(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.raw.close()


class _FakeSession:
    def __init__(self, tsv: bytes, archive: bytes):
        self.tsv = tsv
        self.archive = archive

    def get(self, url, **_kwargs):
        return _FakeResponse(self.tsv if url.endswith("test.tsv?download=true") else self.archive)


def _wav_bytes() -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16_000)
        audio.writeframes(b"\0\0" * 1_600)
    return output.getvalue()


def _tar_gz(members: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return output.getvalue()


def test_fleurs_subset_is_evenly_spaced_and_deterministic():
    rows = [{"id": index, "raw_transcription": f"utterance {index}"} for index in range(10)]

    selected = _select_rows(rows, 4)

    assert [row["id"] for row in selected] == [0, 3, 6, 9]


def test_fleurs_subset_skips_duplicate_transcripts():
    rows = [
        {"id": 1, "raw_transcription": "same"},
        {"id": 2, "raw_transcription": "same"},
        {"id": 3, "transcription": "different"},
    ]

    assert [row["id"] for row in _select_rows(rows, 5)] == [1, 3]


def test_audio_url_supports_viewer_audio_list_and_object():
    assert _audio_source({"audio": [{"src": "https://example.org/a.wav"}]}) == (
        "https://example.org/a.wav"
    )
    assert _audio_source({"audio": {"src": "https://example.org/b.wav"}}) == (
        "https://example.org/b.wav"
    )


def test_official_test_archive_fallback_extracts_only_valid_audio(tmp_path):
    tsv = (
        b"1980\tfirst.wav\tFirst sentence.\tfirst sentence\tchars\t1600\tMALE\n"
        b"1914\tsecond.wav\tSecond sentence.\tsecond sentence\tchars\t1600\tFEMALE\n"
        b"1900\torphan.wav\tOrphan sentence.\torphan sentence\tchars\t1600\tMALE\n"
    )
    archive = _tar_gz(
        {
            "audio/first.wav": _wav_bytes(),
            "audio/second.wav": _wav_bytes(),
            "audio/orphan.wav": _wav_bytes(),
            "audio/unused.wav": b"not a wav",
        }
    )
    stale_path = tmp_path / "data/evaluation/corpus/fleurs/en/test/orphan.wav"
    stale_path.parent.mkdir(parents=True)
    stale_path.write_bytes(_wav_bytes())

    rows = _download_archive_subset(
        tmp_path,
        _FakeSession(tsv, archive),
        config="en_us",
        language="en",
        split="test",
        limit=2,
    )

    assert [row["reference_text"] for row in rows] == ["First sentence.", "Second sentence."]
    assert all("orphan" not in row["id"] for row in rows)
    assert all(row["source_split"] == "test" for row in rows)
    assert all(row["speaker_id"] == "unknown" for row in rows)
    assert all((tmp_path / row["audio_path"]).is_file() for row in rows)

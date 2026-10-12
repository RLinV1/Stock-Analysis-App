import hashlib
import io
import json
import uuid

import pytest

from portfolio_worker import Claimed, upload_artifacts


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.corrupt = False

    def put_object(self, *, Bucket, Key, Body):
        self.objects[(Bucket, Key)] = Body

    def get_object(self, *, Bucket, Key):
        content = self.objects[(Bucket, Key)]
        if self.corrupt:
            content += b"tampered"
        return {"Body": io.BytesIO(content)}


def job():
    return Claimed(uuid.UUID(int=1), uuid.UUID(int=2), uuid.UUID(int=3), {})


def test_attempt_scoped_artifacts_and_index_are_verified(tmp_path):
    (tmp_path / "report.json").write_text('{"state":"completed"}', encoding="utf-8")
    (tmp_path / "request.json").write_text('{"contract_version":1}', encoding="utf-8")
    (tmp_path / ".run.lock").write_text("machine-local", encoding="utf-8")
    s3 = FakeS3()
    key, digest = upload_artifacts(s3, "lab-artifacts", job(), tmp_path)
    assert key == f"runs/{job().run_id}/attempts/{job().attempt_id}/artifact-index.json"
    content = s3.objects[("lab-artifacts", key)]
    assert hashlib.sha256(content).hexdigest() == digest
    index = json.loads(content)
    assert [item["path"] for item in index["files"]] == ["report.json", "request.json"]
    assert all(item["key"].startswith(f"runs/{job().run_id}/attempts/{job().attempt_id}/")
               for item in index["files"])
    assert not any(".run.lock" in object_key for _, object_key in s3.objects)


def test_readback_mismatch_prevents_index_publication(tmp_path):
    (tmp_path / "report.json").write_text("{}", encoding="utf-8")
    s3 = FakeS3()
    s3.corrupt = True
    with pytest.raises(ValueError, match="readback hash mismatch"):
        upload_artifacts(s3, "lab-artifacts", job(), tmp_path)
    assert not any(key.endswith("artifact-index.json") for _, key in s3.objects)


def test_missing_report_is_not_publishable(tmp_path):
    (tmp_path / "request.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="missing its report"):
        upload_artifacts(FakeS3(), "lab-artifacts", job(), tmp_path)

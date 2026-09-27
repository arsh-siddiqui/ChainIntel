"""Evidence management service with SHA-256 integrity and safe file handling."""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.envelope import AppError
from app.models import Evidence
from app.services.audit import log_action
from app.services.serializers import evidence_dict
from app.utils.datetime import utcnow
from app.utils.hashing import sha256_bytes, sha256_file

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".txt", ".csv", ".json", ".zip", ".log", ".md", ".har"}


def _safe_filename(original: str) -> str:
    name = os.path.basename(original or "upload.bin")
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = name[-80:] if len(name) > 80 else name
    return f"{uuid.uuid4().hex[:12]}_{name or 'upload.bin'}"


def save_upload(
    db: Session,
    *,
    case_id: int | None,
    evidence_type: str,
    title: str,
    description: str | None,
    source: str | None,
    filename: str,
    content: bytes,
) -> Evidence:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) == 0:
        raise AppError(400, "EMPTY_FILE", "The uploaded file is empty.")
    if len(content) > max_bytes:
        raise AppError(413, "FILE_TOO_LARGE", f"File exceeds the {settings.max_upload_mb} MB upload limit.")
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise AppError(
            400,
            "UNSUPPORTED_FILE_TYPE",
            f"File type '{extension or 'unknown'}' is not allowed. Permitted: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    evidence_dir = Path(settings.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename)
    file_path = evidence_dir / safe_name
    file_path.write_bytes(content)

    evidence = Evidence(
        case_id=case_id,
        type=evidence_type,
        title=title,
        description=description,
        source=source,
        file_path=str(file_path),
        file_name=os.path.basename(filename),
        sha256=sha256_bytes(content),
        size_bytes=len(content),
    )
    db.add(evidence)
    db.commit()
    log_action(db, "evidence_uploaded", "evidence", evidence.id, {"title": title, "sha256": evidence.sha256, "case_id": case_id})
    return evidence


def save_note(
    db: Session,
    *,
    case_id: int | None,
    evidence_type: str,
    title: str,
    description: str | None,
    source: str | None,
    content_text: str,
) -> Evidence:
    if not content_text.strip():
        raise AppError(400, "EMPTY_NOTE", "Note content is required.")
    evidence = Evidence(
        case_id=case_id,
        type=evidence_type,
        title=title,
        description=description,
        source=source,
        content_text=content_text,
        sha256=sha256_bytes(content_text.encode("utf-8")),
        size_bytes=len(content_text.encode("utf-8")),
    )
    db.add(evidence)
    db.commit()
    log_action(db, "evidence_added", "evidence", evidence.id, {"title": title, "type": evidence_type, "case_id": case_id})
    return evidence


def list_evidence(db: Session, case_id: int | None = None, evidence_type: str | None = None, search: str | None = None, page: int = 1, page_size: int = 25):
    from app.utils.pagination import clamp, meta

    page, page_size = clamp(page, page_size)
    query = db.query(Evidence)
    if case_id:
        query = query.filter(Evidence.case_id == case_id)
    if evidence_type:
        query = query.filter(Evidence.type == evidence_type)
    if search:
        like = f"%{search}%"
        query = query.filter(Evidence.title.ilike(like) | Evidence.description.ilike(like))
    total = query.count()
    items = query.order_by(Evidence.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [evidence_dict(e) for e in items], meta(page, page_size, total)


def get_evidence(db: Session, evidence_id: int) -> Evidence | None:
    return db.query(Evidence).filter(Evidence.id == evidence_id).one_or_none()


def download_evidence(db: Session, evidence_id: int) -> tuple[Path, str]:
    evidence = get_evidence(db, evidence_id)
    if evidence is None:
        raise AppError(404, "EVIDENCE_NOT_FOUND", f"Evidence {evidence_id} does not exist.")
    if not evidence.file_path or not Path(evidence.file_path).exists():
        raise AppError(404, "FILE_NOT_FOUND", "No file is attached to this evidence record.")
    return Path(evidence.file_path), evidence.file_name or "evidence.bin"


def verify_integrity(db: Session, evidence: Evidence) -> bool:
    """Recompute SHA-256 for file-backed evidence; text evidence is verified from content_text."""
    if evidence.file_path and Path(evidence.file_path).exists():
        return sha256_file(evidence.file_path) == (evidence.sha256 or "")
    if evidence.content_text is not None:
        return sha256_bytes(evidence.content_text.encode("utf-8")) == (evidence.sha256 or "")
    return False

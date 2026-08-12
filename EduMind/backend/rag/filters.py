"""
Subject / stage normalization for RAG scoping.

Seed resources store subject as e.g. "高中 数学".
Students store subject="数学", grade="高一".
These helpers map both sides onto (subject_key, stage) so retrieval
can filter Qdrant payload + SQL without cross-subject leakage.
"""

from __future__ import annotations

import re

# Canonical stages used in seed subject strings
STAGES: tuple[str, ...] = ("小学", "初中", "高中", "大学", "职业")

# Longer names first so "计算机科学" wins over bare "计算机"
SUBJECT_KEYS: tuple[str, ...] = (
    "计算机科学",
    "信息技术",
    "数学",
    "英语",
    "物理",
    "化学",
    "生物",
    "语文",
    "历史",
    "地理",
    "政治",
    "计算机",
)

_GRADE_TO_STAGE: tuple[tuple[str, str], ...] = (
    ("高一", "高中"),
    ("高二", "高中"),
    ("高三", "高中"),
    ("高中", "高中"),
    ("初一", "初中"),
    ("初二", "初中"),
    ("初三", "初中"),
    ("七年级", "初中"),
    ("八年级", "初中"),
    ("九年级", "初中"),
    ("初中", "初中"),
    ("一年级", "小学"),
    ("二年级", "小学"),
    ("三年级", "小学"),
    ("四年级", "小学"),
    ("五年级", "小学"),
    ("六年级", "小学"),
    ("小学", "小学"),
    ("大一", "大学"),
    ("大二", "大学"),
    ("大三", "大学"),
    ("大四", "大学"),
    ("大学", "大学"),
    ("职业", "职业"),
)


def extract_subject_key(text: str | None) -> str | None:
    """Pull canonical subject key from '高中 数学' / '数学' / '计算机科学'."""
    raw = (text or "").strip()
    if not raw:
        return None
    for key in SUBJECT_KEYS:
        if key in raw:
            return key
    # Fallback: last whitespace-separated token
    parts = re.split(r"[\s/|·]+", raw)
    return parts[-1] if parts and parts[-1] else raw


def extract_stage(text: str | None) -> str | None:
    """Pull stage from resource subject or free text."""
    raw = (text or "").strip()
    if not raw:
        return None
    for stage in STAGES:
        if stage in raw:
            return stage
    return None


def stage_from_grade(grade: str | None) -> str | None:
    """Map student grade (高一/初二/…) → stage (高中/初中/…)."""
    raw = (grade or "").strip()
    if not raw:
        return None
    for needle, stage in _GRADE_TO_STAGE:
        if needle in raw:
            return stage
    return extract_stage(raw)


def parse_resource_subject(subject: str | None) -> tuple[str | None, str | None]:
    """Return (subject_key, stage) for a LearningResource.subject string."""
    return extract_subject_key(subject), extract_stage(subject)


def resource_matches_scope(
    resource_subject: str | None,
    subject_key: str | None,
    stage: str | None,
    *,
    require_stage: bool = False,
) -> bool:
    """
    Whether a resource subject string belongs to the requested scope.

    - subject_key is a hard gate when provided.
    - stage: when require_stage=True must match; otherwise stage mismatch rejects
      only if the resource itself carries a stage tag.
    """
    raw = resource_subject or ""
    key, res_stage = parse_resource_subject(raw)

    if subject_key:
        ok = False
        if key and (key == subject_key or subject_key in key or key in subject_key):
            ok = True
        elif subject_key in raw:
            ok = True
        if not ok:
            return False

    if not stage:
        return True
    if require_stage:
        return res_stage == stage
    # Soft: reject only explicit cross-stage resources
    if res_stage and res_stage != stage:
        return False
    return True

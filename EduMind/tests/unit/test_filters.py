"""
Unit Tests for subject/stage filtering and Chinese-English name compatibility.
"""

import sys
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from rag.filters import (
    extract_subject_key,
    extract_stage,
    stage_from_grade,
    parse_resource_subject,
    resource_matches_scope,
)


class TestExtractSubjectKey(unittest.TestCase):
    """Verify subject key extraction handles Chinese and English names."""

    def test_chinese_subject(self):
        self.assertEqual(extract_subject_key("数学"), "数学")
        self.assertEqual(extract_subject_key("高中 数学"), "数学")
        self.assertEqual(extract_subject_key("计算机科学"), "计算机科学")

    def test_english_subject(self):
        self.assertEqual(extract_subject_key("Mathematics"), "数学")
        self.assertEqual(extract_subject_key("math"), "数学")
        self.assertEqual(extract_subject_key("Physics"), "物理")
        self.assertEqual(extract_subject_key("English"), "英语")
        self.assertEqual(extract_subject_key("Computer Science"), "计算机科学")

    def test_english_with_stage(self):
        self.assertEqual(extract_subject_key("High School Mathematics"), "数学")
        self.assertEqual(extract_subject_key("College Physics"), "物理")

    def test_empty_and_none(self):
        self.assertIsNone(extract_subject_key(""))
        self.assertIsNone(extract_subject_key(None))
        self.assertIsNone(extract_subject_key("   "))

    def test_unknown_fallback(self):
        # Unknown subject returns last token as-is
        result = extract_subject_key("量子力学")
        self.assertEqual(result, "量子力学")


class TestStageExtraction(unittest.TestCase):
    """Verify stage extraction from various formats."""

    def test_chinese_stage_in_subject(self):
        self.assertEqual(extract_stage("高中 数学"), "高中")
        self.assertEqual(extract_stage("初中 英语"), "初中")
        self.assertEqual(extract_stage("大学 物理"), "大学")

    def test_grade_to_stage(self):
        self.assertEqual(stage_from_grade("高一"), "高中")
        self.assertEqual(stage_from_grade("高三"), "高中")
        self.assertEqual(stage_from_grade("初二"), "初中")
        self.assertEqual(stage_from_grade("九年级"), "初中")
        self.assertEqual(stage_from_grade("小学"), "小学")
        self.assertEqual(stage_from_grade("大一"), "大学")

    def test_no_stage(self):
        self.assertIsNone(extract_stage("数学"))
        self.assertIsNone(extract_stage("Mathematics"))
        self.assertIsNone(stage_from_grade(""))
        self.assertIsNone(stage_from_grade(None))


class TestResourceMatchesScope(unittest.TestCase):
    """Verify scope filtering prevents cross-subject leakage."""

    def test_same_subject_match(self):
        self.assertTrue(resource_matches_scope("数学", "数学", None))
        self.assertTrue(resource_matches_scope("高中 数学", "数学", "高中"))

    def test_cross_subject_rejected(self):
        self.assertFalse(resource_matches_scope("物理", "数学", None))
        self.assertFalse(resource_matches_scope("高中 物理", "数学", "高中"))

    def test_english_resource_matches_chinese_student(self):
        """Resource seeded with 'Mathematics' should match student subject '数学'."""
        self.assertTrue(resource_matches_scope("Mathematics", "数学", None))
        self.assertTrue(resource_matches_scope("High School Mathematics", "数学", "高中"))

    def test_cross_language_cross_subject_rejected(self):
        """English Physics should NOT match Chinese 数学."""
        self.assertFalse(resource_matches_scope("Physics", "数学", None))

    def test_stage_mismatch_rejected(self):
        # Resource tagged 高中 should not match student in 初中
        self.assertFalse(resource_matches_scope("高中 数学", "数学", "初中"))
        # But resource without stage tag should match any stage
        self.assertTrue(resource_matches_scope("数学", "数学", "高中"))

    def test_require_stage_strict(self):
        # When require_stage=True, resource must have matching stage
        self.assertFalse(resource_matches_scope("数学", "数学", "高中", require_stage=True))
        self.assertTrue(resource_matches_scope("高中 数学", "数学", "高中", require_stage=True))

    def test_no_subject_key_allows_all(self):
        # When subject_key is None, subject gate is skipped
        self.assertTrue(resource_matches_scope("物理", None, None))
        self.assertTrue(resource_matches_scope("高中 化学", None, "高中"))


if __name__ == "__main__":
    unittest.main()

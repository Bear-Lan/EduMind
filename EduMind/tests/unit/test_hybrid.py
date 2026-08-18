"""
Unit Tests for Hybrid Retrieval (keyword + RRF).

Tests are fully offline — no embedding API, no Qdrant, no LLM calls.
"""

import sys
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from rag.hybrid import extract_precise_terms, reciprocal_rank_fusion


class TestExtractPreciseTerms(unittest.TestCase):
    """Verify precise-term extraction from Chinese/English queries."""

    def test_problem_number_chinese(self):
        terms = extract_precise_terms("请帮我讲解第3题的解法")
        self.assertIn("第3题", terms)

    def test_example_number(self):
        terms = extract_precise_terms("例2怎么解")
        self.assertIn("例2", terms)

    def test_section_ref(self):
        terms = extract_precise_terms("§1.2 的内容是什么")
        self.assertTrue(any("1.2" in t for t in terms))

    def test_cn_formula_name(self):
        terms = extract_precise_terms("请讲勾股定理的证明")
        self.assertIn("勾股定理", terms)

    def test_en_proper_noun(self):
        terms = extract_precise_terms("Explain Newton's second law")
        self.assertTrue(any("Newton" in t for t in terms))

    def test_empty_query(self):
        self.assertEqual(extract_precise_terms(""), [])
        self.assertEqual(extract_precise_terms(None), [])

    def test_dedup_overlapping(self):
        terms = extract_precise_terms("勾股定理 勾股定理 勾股定理")
        # Should not return the same term three times
        cn_terms = [t for t in terms if "勾股" in t]
        self.assertLessEqual(len(cn_terms), 1)

    def test_max_terms_limit(self):
        long_query = " ".join([f"例{i}" for i in range(1, 20)])
        terms = extract_precise_terms(long_query, max_terms=5)
        self.assertLessEqual(len(terms), 5)


class TestReciprocalRankFusion(unittest.TestCase):
    """Verify RRF combines multiple ranked lists."""

    def test_basic_fusion(self):
        # Channel 1: [A, B, C], Channel 2: [B, A, D]
        result = reciprocal_rank_fusion([[1, 2, 3], [2, 1, 4]])
        ids = [r[0] for r in result]
        # ID 1 and 2 appear in both channels → should rank higher
        self.assertEqual(ids[0], 1)  # rank 0 in ch1 + rank 1 in ch2
        self.assertEqual(ids[1], 2)  # rank 1 in ch1 + rank 0 in ch2
        # Scores are descending
        scores = [r[1] for r in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_single_channel(self):
        result = reciprocal_rank_fusion([[10, 20, 30]])
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], 10)  # best rank

    def test_empty_lists(self):
        self.assertEqual(reciprocal_rank_fusion([]), [])
        self.assertEqual(reciprocal_rank_fusion([[]]), [])

    def test_weighted_fusion(self):
        # Weight channel 2 more heavily
        result = reciprocal_rank_fusion([[1, 2], [2, 1]], weights=[0.5, 2.0])
        # ID 2 is rank 0 in channel 2 (weight 2.0) → should win
        self.assertEqual(result[0][0], 2)

    def test_none_ids_skipped(self):
        result = reciprocal_rank_fusion([[1, None, 3], [None, 1]])
        ids = [r[0] for r in result]
        self.assertNotIn(None, ids)
        self.assertIn(1, ids)
        self.assertIn(3, ids)


if __name__ == "__main__":
    unittest.main()

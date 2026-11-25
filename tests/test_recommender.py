import unittest

from recommendation import recommend
from recommendation.recommender import feature_score
from recommendation.sample_data import COURSES, STUDENT


class RecommenderTests(unittest.TestCase):
    def test_feature_conversion(self):
        cases = [
            ({"status": "absent"}, 0),
            ({"status": "present", "frequency": "low"}, 25),
            ({"status": "present", "frequency": "medium"}, 50),
            ({"status": "present", "frequency": "high"}, 100),
            ({"status": "unknown", "frequency": "high"}, None),
            ({"status": "present", "frequency": "unknown"}, None),
            ({"status": "present", "frequency": None}, None),
            ({"status": "present"}, None),
        ]
        for feature, expected in cases:
            with self.subTest(feature=feature):
                self.assertEqual(feature_score(feature), expected)

    def test_sample_score_rank_and_insufficient_data(self):
        result = recommend(STUDENT, courses=reversed(COURSES))
        good, poor = result["recommendations"]
        self.assertEqual((good["course_id"], good["rank"], good["match_score"]), ("A", 1, 100))
        self.assertEqual((poor["course_id"], poor["rank"]), ("B", 2))
        self.assertAlmostEqual(poor["match_score"], 150 / 7)
        self.assertEqual(good["data_coverage"], 1)
        self.assertEqual(len(good["recommendation_reason"]), 3)
        self.assertEqual(len(poor["cautions"]), 3)
        unknown, = result["insufficient_data"]
        self.assertEqual(unknown["course_id"], "C")
        self.assertIsNone(unknown["match_score"])
        self.assertIsNone(unknown["rank"])
        self.assertEqual(unknown["data_coverage"], 0)
        self.assertEqual(unknown["recommendation_reason"], [])
        self.assertEqual(unknown["cautions"], [])

    def test_weighted_score_and_coverage_exclude_unknowns(self):
        course = dict(COURSES[0], features={
            "presentation": {"status": "present", "frequency": "low"},
            "teamwork": {"status": "present", "frequency": "high"},
            "practice": {"status": "present", "frequency": None},
        })
        weights = {"presentation": 3, "teamwork": 2, "practice": 5}
        result, = recommend(STUDENT, weights, [course])["recommendations"]
        self.assertEqual(result["match_score"], 60)
        self.assertAlmostEqual(result["data_coverage"], 5 / 14)
        self.assertEqual(len(result["recommendation_reason"]), 1)
        self.assertEqual(len(result["cautions"]), 1)
        self.assertIn("팀 활동", result["cautions"][0])

    def test_known_features_with_zero_weight_are_excluded(self):
        weights = dict.fromkeys(STUDENT, 0)
        weights["exam"] = 1
        course = dict(COURSES[0], features={"teamwork": {"status": "absent"}})
        result, = recommend(STUDENT, weights, [course])["insufficient_data"]
        self.assertEqual(result["data_coverage"], 0)
        self.assertIsNone(result["match_score"])

    def test_reason_thresholds_and_weight_order(self):
        student = dict.fromkeys(STUDENT, 100)
        student["presentation"] = 80
        student["exam"] = 0
        course = dict(COURSES[0], features={
            "presentation": {"status": "present", "frequency": "high"},
            "practice": {"status": "present", "frequency": "high"},
            "teamwork": {"status": "present", "frequency": "medium"},
            "theory": {"status": "present", "frequency": "low"},
            "exam": {"status": "present", "frequency": "high"},
        })
        result, = recommend(student, {"practice": 2, "exam": 3}, [course])["recommendations"]
        self.assertEqual(
            [reason.split()[0] for reason in result["recommendation_reason"]], ["실습", "발표"]
        )
        self.assertEqual([caution.split()[0] for caution in result["cautions"]], ["시험", "이론"])

    def test_ties_use_coverage_then_course_id(self):
        partial = dict(COURSES[0], course_id="0", features={"exam": {"status": "absent"}})
        full = dict(COURSES[0], course_id="Z")
        result = recommend(STUDENT, None, [full, partial, COURSES[0]])
        self.assertEqual(
            [(course["course_id"], course["rank"]) for course in result["recommendations"]],
            [("A", 1), ("Z", 2), ("0", 3)],
        )

    def test_invalid_student_scores_and_weights(self):
        for value in (-1, 101, float("nan"), float("inf"), True, "50"):
            with self.subTest(student_score=value), self.assertRaises(ValueError):
                recommend(dict(STUDENT, exam=value), None, COURSES)
        with self.assertRaises(ValueError):
            recommend({}, None, COURSES)
        for weights in ({"exam": -1}, {"exam": float("inf")}, dict.fromkeys(STUDENT, 0)):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                recommend(STUDENT, weights, COURSES)

    def test_invalid_course_features(self):
        for feature in ({"status": "invalid"}, {"status": "present", "frequency": "rare"}):
            course = dict(COURSES[0], features={"exam": feature})
            with self.subTest(feature=feature), self.assertRaises(ValueError):
                recommend(STUDENT, None, [course])

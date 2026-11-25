"""Run the recommendation prototype with fictional courses."""

import json

from .recommender import FEATURE_LABELS, recommend


STUDENT = dict(zip(FEATURE_LABELS, (25, 0, 50, 0, 50, 25, 100)))


def _course(course_id, name, frequencies):
    features = {}
    for feature, frequency in zip(FEATURE_LABELS, frequencies):
        if frequency in ("absent", "unknown"):
            features[feature] = {"status": frequency}
        else:
            features[feature] = {"status": "present", "frequency": frequency}
    return {
        "course_id": course_id,
        "course_name": name,
        "professor_name": f"가상 교수 {course_id}",
        "features": features,
    }


COURSES = [
    _course("A", "실습 중심 교양", ("low", "absent", "medium", "absent", "medium", "low", "high")),
    _course("B", "발표와 시험 중심 교양", ("high", "high", "absent", "high", "absent", "high", "absent")),
    _course("C", "운영 정보 미확인 교양", ("unknown",) * len(FEATURE_LABELS)),
]


if __name__ == "__main__":
    print(json.dumps(recommend(STUDENT, None, COURSES), ensure_ascii=False, indent=2))

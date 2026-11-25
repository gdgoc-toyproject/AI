"""Compare student preferences with confirmed course characteristics."""

import math
from collections.abc import Mapping
from fractions import Fraction


FEATURE_LABELS = {
    "presentation": "발표",
    "teamwork": "팀 활동",
    "individual_assignment": "개인 과제",
    "exam": "시험",
    "communication": "소통",
    "theory": "이론",
    "practice": "실습",
}
FREQUENCY_SCORES = {"low": 25, "medium": 50, "high": 100}
FREQUENCY_LABELS = {"low": "낮음", "medium": "보통", "high": "높음"}


def _validate_number(value, name, maximum=math.inf):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0 <= value <= maximum
        or value == math.inf
    ):
        raise ValueError(f"Invalid value for {name}: {value!r}")


def _validate_features(values, name):
    if not isinstance(values, Mapping):
        raise ValueError(f"{name} must be a mapping")
    if values.keys() - FEATURE_LABELS.keys():
        raise ValueError(f"{name} contains an unrecognized feature")


def feature_score(feature):
    """Convert one simplified course feature to a score or None."""
    if not isinstance(feature, Mapping):
        raise ValueError("Each course feature must be a mapping")
    status = feature.get("status")
    if status == "unknown":
        return None
    if status == "absent":
        return 0
    if status != "present":
        raise ValueError(f"Invalid course feature status: {status!r}")

    frequency = feature.get("frequency")
    if frequency is None or frequency == "unknown":
        return None
    if not isinstance(frequency, str) or frequency not in FREQUENCY_SCORES:
        raise ValueError(f"Invalid course feature frequency: {frequency!r}")
    return FREQUENCY_SCORES[frequency]


def convert_course_features(features):
    """Adapt the simplified course JSON to scores and confirmed descriptions."""
    _validate_features(features, "course features")
    confirmed = {}
    for name in FEATURE_LABELS:
        if name not in features:
            continue
        feature = features[name]
        score = feature_score(feature)
        if score is None:
            continue
        description = (
            "없음" if score == 0 else FREQUENCY_LABELS[feature["frequency"]]
        )
        confirmed[name] = (score, description)
    return confirmed


def recommend(student, weights=None, courses=()):
    """Return ranked courses and courses that have no comparable weight."""
    _validate_features(student, "student")
    if student.keys() != FEATURE_LABELS.keys():
        raise ValueError("Student scores must include all seven features")
    for name, value in student.items():
        _validate_number(value, f"student.{name}", 100)

    weights = {} if weights is None else weights
    _validate_features(weights, "weights")
    weights = {name: weights.get(name, 1) for name in FEATURE_LABELS}
    for name, value in weights.items():
        _validate_number(value, f"weights.{name}")
    # Keep score and coverage comparisons exact until ranks have been assigned.
    weights = {name: Fraction(value) for name, value in weights.items()}
    total_weight = sum(weights.values())
    if total_weight == 0:
        raise ValueError("At least one weight must be positive")
    student = {name: Fraction(value) for name, value in student.items()}

    recommendations = []
    insufficient_data = []
    for course in courses:
        if not isinstance(course, Mapping):
            raise ValueError("Each course must be a mapping")
        try:
            result = {
                field: course[field]
                for field in ("course_id", "course_name", "professor_name")
            }
            confirmed = convert_course_features(course["features"])
        except KeyError as error:
            raise ValueError(f"Missing course field: {error.args[0]}") from error

        course_id = result["course_id"]
        if isinstance(course_id, bool) or not isinstance(course_id, (int, str)):
            raise ValueError("course_id must be an integer or a string")
        compared = [
            (name, 100 - abs(student[name] - score), description)
            for name, (score, description) in confirmed.items()
            if weights[name] > 0
        ]
        comparable_weight = sum(weights[name] for name, _, _ in compared)
        result.update(
            match_score=None,
            rank=None,
            recommendation_reason=[],
            cautions=[],
            data_coverage=0.0,
        )
        if not compared:
            insufficient_data.append(result)
            continue

        result["match_score"] = sum(
            fit * weights[name] for name, fit, _ in compared
        ) / comparable_weight
        result["data_coverage"] = comparable_weight / total_weight

        # Stable sorting preserves feature order for equal weights.
        compared.sort(key=lambda item: weights[item[0]], reverse=True)
        result["recommendation_reason"] = [
            f"{FEATURE_LABELS[name]} 특성({description})이 학생 성향과 잘 맞습니다."
            for name, fit, description in compared
            if fit >= 80
        ][:3]
        result["cautions"] = [
            f"{FEATURE_LABELS[name]} 특성({description})이 학생 성향과 차이가 큽니다."
            for name, fit, description in compared
            if fit < 50
        ][:3]
        recommendations.append(result)

    recommendations.sort(
        key=lambda item: (
            -item["match_score"],
            -item["data_coverage"],
            isinstance(item["course_id"], str),
            item["course_id"],
        )
    )
    for rank, result in enumerate(recommendations, start=1):
        result["rank"] = rank
        result["match_score"] = float(result["match_score"])
        result["data_coverage"] = float(result["data_coverage"])
    return {"recommendations": recommendations, "insufficient_data": insufficient_data}

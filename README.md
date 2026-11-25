# AI
강의평 분석 및 개인 맞춤형 교양 추천 알고리즘 개발

## 추천 프로토타입 실행

```powershell
python -m recommendation.sample_data
python -m unittest discover -s tests -v
```

`recommend(student, weights, courses)`는 학생의 7개 성향 점수(0~100)와 강의 특성을 비교합니다.
`weights`를 생략하거나 `None`을 전달하면 모든 항목에 가중치 1을 적용합니다.
일부 가중치만 지정하면 생략된 항목은 1이며, 0은 해당 항목을 비교에서 제외합니다.
음수 가중치와 모든 가중치가 0인 입력은 `ValueError`로 처리합니다.

강의 입력은 `course_id`, `course_name`, `professor_name`, `features`를 포함합니다.
`features`에는 성향 변수별로 `{"status": "present", "frequency": "low"}` 같은 값을 넣습니다.
누락되거나 확인되지 않은 특성은 계산에서 제외합니다. `data_coverage`는 0~1 비율입니다.
실제 리뷰 분석 JSON을 연동할 때는 강의별 특성을 집계한 뒤
`convert_course_features`가 받는 형식으로 변환하면 됩니다.

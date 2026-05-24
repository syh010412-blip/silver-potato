"""Claude AI로 구글 캘린더(계획) vs Notion Inbox(실행) 비교 분석."""
import json

import anthropic

from config import ANTHROPIC_API_KEY, DAY_NAMES, DAILY_HABITS, TIME_ZONES, GRADE_THRESHOLDS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """당신은 개인 생산성 코치입니다.
사용자의 구글 캘린더(계획)와 노션 Inbox(실행 캡처)를 비교 분석하여 데이터 기반 인사이트를 제공합니다.
반드시 유효한 JSON만 출력하세요. 마크다운 코드블록 없이.
~해요/~합니다 말투를 사용하세요. 감정적 격려보다 데이터 기반 구체적 조언을 우선합니다.
"""

_HABIT_LIST = ', '.join(DAILY_HABITS)
_GRADE_DESC = ' / '.join(f'{g}={t}%이상' for g, t in GRADE_THRESHOLDS.items())
_TZ_DESC = ', '.join(f'{name}({s}~{e}시)' for name, (s, e) in TIME_ZONES.items() if name != '심야')


def _build_prompt(week: dict, cal_by_date: dict, inbox_items: list[dict], inbox_summary: dict) -> str:
    monday, sunday = week['monday'], week['sunday']

    # 캘린더 이벤트 목록
    cal_lines = []
    total_cal = 0
    for d in week['dates']:
        events = cal_by_date.get(d, [])
        total_cal += len(events)
        day_name = DAY_NAMES[week['dates'].index(d)]
        for ev in events:
            time_str = '종일' if ev['is_all_day'] else f'{ev["start"][11:16]}~{ev["end"][11:16]}'
            cal_lines.append(f'  {d}({day_name}) {time_str} | {ev["title"]} [{ev["calendar"]}]')
    cal_section = '\n'.join(cal_lines) if cal_lines else '  (이벤트 없음)'

    # Inbox 항목 목록
    inbox_lines = []
    for item in inbox_items:
        proc = '✅ 처리완료' if item['processed'] else '⏳ 미처리'
        memo_str = f' / 메모: {item["memo"]}' if item['memo'] else ''
        body_str = f' / 본문: {item["body"]}' if item.get('body') else ''
        inbox_lines.append(
            f'  {item["date"]} {item["time"]} | {item["title"]}{memo_str}{body_str} | {proc} | 출처: {item["source"] or "기타"}'
        )
    inbox_section = '\n'.join(inbox_lines) if inbox_lines else '  (항목 없음)'

    return f"""아래 데이터를 분석하여 JSON으로 출력하세요.

## 분析 기간
{monday} (월) ~ {sunday} (일)

## 구글 캘린더 일정 (계획, 총 {total_cal}건)
{cal_section}

## Notion Inbox 항목 (캡처/실행, 총 {inbox_summary['total']}건)
- 처리 완료: {inbox_summary['processed']}건 ({inbox_summary['process_rate']}%)
- 미처리: {inbox_summary['unprocessed']}건
- 출처별: {json.dumps(inbox_summary['by_source'], ensure_ascii=False)}
{inbox_section}

## 분析 지침

### 계획 vs 실행
- 캘린더 이벤트(계획)와 Inbox 항목(실행 캡처) 간의 연관성을 찾아 비교하세요.
- 연관성 기준: 제목·키워드 유사성, 같은 날 비슷한 시간대 등.
- Inbox는 GTD 수집함으로, 반드시 캘린더와 1:1 매칭이 아닐 수 있어요.
- 생활형 루틴(식사·취침·재활치료 등)은 Inbox 캡처 대상이 아닐 수 있어요.
  "기록 없음 ≠ 실행 안 함"으로 해석하세요.

### 고정 습관 추적
추적할 습관 목록: {_HABIT_LIST}
캘린더 이벤트 또는 Inbox 항목에서 각 습관의 달성 여부를 날짜별로 확인하세요.
습관명이 정확히 일치하지 않아도 유사 표현(예: "운동", "gym" → "헬스")을 인식하세요.

### 시간대 집중도 분석
시간대 구간: {_TZ_DESC}
어느 시간대에 캘린더 일정이 집중되어 있는지, 어느 시간대에 Inbox 캡처가 많은지 파악하세요.
캘린더 계획이 없는 긴 공백(1시간+)이 있는지 확인하세요 (단, 활동 시간 09:00~23:00 기준).

### 등급 기준 (Inbox 처리율 기반)
{_GRADE_DESC}
이 기준으로 주간 등급(A~F)을 부여하고, 판정 근거를 간략히 설명하세요.

### 분析 관점
- 하루에 계획 대비 실행을 잘했는지 객관적으로 점검
- 어떤 시간대에 집중력이 좋은지/안 좋은지 파악
- 고정 습관을 언제 하면 좋을지 파악 (아침 vs 저녁 등)
- 다음에 어떻게 하면 더 나은 실행이 가능한지 구체적 행동 지침 제시
- 못함/미처리 항목이 특정 시간대에 몰려있는지 패턴 확인

## 출력 JSON 형식
{{
  "grade": "A|B|C|D|F",
  "grade_reason": "등급 판정 근거 (1문장)",
  "weekly_overview": "주간 총평 (2~3문장, 캘린더 계획 대비 Inbox 실행 현황 중심)",
  "plan_vs_execution": {{
    "executed_as_planned": [
      {{"calendar_event": "캘린더 이벤트명", "inbox_item": "매칭된 Inbox 항목명", "date": "YYYY-MM-DD", "note": "연관성 설명"}}
    ],
    "unplanned_captures": [
      {{"inbox_item": "Inbox 항목명", "date": "YYYY-MM-DD", "processed": true, "insight": "이 캡처의 의미"}}
    ],
    "planned_not_captured": [
      {{"calendar_event": "캘린더 이벤트명", "date": "YYYY-MM-DD", "reason": "미캡처 가능 이유"}}
    ]
  }},
  "metrics": {{
    "total_calendar_events": {total_cal},
    "total_inbox_items": {inbox_summary['total']},
    "inbox_process_rate": {inbox_summary['process_rate']},
    "calendar_capture_rate": 0,
    "capture_rate_note": "캘린더 이벤트 중 Inbox에 캡처된 비율 (생활루틴 제외 기준)"
  }},
  "habits": [
    {{
      "habit": "습관명",
      "days_completed": ["YYYY-MM-DD"],
      "completion_rate": 0,
      "evidence": "근거가 된 캘린더/Inbox 항목 요약",
      "best_time": "이 습관을 주로 한 시간대 (또는 추천 시간대)"
    }}
  ],
  "time_analysis": {{
    "most_active_zone": "가장 활동이 많은 시간대",
    "focus_pattern": "집중 패턴 설명 (1~2문장)",
    "gap_warning": "긴 공백이 발견된 경우 설명, 없으면 null"
  }},
  "insights": [
    "인사이트 1 (구체적 데이터 기반 관찰)",
    "인사이트 2",
    "인사이트 3"
  ],
  "patterns": {{
    "strong_points": "잘 하고 있는 점",
    "weak_points": "개선이 필요한 점",
    "inbox_health": "Inbox 처리 상태 평가 (캡처율·처리율·패턴)"
  }},
  "next_week_suggestions": [
    "구체적 행동 제안 1",
    "구체적 행동 제안 2",
    "구체적 행동 제안 3",
    "구체적 행동 제안 4",
    "구체적 행동 제안 5"
  ]
}}"""


def analyze(week: dict, cal_by_date: dict, inbox_items: list[dict], inbox_summary: dict) -> dict:
    print('[AI 분析] Claude에 분析 요청 중...')
    prompt = _build_prompt(week, cal_by_date, inbox_items, inbox_summary)

    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': prompt}],
    )

    raw = message.content[0].text.strip()
    raw = raw.removeprefix('```json').removeprefix('```').removesuffix('```').strip()
    s, e = raw.find('{'), raw.rfind('}')
    if s != -1 and e != -1:
        raw = raw[s:e + 1]

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f'[AI 분析] JSON 파싱 실패 ({exc}), 원본 앞 500자:\n{raw[:500]}')
        result = json.loads(raw.replace('\x00', '').replace('\r', ''))

    print('[AI 분析] 완료')
    return result

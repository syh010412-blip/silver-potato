"""Claude AI로 구글 캘린더(계획) vs Notion Inbox(실행) 비교 분석."""
import json

import anthropic

from config import ANTHROPIC_API_KEY, DAY_NAMES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """당신은 개인 생산성 코치입니다.
사용자의 구글 캘린더(계획)와 노션 Inbox(실행 캡처)를 비교 분석하여 인사이트를 제공합니다.
반드시 유효한 JSON만 출력하세요. 마크다운 코드블록 없이.
한국어로 응답하세요. 구체적이고 실행 가능한 조언 위주로 작성하세요.
"""


def _build_diary_section(diary_items: list[dict]) -> str:
    if not diary_items:
        return '## 일기\n  (이번 주 일기 없음)\n'
    lines = ['## 일기 (Comment 필드 기준)']
    for item in diary_items:
        lines.append(f'  {item["date"]} [{item["title"]}]')
        if item['comment']:
            lines.append(f'    {item["comment"]}')
    return '\n'.join(lines)


def _build_prompt(week: dict, cal_by_date: dict, inbox_items: list[dict], inbox_summary: dict,
                  diary_items: list[dict] | None = None) -> str:
    monday, sunday = week['monday'], week['sunday']

    # 캘린더 이벤트 목록 텍스트
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

    # Inbox 항목 목록 텍스트
    inbox_lines = []
    for item in inbox_items:
        proc = '✅ 처리완료' if item['processed'] else '⏳ 미처리'
        memo_str = f' / 메모: {item["memo"]}' if item['memo'] else ''
        body_str = f' / 본문: {item["body"]}' if item.get('body') else ''
        inbox_lines.append(
            f'  {item["date"]} {item["time"]} | {item["title"]}{memo_str}{body_str} | {proc} | 출처: {item["source"] or "기타"}'
        )
    inbox_section = '\n'.join(inbox_lines) if inbox_lines else '  (항목 없음)'

    diary_section = _build_diary_section(diary_items or [])
    has_diary = bool(diary_items)

    diary_output_schema = '''
  "diary_analysis": {
    "total_entries": 0,
    "recording_rate": "X일 기록 (7일 중)",
    "overall_sentiment": "전체 감정 총평 (2~3문장, 따뜻하고 공감 어린 톤으로)",
    "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
    "emotional_patterns": {
      "positive": "긍정 감정이 올라오는 상황 패턴",
      "negative": "부정 감정이 생기는 상황 패턴"
    },
    "day_sentiments": [
      {"date": "YYYY-MM-DD", "sentiment": "positive|negative|neutral", "emoji": "🟢|🔴|⬜", "preview": "일기 첫 40자 미리보기"}
    ],
    "topics": [
      {"name": "주제명", "count": 0}
    ],
    "frequent_words": ["단어1", "단어2", "단어3"],
    "growth_points": {
      "strengths": "잘 하고 있는 점 (구체적으로)",
      "improvements": "개선 포인트 (부드럽게)"
    },
    "self_care_suggestions": [
      "자기돌봄 제안 1",
      "자기돌봄 제안 2",
      "자기돌봄 제안 3"
    ]
  },''' if has_diary else '''
  "diary_analysis": null,'''

    return f"""아래 데이터를 분석하여 JSON으로 출력하세요.

## 분석 기간
{monday} (월) ~ {sunday} (일)

## 구글 캘린더 일정 (계획, 총 {total_cal}건)
{cal_section}

## Notion Inbox 항목 (캡처/실행, 총 {inbox_summary['total']}건)
- 처리 완료: {inbox_summary['processed']}건 ({inbox_summary['process_rate']}%)
- 미처리: {inbox_summary['unprocessed']}건
- 출처별: {json.dumps(inbox_summary['by_source'], ensure_ascii=False)}
{inbox_section}

{diary_section}

## 분석 지침
- 캘린더 이벤트(계획)와 Inbox 항목(실행 캡처) 간의 연관성을 찾아 비교하세요.
- 연관성 기준: 제목·키워드 유사성, 같은 날 비슷한 시간대 등.
- Inbox는 GTD 수집함으로, 반드시 캘린더와 1:1 매칭이 아닐 수 있습니다.
- 생활형 루틴(식사·취침·재활치료 등)은 Inbox 캡처 대상이 아닐 수 있으므로
  "기록 없음 ≠ 실행 안 함"으로 해석하세요.
- 주간 총평은 2~3문장, 일별 인사이트는 각 1문장으로 작성하세요.
- 일기 분석 시 감정을 판단하되 공감 어린 톤을 유지하세요. 한 단어로 positive/negative/neutral 분류.

## 출력 JSON 형식
{{
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
  "insights": [
    "인사이트 1 (구체적인 관찰)",
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
  ]{diary_output_schema}
}}"""


def analyze(week: dict, cal_by_date: dict, inbox_items: list[dict], inbox_summary: dict,
            diary_items: list[dict] | None = None) -> dict:
    print('[AI 분석] Claude에 분석 요청 중...')
    prompt = _build_prompt(week, cal_by_date, inbox_items, inbox_summary, diary_items)

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
        print(f'[AI 분석] JSON 파싱 실패 ({exc}), 원본 앞 500자:\n{raw[:500]}')
        result = json.loads(raw.replace('\x00', '').replace('\r', ''))

    print('[AI 분석] 완료')
    return result

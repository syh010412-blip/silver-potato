"""Habit Tracker DB에서 주간 습관 기록을 읽어오는 모듈."""
import requests

from config import NOTION_API_KEY, HABIT_DB_ID

_HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}
_BASE = 'https://api.notion.com/v1'

HABIT_FIELDS = [
    '⏰ 4:00 기상',
    '🙆‍♀️ 스트레칭',
    '🚽 세안',
    '🧘‍♀️ 명상',
    '💊 영양제 섭취',
    '💡 GTD Memo',
    '💪🏻 운동',
    '💸 경제신문',
    '📖 독서',
    '📝 일기 쓰기',
    '𝐍 노션 정리',
]


def _req(path: str, method: str = 'GET', body: dict | None = None) -> dict:
    url = f'{_BASE}/{path}'
    resp = requests.request(method, url, headers=_HEADERS, json=body or None, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _parse_page(page: dict) -> dict:
    props = page['properties']

    def checkbox(key: str) -> bool:
        return bool((props.get(key) or {}).get('checkbox', False))

    def text(key: str) -> str:
        return ''.join(t['plain_text'] for t in (props.get(key) or {}).get('rich_text', []))

    date_val = ((props.get('Date') or {}).get('date') or {}).get('start', '')
    habits = {h: checkbox(h) for h in HABIT_FIELDS}

    return {
        'date': date_val,
        'wake_up': text('Wake Up'),
        'in_bed': text('In Bed'),
        'habits': habits,
        'completed': sum(1 for v in habits.values() if v),
        'total': len(HABIT_FIELDS),
    }


def get_habits_for_week(monday: str, sunday: str) -> list[dict]:
    """월~일 기간의 습관 기록 반환."""
    results = []
    cursor = None
    while True:
        body: dict = {
            'filter': {
                'and': [
                    {'property': 'Date', 'date': {'on_or_after': monday}},
                    {'property': 'Date', 'date': {'on_or_before': sunday}},
                ]
            },
            'sorts': [{'property': 'Date', 'direction': 'ascending'}],
            'page_size': 100,
        }
        if cursor:
            body['start_cursor'] = cursor
        res = _req(f'databases/{HABIT_DB_ID}/query', 'POST', body)
        results.extend(res['results'])
        if res.get('has_more'):
            cursor = res['next_cursor']
        else:
            break

    items = [_parse_page(p) for p in results]
    print(f'[Habit] {len(items)}건 ({monday} ~ {sunday})')
    return items


def summarize_habits(items: list[dict]) -> dict:
    if not items:
        return {
            'total_days': 0,
            'avg_completion_rate': 0,
            'habit_completion': {h: {'count': 0, 'rate': 0} for h in HABIT_FIELDS},
        }

    habit_completion = {}
    for h in HABIT_FIELDS:
        count = sum(1 for item in items if item['habits'].get(h, False))
        habit_completion[h] = {
            'count': count,
            'rate': round(count / len(items) * 100),
        }

    avg_rate = round(
        sum(item['completed'] / item['total'] * 100 for item in items) / len(items)
    )

    return {
        'total_days': len(items),
        'avg_completion_rate': avg_rate,
        'habit_completion': habit_completion,
    }

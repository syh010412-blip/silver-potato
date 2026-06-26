"""DIARY DB에서 주간 일기 기록을 읽어오는 모듈."""
import requests

from config import NOTION_API_KEY, DIARY_DB_ID

_HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}
_BASE = 'https://api.notion.com/v1'


def _req(path: str, method: str = 'GET', body: dict | None = None) -> dict:
    url = f'{_BASE}/{path}'
    resp = requests.request(method, url, headers=_HEADERS, json=body or None, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _get_page_text(page_id: str) -> str:
    """페이지 본문 블록을 텍스트로 추출."""
    lines = []
    cursor = None
    while True:
        path = f'blocks/{page_id}/children?page_size=100'
        if cursor:
            path += f'&start_cursor={cursor}'
        res = _req(path)
        for block in res['results']:
            bt = block['type']
            rt = block.get(bt, {}).get('rich_text', [])
            text = ''.join(t['plain_text'] for t in rt)
            if text:
                lines.append(text)
        if res.get('has_more'):
            cursor = res['next_cursor']
        else:
            break
    return '\n'.join(lines)


def _parse_page(page: dict) -> dict:
    props = page['properties']
    comment = ''.join(
        t['plain_text'] for t in (props.get('Comment') or {}).get('rich_text', [])
    )
    date_val = ((props.get('Date') or {}).get('date') or {}).get('start', '')
    title = ''.join(t['plain_text'] for t in (props.get('Title') or {}).get('title', []))
    return {
        'page_id': page['id'],
        'date': date_val,
        'title': title,
        'comment': comment,
    }


def get_diary_for_week(monday: str, sunday: str) -> list[dict]:
    """월~일 기간의 일기 기록 반환."""
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
        res = _req(f'databases/{DIARY_DB_ID}/query', 'POST', body)
        results.extend(res['results'])
        if res.get('has_more'):
            cursor = res['next_cursor']
        else:
            break

    items = []
    for p in results:
        item = _parse_page(p)
        # Comment 필드가 비어있으면 페이지 본문에서 읽기
        if not item['comment']:
            item['comment'] = _get_page_text(item['page_id'])
        items.append(item)

    print(f'[Diary] {len(items)}건 ({monday} ~ {sunday})')
    return items

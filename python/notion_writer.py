"""AI 주간 리포트 DB에 분석 결과 페이지를 생성/업데이트하는 모듈.

AI 주간 리포트 DB 스키마:
  리포트 명  (title) - 페이지 제목
  분析 날짜  (date)  - 분석 기준 날짜
"""
from notion_client import Client

from config import NOTION_API_KEY, REPORT_DB_ID

notion = Client(auth=NOTION_API_KEY)

CHUNK_SIZE = 100


def _find_existing(title: str) -> str | None:
    res = notion.databases.query(
        database_id=REPORT_DB_ID,
        filter={'property': '리포트 명', 'title': {'equals': title}},
        page_size=1,
    )
    results = res.get('results', [])
    return results[0]['id'] if results else None


def _clear_blocks(page_id: str) -> None:
    cursor = None
    while True:
        kwargs: dict = {'block_id': page_id, 'page_size': 100}
        if cursor:
            kwargs['start_cursor'] = cursor
        res = notion.blocks.children.list(**kwargs)
        for block in res['results']:
            try:
                notion.blocks.delete(block_id=block['id'])
            except Exception:
                pass
        if res.get('has_more'):
            cursor = res['next_cursor']
        else:
            break


def _append_blocks(page_id: str, blocks: list[dict]) -> None:
    for i in range(0, len(blocks), CHUNK_SIZE):
        chunk = blocks[i:i + CHUNK_SIZE]
        notion.blocks.children.append(block_id=page_id, children=chunk)
        done = min(i + CHUNK_SIZE, len(blocks))
        print(f'[Notion] 블록 업로드: {done}/{len(blocks)}')


def upsert_report(title: str, blocks: list[dict], analysis_date: str) -> str:
    """리포트 페이지를 생성하거나 기존 페이지를 업데이트."""
    existing_id = _find_existing(title)

    if existing_id:
        print(f'[Notion] 기존 페이지 업데이트: "{title}"')
        notion.pages.update(
            page_id=existing_id,
            icon={'type': 'emoji', 'emoji': '📊'},
        )
        _clear_blocks(existing_id)
        _append_blocks(existing_id, blocks)
        print('[Notion] 업데이트 완료')
        return existing_id

    print(f'[Notion] 새 페이지 생성: "{title}"')
    page = notion.pages.create(
        parent={'database_id': REPORT_DB_ID},
        icon={'type': 'emoji', 'emoji': '📊'},
        properties={
            '리포트 명': {'title': [{'text': {'content': title}}]},
            '분析 날짜': {'date': {'start': analysis_date}},
        },
    )
    _append_blocks(page['id'], blocks)
    print('[Notion] 생성 완료')
    return page['id']

"""Notion 블록 빌더 모듈."""

# ── 리치텍스트 헬퍼 ──────────────────────────────────────────────

def rt(content: str, bold: bool = False, italic: bool = False,
       code: bool = False, color: str = 'default') -> dict:
    return {
        'type': 'text',
        'text': {'content': content, 'link': None},
        'annotations': {
            'bold': bold, 'italic': italic,
            'strikethrough': False, 'underline': False,
            'code': code, 'color': color,
        },
    }


# ── 블록 빌더 ────────────────────────────────────────────────────

def divider() -> dict:
    return {'object': 'block', 'type': 'divider', 'divider': {}}


def heading1(text: str) -> dict:
    return {
        'object': 'block', 'type': 'heading_1',
        'heading_1': {'rich_text': [rt(text)], 'is_toggleable': False},
    }


def heading2(text: str) -> dict:
    return {
        'object': 'block', 'type': 'heading_2',
        'heading_2': {'rich_text': [rt(text)], 'is_toggleable': False},
    }


def heading3(text: str) -> dict:
    return {
        'object': 'block', 'type': 'heading_3',
        'heading_3': {'rich_text': [rt(text)], 'is_toggleable': False},
    }


def callout(rich_texts: list | str, emoji: str = '📌', color: str = 'default') -> dict:
    if isinstance(rich_texts, str):
        rich_texts = [rt(rich_texts)]
    return {
        'object': 'block', 'type': 'callout',
        'callout': {
            'rich_text': rich_texts,
            'icon': {'type': 'emoji', 'emoji': emoji},
            'color': color,
        },
    }


def bullet(rich_texts: list | str) -> dict:
    if isinstance(rich_texts, str):
        rich_texts = [rt(rich_texts)]
    return {
        'object': 'block', 'type': 'bulleted_list_item',
        'bulleted_list_item': {'rich_text': rich_texts},
    }


def numbered(rich_texts: list | str) -> dict:
    if isinstance(rich_texts, str):
        rich_texts = [rt(rich_texts)]
    return {
        'object': 'block', 'type': 'numbered_list_item',
        'numbered_list_item': {'rich_text': rich_texts},
    }


def paragraph(rich_texts: list | str) -> dict:
    if isinstance(rich_texts, str):
        rich_texts = [rt(rich_texts)]
    return {
        'object': 'block', 'type': 'paragraph',
        'paragraph': {'rich_text': rich_texts},
    }


def table(headers: list[str], rows: list[list[str]]) -> dict:
    header_row = {
        'object': 'block', 'type': 'table_row',
        'table_row': {'cells': [[rt(h, bold=True)] for h in headers]},
    }
    data_rows = [
        {
            'object': 'block', 'type': 'table_row',
            'table_row': {'cells': [[rt(str(cell))] for cell in row]},
        }
        for row in rows
    ]
    return {
        'object': 'block', 'type': 'table',
        'table': {
            'table_width': len(headers),
            'has_column_header': True,
            'has_row_header': False,
            'children': [header_row, *data_rows],
        },
    }


def toggle_heading2(text: str, children: list[dict]) -> dict:
    return {
        'object': 'block', 'type': 'heading_2',
        'heading_2': {
            'rich_text': [rt(text)],
            'is_toggleable': True,
            'children': children,
        },
    }


# ── 등급 이모지 헬퍼 ────────────────────────────────────────────

_GRADE_EMOJI = {'A': '🏆', 'B': '🥈', 'C': '🥉', 'D': '⚠️', 'F': '🔴'}
_GRADE_COLOR = {'A': 'green_background', 'B': 'blue_background', 'C': 'yellow_background', 'D': 'orange_background', 'F': 'red_background'}


# ── 메인 리포트 빌더 ─────────────────────────────────────────────

def build_report_blocks(
    week: dict,
    cal_by_date: dict,
    inbox_items: list[dict],
    inbox_summary: dict,
    analysis: dict,
) -> list[dict]:
    monday, sunday = week['monday'], week['sunday']
    blocks: list[dict] = []

    metrics = analysis.get('metrics', {})
    cal_total = metrics.get('total_calendar_events', 0)
    inbox_total = metrics.get('total_inbox_items', 0)
    inbox_rate = inbox_summary.get('process_rate', 0)
    grade = analysis.get('grade', '-')
    grade_emoji = _GRADE_EMOJI.get(grade, '📊')
    grade_color = _GRADE_COLOR.get(grade, 'blue_background')

    # ── 헤더 ──────────────────────────────────────────────────────
    blocks.append(callout(
        [
            rt(f'{monday} ~ {sunday}  주간 활동 분析 리포트\n', bold=True),
            rt(f'캘린더 일정 {cal_total}건  |  Inbox 캡처 {inbox_total}건  |  처리율 {inbox_rate}%'),
        ],
        '📊', 'blue_background',
    ))

    # 등급 callout
    grade_reason = analysis.get('grade_reason', '')
    blocks.append(callout(
        [
            rt(f'주간 등급: {grade}  {grade_emoji}\n', bold=True),
            rt(grade_reason),
        ],
        grade_emoji, grade_color,
    ))
    blocks.append(divider())

    # ── 주간 요약 ─────────────────────────────────────────────────
    blocks.append(heading1('📋 주간 요약'))
    overview = analysis.get('weekly_overview', '')
    if overview:
        blocks.append(callout(overview, '💬', 'gray_background'))

    # 수치 요약 테이블
    blocks.append(table(
        ['항목', '수치'],
        [
            ['캘린더 일정 수', f'{cal_total}개'],
            ['Inbox 총 항목', f'{inbox_total}개'],
            ['→ 처리 완료', f'{inbox_summary["processed"]}개'],
            ['→ 미처리', f'{inbox_summary["unprocessed"]}개'],
            ['Inbox 처리율', f'{inbox_rate}%'],
            ['캘린더 캡처율', metrics.get('capture_rate_note', '-')],
        ],
    ))
    blocks.append(divider())

    # ── 계획 vs 실행 ──────────────────────────────────────────────
    blocks.append(heading1('📅 계획 vs 실행 分析'))

    pve = analysis.get('plan_vs_execution', {})

    executed = pve.get('executed_as_planned', [])
    blocks.append(heading2(f'✅ 계획대로 실행된 것 ({len(executed)}건)'))
    if executed:
        rows = [[e.get('date', ''), e.get('calendar_event', ''), e.get('inbox_item', ''), e.get('note', '')] for e in executed]
        blocks.append(table(['날짜', '캘린더(계획)', 'Inbox(실행)', '연관성'], rows))
    else:
        blocks.append(paragraph([rt('직접 매칭되는 항목이 없거나 확인 불가해요.', color='gray')]))

    unplanned = pve.get('unplanned_captures', [])
    blocks.append(heading2(f'🆕 계획에 없었지만 캡처된 것 ({len(unplanned)}건)'))
    if unplanned:
        rows = [
            [u.get('date', ''), u.get('inbox_item', ''),
             '✅ 처리완료' if u.get('processed') else '⏳ 미처리',
             u.get('insight', '')]
            for u in unplanned
        ]
        blocks.append(table(['날짜', 'Inbox 항목', '상태', '의미'], rows))
    else:
        blocks.append(paragraph([rt('캘린더 외 별도 캡처 없어요.', color='gray')]))

    not_captured = pve.get('planned_not_captured', [])
    blocks.append(heading2(f'❌ 계획했지만 캡처되지 않은 것 ({len(not_captured)}건)'))
    if not_captured:
        rows = [[n.get('date', ''), n.get('calendar_event', ''), n.get('reason', '')] for n in not_captured]
        blocks.append(table(['날짜', '캘린더 이벤트', '미캡처 이유'], rows))
    else:
        blocks.append(paragraph([rt('없어요.', color='gray')]))

    blocks.append(divider())

    # ── 습관 추적 ─────────────────────────────────────────────────
    habits = analysis.get('habits', [])
    if habits:
        blocks.append(heading1('🏃 고정 습관 추적'))
        habit_rows = []
        for h in habits:
            days_done = len(h.get('days_completed', []))
            rate = h.get('completion_rate', 0)
            bar = '■' * round(rate / 10) + '□' * (10 - round(rate / 10))
            best_time = h.get('best_time', '-')
            habit_rows.append([
                h.get('habit', ''),
                f'{days_done}일 / 7일',
                f'{rate}%',
                bar,
                best_time,
            ])
        blocks.append(table(['습관', '달성', '달성률', '진행도', '적합 시간대'], habit_rows))

        # 습관별 달성 일자 (토글)
        habit_detail_children = []
        for h in habits:
            evidence = h.get('evidence', '')
            days = ', '.join(h.get('days_completed', [])) or '없음'
            habit_detail_children.append(bullet(
                [rt(f'{h.get("habit", "")}: ', bold=True), rt(f'{days}  |  근거: {evidence}')]
            ))
        blocks.append(toggle_heading2('📋 습관 달성 상세', habit_detail_children))
        blocks.append(divider())

    # ── 시간대 분析 ───────────────────────────────────────────────
    time_analysis = analysis.get('time_analysis', {})
    if time_analysis:
        blocks.append(heading1('⏰ 시간대 生産性 分析'))
        most_active = time_analysis.get('most_active_zone', '-')
        focus_pattern = time_analysis.get('focus_pattern', '')
        gap_warning = time_analysis.get('gap_warning')

        blocks.append(callout(
            [rt(f'가장 활동적인 시간대: {most_active}\n', bold=True), rt(focus_pattern)],
            '⏰', 'purple_background',
        ))
        if gap_warning:
            blocks.append(callout(gap_warning, '⚠️', 'orange_background'))
        blocks.append(divider())

    # ── Inbox 현황 ────────────────────────────────────────────────
    blocks.append(heading1('📥 Inbox 현황'))

    source_rows = [[src, str(cnt)] for src, cnt in inbox_summary.get('by_source', {}).items()]
    if source_rows:
        blocks.append(table(['출처', '건수'], source_rows))

    inbox_children: list[dict] = []
    if inbox_items:
        item_rows = [
            [
                item['date'], item['time'],
                item['title'],
                item['memo'][:40] + ('…' if len(item['memo']) > 40 else '') if item['memo'] else '',
                '✅' if item['processed'] else '⏳',
                item['source'] or '기타',
            ]
            for item in inbox_items
        ]
        inbox_children.append(table(['날짜', '시간', '제목', '메모', '처리', '출처'], item_rows))
    else:
        inbox_children.append(paragraph('이번 주 Inbox 항목 없음'))
    blocks.append(toggle_heading2(f'📋 Inbox 전체 목록 ({inbox_total}건)', inbox_children))
    blocks.append(divider())

    # ── 구글 캘린더 일정 요약 ─────────────────────────────────────
    blocks.append(heading1('📆 이번 주 구글 캘린더 일정'))
    from config import DAY_NAMES
    cal_children: list[dict] = []
    for i, d in enumerate(week['dates']):
        events = cal_by_date.get(d, [])
        day_name = DAY_NAMES[i]
        if events:
            day_rows = [
                ['종일' if ev['is_all_day'] else f'{ev["start"][11:16]}~{ev["end"][11:16]}', ev['title'], ev['calendar']]
                for ev in events
            ]
            cal_children.append(heading3(f'{day_name} {d} ({len(events)}건)'))
            cal_children.append(table(['시간', '이벤트', '캘린더'], day_rows))
        else:
            cal_children.append(bullet(f'{day_name} {d} — 일정 없어요'))
    blocks.append(toggle_heading2(f'📅 일별 캘린더 ({cal_total}건)', cal_children))
    blocks.append(divider())

    # ── 인사이트 & 패턴 ──────────────────────────────────────────
    blocks.append(heading1('💡 인사이트 & 패턴'))

    insights = analysis.get('insights', [])
    for insight in insights:
        blocks.append(bullet(insight))

    patterns = analysis.get('patterns', {})
    if patterns:
        if patterns.get('strong_points'):
            blocks.append(callout(
                [rt('잘 하고 있는 점\n', bold=True), rt(patterns['strong_points'])],
                '🟢', 'green_background',
            ))
        if patterns.get('weak_points'):
            blocks.append(callout(
                [rt('개선이 필요한 점\n', bold=True), rt(patterns['weak_points'])],
                '🔴', 'red_background',
            ))
        if patterns.get('inbox_health'):
            blocks.append(callout(
                [rt('Inbox 상태\n', bold=True), rt(patterns['inbox_health'])],
                '📥', 'yellow_background',
            ))

    blocks.append(divider())

    # ── 다음 주 제안 ──────────────────────────────────────────────
    blocks.append(heading1('🚀 다음 주 제안'))

    suggestions = analysis.get('next_week_suggestions', [])
    for sug in suggestions:
        blocks.append(numbered(sug))

    blocks.append(divider())
    blocks.append(callout('🤖 Claude AI가 자동 분析한 주간 리포트입니다.', '🤖', 'gray_background'))

    return blocks

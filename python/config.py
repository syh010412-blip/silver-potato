import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

# Notion
NOTION_API_KEY = os.getenv('NOTION_API_KEY', '')
INBOX_DB_ID = os.getenv('NOTION_INBOX_DB_ID') or '81c6e06c-3979-4922-a591-58dd1cd46b34'
REPORT_DB_ID = os.getenv('NOTION_REPORT_DB_ID') or '34da3bd9-3958-8007-82ee-efb717e2658f'

# Anthropic
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# Google Calendar
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
GOOGLE_TOKEN_PATH = os.getenv('GOOGLE_TOKEN_PATH', 'token.json')
_default_exclude = '대한민국의 휴일,미정'
CALENDAR_EXCLUDE = [x.strip() for x in os.getenv('CALENDAR_EXCLUDE', _default_exclude).split(',') if x.strip()]

# 분析 기준 (분析기준.txt 기반)
DAILY_HABITS = ['헬스', '쓰레드', '독서 10분', '신문 읽기', '일기쓰기']
GRADE_THRESHOLDS = {'A': 90, 'B': 75, 'C': 60, 'D': 40, 'F': 0}
TIME_ZONES = {
    '이른 아침': (6, 9),
    '오전': (9, 12),
    '오후 초반': (12, 15),
    '오후 후반': (15, 18),
    '저녁': (18, 21),
    '밤': (21, 24),
    '심야': (0, 6),
}
ACTIVITY_HOURS = (9, 23)


def get_kst_today() -> str:
    from datetime import timezone, datetime
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).strftime('%Y-%m-%d')


def get_week_range(today_str: str) -> dict:
    today = date.fromisoformat(today_str)
    day_of_week = today.weekday()
    monday = today - timedelta(days=day_of_week)
    dates = [str(monday + timedelta(days=i)) for i in range(7)]
    return {
        'monday': dates[0],
        'sunday': dates[6],
        'dates': dates,
    }


def get_grade(rate: float) -> str:
    for grade, threshold in GRADE_THRESHOLDS.items():
        if rate >= threshold:
            return grade
    return 'F'


DAY_NAMES = ['월', '화', '수', '목', '금', '토', '일']

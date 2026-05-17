"""분석기준.txt 파서 - 분석 설정 파일을 로드합니다."""
import os
import unicodedata


def _find_path() -> str | None:
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        for f in os.listdir(parent):
            if unicodedata.normalize('NFC', f) == '분석기준.txt':
                return os.path.join(parent, f)
    except OSError:
        pass
    return None


def _parse() -> dict[str, list[str]]:
    path = _find_path()
    if not path:
        return {}
    sections: dict[str, list[str]] = {}
    current: str | None = None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('[') and line.endswith(']'):
                    current = unicodedata.normalize('NFC', line[1:-1])
                    sections[current] = []
                elif current is not None:
                    sections[current].append(unicodedata.normalize('NFC', line))
    except OSError:
        pass
    return sections


_SECTIONS = _parse()


def _kv(section: str) -> dict[str, str]:
    result = {}
    for line in _SECTIONS.get(section, []):
        if '=' in line:
            k, _, v = line.partition('=')
            result[k.strip()] = v.strip()
    return result


def _lines(section: str) -> list[str]:
    return list(_SECTIONS.get(section, []))


def get_calendar_excludes() -> list[str]:
    raw = _kv('구글 캘린더').get('제외', '')
    return [x.strip() for x in raw.split(',') if x.strip()]


def get_habits() -> list[str]:
    habits: list[str] = []
    for line in _lines('습관 목록'):
        if '=' not in line:
            habits.extend(x.strip() for x in line.split(',') if x.strip())
    return habits


def get_analysis_perspectives() -> list[str]:
    return [ln for ln in _lines('분석 관점') if '=' not in ln]


def get_analysis_style() -> dict[str, str]:
    return _kv('분석 스타일')


def get_grade_criteria() -> list[tuple[str, int]]:
    """등급 기준 목록 (높은 순), (등급, 최소%)."""
    grades = []
    for grade, pct_str in _kv('등급 기준').items():
        try:
            grades.append((grade, int(pct_str)))
        except ValueError:
            pass
    return sorted(grades, key=lambda x: -x[1])

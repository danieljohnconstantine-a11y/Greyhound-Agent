import logging
import os
import re
import zipfile
from datetime import datetime
from xml.etree import ElementTree as ET

import pandas as pd


RESULT_COLUMNS = ['Track', 'Date', 'Race', 'RaceNumber', 'Winner', '2nd', '3rd', '4th']

_TRACK_ALIASES = {
    'ANGLE PARK': 'Angle Park',
    'BALLARAT': 'Ballarat',
    'BENDIGO': 'Bendigo',
    'BET NATION TOWNSVILLE': 'Townsville',
    'BETDELUXE CAPALABA': 'Capalaba',
    'BETDELUXE ROCKHAMPTON': 'Rockhampton',
    'BROKEN HILL': 'Broken Hill',
    'BULLI': 'Bulli',
    'CAPALABA': 'Capalaba',
    'CASINO': 'Casino',
    'DARWIN': 'Darwin',
    'GAWLER': 'Gawler',
    'GEELONG': 'Geelong',
    'GOSFORD': 'Gosford',
    'GRAFTON': 'Grafton',
    'GUNNEDAH': 'Gunnedah',
    'HEALESVILLE': 'Healesville',
    'HOBART': 'Hobart',
    'HORSHAM': 'Horsham',
    'LADBROKES Q1 LAKESIDE': 'Q Lakeside',
    'LADBROKES Q2 PARKLANDS': 'Q Parklands',
    'LADBROKES Q STRAIGHT': 'Q Straight',
    'MAITLAND': 'Maitland',
    'MANDURAH': 'Mandurah',
    'MEADOWS': 'Meadows',
    'MOUNT GAMBIER': 'Mount Gambier',
    'MT GAMBIER': 'Mount Gambier',
    'NOWRA': 'Nowra',
    'Q LAKESIDE': 'Q Lakeside',
    'Q PARKLANDS': 'Q Parklands',
    'Q STRAIGHT': 'Q Straight',
    'RICHMOND': 'Richmond',
    'RICHMOND STRAIGHT': 'Richmond',
    'ROCKHAMPTON': 'Rockhampton',
    'SALE': 'Sale',
    'SANDOWN': 'Sandown',
    'SANDOWN PARK': 'Sandown',
    'SHEPPARTON': 'Shepparton',
    'THE GARDENS': 'The Gardens',
    'THE MEADOWS': 'Meadows',
    'TOWNSVILLE': 'Townsville',
    'TRARALGON': 'Traralgon',
    'WARRAGUL': 'Warragul',
    'WARRNAMBOOL': 'Warrnambool',
    'WENTWORTH PARK': 'Wentworth Park',
}

_WORD_NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
_TRACK_DATE_RE = re.compile(r'^(?P<track>.+?)(?P<date>\d{1,2}/\d{1,2}/\d{4})$')
_TRACK_DATE_PREFIX_RE = re.compile(r'^(?P<track>.+?)(?P<date>\d{1,2}/\d{1,2}/\d{4})(?:\s+|$)')
_RACE_TOKEN_RE = re.compile(r'R(?P<race>\d+)(?P<tail>\d{4}|ABD)', re.IGNORECASE)
_RESULT_DATE_RE = re.compile(r'results_(\d{4}-\d{2}-\d{2})\.csv$', re.IGNORECASE)
_DOCX_DATE_RE = re.compile(r'(\d{2})(\d{2})(\d{4})results\.docx$', re.IGNORECASE)
_EXTRA_DATA_DIR_RE = re.compile(r'^data(?P<index>\d+)$', re.IGNORECASE)


def _source_priority(path):
    lower = path.lower()
    if lower.endswith('.csv'):
        return 0
    if lower.endswith('.docx'):
        return 1
    return 9


def discover_additional_data_dirs(data_dir='data'):
    """
    Discover sibling directories named ``data2``, ``data3``, ``data4`` ...
    and return them in numeric order.
    """
    base_dir = os.path.abspath(data_dir)
    parent_dir = os.path.dirname(base_dir)
    primary_name = os.path.basename(base_dir).lower()

    discovered = []
    if not os.path.isdir(parent_dir):
        return discovered

    for name in os.listdir(parent_dir):
        directory = os.path.join(parent_dir, name)
        if not os.path.isdir(directory):
            continue

        if name.lower() == primary_name:
            continue

        match = _EXTRA_DATA_DIR_RE.fullmatch(name)
        if not match:
            continue

        discovered.append((int(match.group('index')), directory))

    discovered.sort(key=lambda item: item[0])
    return [directory for _, directory in discovered]


def find_result_files(data_dir='data', include_output_docx=True, extra_dirs=None):
    """
    Return all supported result files for training.

    Supported patterns:
      - data/results_*.csv
      - data/results_*.docx
      - data/*RESULTS.docx
      - outputs/results_*.docx
      - outputs/*RESULTS.docx

    Args:
        data_dir: Primary directory to search for result files.
        include_output_docx: Also search the sibling ``outputs/`` directory.
        extra_dirs: Optional list of additional directories to include
            (e.g. ``['data2']``).  Files in these directories are merged and
            deduplicated with those from ``data_dir``.
    """
    data_dir = os.path.abspath(data_dir)
    search_dirs = [data_dir]

    if include_output_docx:
        outputs_dir = os.path.join(os.path.dirname(data_dir), 'outputs')
        if os.path.isdir(outputs_dir) and outputs_dir not in search_dirs:
            search_dirs.append(outputs_dir)

    if extra_dirs:
        for extra in extra_dirs:
            extra_abs = os.path.abspath(extra)
            if extra_abs not in search_dirs:
                search_dirs.append(extra_abs)

    auto_extra_dirs = discover_additional_data_dirs(data_dir)
    for auto_extra in auto_extra_dirs:
        if auto_extra not in search_dirs:
            search_dirs.append(auto_extra)

    result_files = []
    for directory in search_dirs:
        if not os.path.isdir(directory):
            continue

        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if not os.path.isfile(path):
                continue

            lower = name.lower()
            is_csv = lower.startswith('results_') and lower.endswith('.csv')
            is_docx = lower.endswith('.docx') and (
                lower.startswith('results_') or lower.endswith('results.docx')
            )

            if is_csv or is_docx:
                result_files.append(path)

    return sorted(set(result_files), key=lambda path: (_source_priority(path), path.lower()))


def load_results_dataframe(data_dir='data', include_output_docx=True, logger=None, extra_dirs=None):
    """
    Load results from CSV and DOCX files and normalize them to a shared schema.

    Args:
        data_dir: Primary directory containing result files.
        include_output_docx: Also search the sibling ``outputs/`` directory.
        logger: Optional logger instance.
        extra_dirs: Optional list of additional directories to include
            (e.g. ``['data2']``).
    """
    logger = logger or logging.getLogger(__name__)
    result_files = find_result_files(data_dir=data_dir, include_output_docx=include_output_docx, extra_dirs=extra_dirs)

    dataframes = []
    for result_file in result_files:
        try:
            if result_file.lower().endswith('.csv'):
                df = pd.read_csv(result_file)
            else:
                df = load_docx_results(result_file)

            normalized = normalize_results_dataframe(df, source_path=result_file)
            if normalized.empty:
                continue

            normalized['_source_file'] = result_file
            normalized['_source_format'] = os.path.splitext(result_file)[1].lower().lstrip('.')
            dataframes.append(normalized)
        except Exception as exc:
            logger.warning(f"Skipping unreadable results file {result_file}: {exc}")

    if not dataframes:
        return pd.DataFrame(columns=RESULT_COLUMNS + ['_source_file', '_source_format'])

    combined = pd.concat(dataframes, ignore_index=True)
    combined['_source_priority'] = combined['_source_format'].map({'csv': 0, 'docx': 1}).fillna(9)
    combined = combined.sort_values(
        by=['Date', 'Track', 'RaceNumber', '_source_priority', '_source_file'],
        kind='stable'
    )
    combined = combined.drop_duplicates(subset=['Date', 'Track', 'RaceNumber'], keep='first')
    combined = combined.drop(columns=['_source_priority'])
    return combined.reset_index(drop=True)


def normalize_results_dataframe(df, source_path=''):
    """
    Normalize heterogeneous result files to the standard training schema.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    normalized = df.copy()

    if 'Race' not in normalized.columns and 'RaceNumber' in normalized.columns:
        normalized['Race'] = normalized['RaceNumber']
    if 'RaceNumber' not in normalized.columns and 'Race' in normalized.columns:
        normalized['RaceNumber'] = normalized['Race']

    if 'Winner' not in normalized.columns:
        if 'Position1' in normalized.columns:
            normalized['Winner'] = normalized['Position1']
        elif 'WinnerBox' in normalized.columns:
            normalized['Winner'] = normalized['WinnerBox']

    if '2nd' not in normalized.columns and 'Position2' in normalized.columns:
        normalized['2nd'] = normalized['Position2']
    if '3rd' not in normalized.columns and 'Position3' in normalized.columns:
        normalized['3rd'] = normalized['Position3']
    if '4th' not in normalized.columns and 'Position4' in normalized.columns:
        normalized['4th'] = normalized['Position4']

    if 'Date' not in normalized.columns:
        inferred_date = _extract_date_from_filename(source_path)
        normalized['Date'] = inferred_date if inferred_date else ''

    for column in ['Track', 'Date', 'Race', 'RaceNumber', 'Winner', '2nd', '3rd', '4th']:
        if column not in normalized.columns:
            normalized[column] = None

    normalized['Track'] = normalized['Track'].apply(_normalize_track)
    normalized['Date'] = normalized['Date'].apply(
        lambda value: _normalize_date(value) or _extract_date_from_filename(source_path) or ''
    )
    normalized['RaceNumber'] = normalized['RaceNumber'].apply(_normalize_race_number)
    normalized['Race'] = normalized['Race'].apply(_normalize_race_number)
    normalized.loc[normalized['Race'].isna(), 'Race'] = normalized.loc[normalized['Race'].isna(), 'RaceNumber']
    normalized.loc[normalized['RaceNumber'].isna(), 'RaceNumber'] = normalized.loc[
        normalized['RaceNumber'].isna(), 'Race'
    ]

    normalized['Winner'] = normalized['Winner'].apply(_normalize_placing)
    normalized['2nd'] = normalized['2nd'].apply(_normalize_placing)
    normalized['3rd'] = normalized['3rd'].apply(_normalize_placing)
    normalized['4th'] = normalized['4th'].apply(_normalize_placing)

    normalized = normalized.dropna(subset=['Track', 'Date', 'RaceNumber'])
    normalized = normalized[normalized['Track'] != '']
    normalized = normalized[normalized['Date'] != '']
    normalized['Race'] = normalized['Race'].astype(int)
    normalized['RaceNumber'] = normalized['RaceNumber'].astype(int)
    return normalized[RESULT_COLUMNS].reset_index(drop=True)


def load_docx_results(path):
    """
    Parse Word result files that store one track per table row or paragraph line.
    """
    rows = []
    body = _read_docx_body(path)

    for child in list(body):
        tag = child.tag.rsplit('}', 1)[-1]

        if tag == 'tbl':
            for table_row in child.findall('./w:tr', _WORD_NS):
                cells = [_collect_text(cell) for cell in table_row.findall('./w:tc', _WORD_NS)]
                rows.extend(_parse_result_cells(cells))

        elif tag == 'p':
            paragraph = _collect_text(child)
            rows.extend(_parse_result_paragraph(paragraph))

    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def _read_docx_body(path):
    with zipfile.ZipFile(path) as docx_zip:
        document_xml = docx_zip.read('word/document.xml')

    root = ET.fromstring(document_xml)
    body = root.find('w:body', _WORD_NS)
    if body is None:
        raise ValueError("DOCX has no document body")
    return body


def _collect_text(node):
    return ''.join(text.text or '' for text in node.findall('.//w:t', _WORD_NS)).strip()


def _parse_result_cells(cells):
    cells = [cell.strip() for cell in cells if cell and cell.strip()]
    if not cells:
        return []

    track_date = _parse_track_date(cells[0])
    if not track_date:
        return []

    track, date = track_date
    rows = []
    for token in cells[1:]:
        parsed = _parse_race_token(token)
        if parsed:
            race_number, winner, second, third, fourth = parsed
            rows.append({
                'Track': track,
                'Date': date,
                'Race': race_number,
                'RaceNumber': race_number,
                'Winner': winner,
                '2nd': second,
                '3rd': third,
                '4th': fourth,
            })
    return rows


def _parse_result_paragraph(paragraph):
    paragraph = (paragraph or '').strip()
    if not paragraph:
        return []

    match = _TRACK_DATE_PREFIX_RE.match(paragraph)
    if not match:
        return []

    track = _normalize_track(match.group('track'))
    date = _normalize_date(match.group('date'))
    if not track or not date:
        return []

    rows = []
    remainder = paragraph[match.end():]
    for token_match in _RACE_TOKEN_RE.finditer(remainder):
        parsed = _parse_race_token(token_match.group(0))
        if parsed:
            race_number, winner, second, third, fourth = parsed
            rows.append({
                'Track': track,
                'Date': date,
                'Race': race_number,
                'RaceNumber': race_number,
                'Winner': winner,
                '2nd': second,
                '3rd': third,
                '4th': fourth,
            })
    return rows


def _parse_track_date(text):
    text = (text or '').strip()
    match = _TRACK_DATE_RE.match(text)
    if not match:
        return None

    track = _normalize_track(match.group('track'))
    date = _normalize_date(match.group('date'))
    if not track or not date:
        return None
    return track, date


def _parse_race_token(token):
    token = (token or '').strip()
    if not token:
        return None

    match = re.fullmatch(r'R(?P<race>\d+)(?P<tail>\d{4}|ABD)', token, re.IGNORECASE)
    if not match:
        return None

    race_number = int(match.group('race'))
    tail = match.group('tail').upper()
    if tail == 'ABD':
        return race_number, 'ABD', None, None, None

    return race_number, int(tail[0]), int(tail[1]), int(tail[2]), int(tail[3])


def _normalize_track(value):
    if value is None:
        return ''
    if isinstance(value, float) and pd.isna(value):
        return ''
    cleaned = re.sub(r'\s+', ' ', str(value)).strip()
    return _TRACK_ALIASES.get(cleaned.upper(), cleaned)


def _normalize_date(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    for date_format in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(text, date_format).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def _normalize_race_number(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    if text.upper().startswith('R'):
        text = text[1:]

    if text.isdigit():
        return int(text)

    digits = re.search(r'\d+', text)
    return int(digits.group()) if digits else None


def _normalize_placing(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None
    if text.upper() == 'ABD':
        return 'ABD'

    digits = re.search(r'\d+', text)
    return int(digits.group()) if digits else None


def _extract_date_from_filename(path):
    filename = os.path.basename(path or '')

    match = _RESULT_DATE_RE.search(filename)
    if match:
        return match.group(1)

    match = _DOCX_DATE_RE.search(filename)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"

    return None

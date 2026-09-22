"""Workbook consolidation independent of the web interface."""
from dataclasses import dataclass
from io import BytesIO
from openpyxl import Workbook
from workbook_reader import ConsolidationError, MAX_ROWS, MAX_EXPANDED_BYTES, read_workbook

MAX_FILES = 20

@dataclass
class Result:
    content: BytesIO
    files: int
    rows: int

def consolidate(files):
    """Combine first worksheets by exact headings, keeping duplicate rows."""
    if not 2 <= len(files) <= MAX_FILES:
        raise ConsolidationError(f'Choose between 2 and {MAX_FILES} Excel files.')
    output = Workbook()
    target = output.active
    target.title = 'Consolidated'
    headers = None
    row_count = 0
    budget = MAX_EXPANDED_BYTES
    for name, stream in files:
        data = read_workbook(name, stream, budget)
        budget -= data.expanded_bytes
        if headers is None:
            headers = data.headers
            target.append(headers)
            for cell in target[1]:
                cell.data_type = 's'
        elif set(data.headers) != set(headers):
            raise ConsolidationError(f'{name}: column headings do not match the first file. Check spelling, spaces and case.')
        positions = [data.headers.index(header) for header in headers]
        for row in data.rows:
            if row_count >= MAX_ROWS:
                raise ConsolidationError(f'Maximum {MAX_ROWS:,} combined rows supported.')
            values = [row[index] for index in positions]
            target.append(values)
            for index, value in enumerate(values, start=1):
                if isinstance(value, str):
                    target.cell(row_count + 2, index).data_type = 's'
            row_count += 1
    target.freeze_panes = 'A2'
    target.auto_filter.ref = target.dimensions
    for column in target.columns:
        target.column_dimensions[column[0].column_letter].width = 20
    content = BytesIO()
    output.save(content)
    content.seek(0)
    return Result(content, len(files), row_count)

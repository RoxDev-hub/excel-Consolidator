"""Workbook consolidation independent of the web interface."""
from dataclasses import dataclass
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException

MAX_FILES = 20
MAX_ROWS = 100_000
MAX_COLUMNS = 200
MAX_EXPANDED_BYTES = 100 * 1024 * 1024


class ConsolidationError(ValueError):
    pass


@dataclass
class Result:
    content: BytesIO
    files: int
    rows: int


def consolidate(files):
    """Combine (filename, binary stream) pairs, aligning exact column names.

    The first worksheet's first row must contain unique text headers. Blank
    rows are skipped; duplicates, text and numeric values are retained.
    Formulas are rejected until an explicit calculation policy is implemented.
    """
    if not 2 <= len(files) <= MAX_FILES:
        raise ConsolidationError(f"Choose between 2 and {MAX_FILES} Excel files.")
    output = Workbook()
    target = output.active
    target.title = "Consolidated"
    headers = None
    row_count = 0
    expanded_bytes = 0
    for name, stream in files:
        if not name.lower().endswith(".xlsx"):
            raise ConsolidationError(f"{name}: use an .xlsx workbook.")
        try:
            with ZipFile(stream) as archive:
                expanded_bytes += sum(item.file_size for item in archive.infolist())
                if expanded_bytes > MAX_EXPANDED_BYTES:
                    raise ConsolidationError("These workbooks are too large when unpacked. Try smaller files.")
            stream.seek(0)
            book = load_workbook(stream, read_only=True, data_only=False)
            try:
                sheet = book.worksheets[0]
                if sheet.max_column and sheet.max_column > MAX_COLUMNS:
                    raise ConsolidationError(f"{name}: maximum {MAX_COLUMNS} columns supported.")
                rows = sheet.iter_rows()
                first = next(rows, ())
                current = [cell.value for cell in first]
                if not current or any(not isinstance(h, str) or not h.strip() for h in current):
                    raise ConsolidationError(f"{name}: row 1 must contain a text heading for every column.")
                if any(cell.data_type == "f" for cell in first) or len(set(current)) != len(current):
                    raise ConsolidationError(f"{name}: headings must be unique text, without formulas.")
                if headers is None:
                    headers = current
                    target.append(headers)
                    for cell in target[1]:
                        cell.data_type = "s"
                elif set(current) != set(headers):
                    raise ConsolidationError(f"{name}: column headings do not match the first file. Check spelling, spaces and case.")
                positions = [current.index(header) for header in headers]
                for row_number, row in enumerate(rows, start=2):
                    if row_number > MAX_ROWS + 1:
                        raise ConsolidationError(f"{name}: maximum {MAX_ROWS:,} worksheet rows supported.")
                    if any(cell.data_type == "f" for cell in row):
                        raise ConsolidationError(f"{name}: formula found on row {row_number}. Save formulas as values before uploading.")
                    values = [cell.value for cell in row]
                    if all(value is None for value in values):
                        continue
                    if row_count >= MAX_ROWS:
                        raise ConsolidationError(f"Maximum {MAX_ROWS:,} combined rows supported.")
                    target.append([values[index] for index in positions])
                    # Strings beginning '=' must remain literal text in the export.
                    for index, source in enumerate(positions, start=1):
                        cell = target.cell(row_count + 2, index)
                        if isinstance(values[source], str):
                            cell.data_type = "s"
                    row_count += 1
            finally:
                book.close()
        except ConsolidationError:
            raise
        except (BadZipFile, InvalidFileException, KeyError, ValueError, IndexError, OSError, SyntaxError) as exc:
            raise ConsolidationError(f"{name}: could not read this workbook. Upload a valid, unencrypted .xlsx file.") from exc
    target.freeze_panes = "A2"
    target.auto_filter.ref = target.dimensions
    for column in target.columns:
        target.column_dimensions[column[0].column_letter].width = 20
    content = BytesIO()
    output.save(content)
    content.seek(0)
    return Result(content, len(files), row_count)

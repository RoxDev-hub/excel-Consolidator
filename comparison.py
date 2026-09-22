"""Value comparison only. Row order is ignored; duplicate counts matter."""
from collections import Counter
from datetime import date, datetime
from itertools import islice
from workbook_reader import MAX_EXPANDED_BYTES, read_workbook

def cell_key(value):
    # Numeric 1 and 1.0 match; booleans, text and numbers stay distinct.
    if isinstance(value, bool):
        return ('boolean', value)
    if isinstance(value, (int, float)):
        return ('number', value)
    if isinstance(value, datetime):
        return ('datetime', value.isoformat())
    if isinstance(value, date):
        return ('datetime', datetime.combine(value, datetime.min.time()).isoformat())
    return (type(value).__name__, value)

def compare_workbooks(actual_file, expected_file):
    actual = read_workbook(*actual_file)
    expected = read_workbook(*expected_file, budget=MAX_EXPANDED_BYTES - actual.expanded_bytes)
    missing_columns = [h for h in expected.headers if h not in actual.headers]
    extra_columns = [h for h in actual.headers if h not in expected.headers]
    report = dict(matches=False, actual_rows=len(actual.rows), expected_rows=len(expected.rows),
                  missing_columns=missing_columns, extra_columns=extra_columns,
                  matching_rows=None, missing_rows=None, extra_rows=None,
                  missing_examples=[], extra_examples=[], columns=expected.headers)
    if missing_columns or extra_columns:
        return report
    positions = [actual.headers.index(h) for h in expected.headers]
    actual_counts = Counter(tuple(cell_key(row[i]) for i in positions) for row in actual.rows)
    expected_counts = Counter(tuple(cell_key(v) for v in row) for row in expected.rows)
    missing, extra = expected_counts - actual_counts, actual_counts - expected_counts
    def examples(counts):
        return [dict(values=[str(value) if value is not None else '(blank)' for _, value in key], count=count)
                for key, count in islice(counts.items(), 10)]
    report.update(matches=not missing and not extra,
                  matching_rows=sum((actual_counts & expected_counts).values()),
                  missing_rows=sum(missing.values()), extra_rows=sum(extra.values()),
                  missing_examples=examples(missing), extra_examples=examples(extra))
    return report

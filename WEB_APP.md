# Excel Consolidator web app

A small Flask web app with a separate Python consolidation module. Upload
workbooks, consolidate, review file/row counts, and download one Excel file.

## Run locally (PowerShell)

**For the easiest Windows launch, double-click `Start Excel Consolidator.bat`.**
See [START_HERE.md](START_HERE.md) for first-time setup and the separation of
launcher, frontend, web adapter, and Excel processing. The launcher owns a
separate `.launcher-venv` and opens an available local port automatically.
The commands below are an alternative for developers.

From the repository folder, with Python 3.12 or newer installed:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:5000. Stop the server with Ctrl+C.
If your existing environment works, skip the environment creation command.
An isolated `.review-env` was used during implementation; you can also run
`.\.review-env\Scripts\python.exe app.py` while reviewing locally.

## First-version contract

- Select 2–20 `.xlsx` workbooks totalling less than 25 MB.
- Read only the first worksheet, using row 1 as unique, nonblank text headings.
- Require exactly matching column names (including spaces and case).
  Reordered columns are aligned to the first workbook's order.
- Keep input file/row order, duplicates, and original values; skip fully blank rows.
- Header-only workbooks are allowed; workbooks with no headers are rejected.
- Stop the whole operation on an invalid file; no partial success download.
- Reject formulas. Save formulas as values in Excel before uploading.
- Export values into a new workbook, with a frozen header and filters.
  Source formatting, charts, macros, additional sheets and formulas are not copied.
- Limit workbooks to 200 columns, 100,000 worksheet rows / combined data rows,
  and 100 MB total declared unpacked ZIP content.

Uploads are handled for the request only. The application does not create an
upload library or store generated workbooks on disk. Flask may spool larger
uploads into temporary files during processing; these are closed after the request.
The browser holds the download until files are reselected or the page is closed.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_web test_launcher
```

Tests exercise column alignment, duplicates, empty rows/files, invalid inputs,
formula handling, upload limits and the HTTP download. If present, the local
`tests/00_clean/input` sample is also checked for its 600 rows. Other sample
scenarios describe future cleaning/validation policies, not current behavior.

## Hosting later

This branch is local and has not been deployed. A Python host can run:

```powershell
waitress-serve --listen=0.0.0.0:8000 app:app
```

Use HTTPS through the host and configure request/time/concurrency limits before
public launch. The local Flask development server is for local review.
Future steps can add validation, cleaning and duplicate policies to the Python
module without mixing those rules into the page.

## Verify a result

After consolidation, click **Verify result** next to Download, choose an expected
`.xlsx` workbook, and click **Compare results**. The current consolidated workbook
is retained in browser memory and sent with the expected file. Nothing needs to
be moved out of Downloads. Reselecting source files clears verification and its
retained result. Choosing a different expected file clears the old report.

Comparison ignores row and column order, but counts duplicate occurrences.
Headings, text, whitespace, and value types must match exactly. Numbers such as
1 and 1.0 match; text "1" is different from numeric 1. No rounding tolerance or
cleaning is applied. Formatting is ignored. Both files use the first worksheet,
headers on row 1, and no formulas. Blank rows are skipped. Limits: 25 MB total
upload, 100 MB total unpacked content, 100,000 rows per file, 200 columns.

The report shows matching, missing, and extra row counts plus up to 10 distinct
example rows in each direction. Missing means present in expected but absent
from the consolidated result. Changed rows appear as one missing and one extra;
there is no record ID matching. Column mismatches are listed and stop row
comparison. Verification reports differences without changing either workbook.

## Stop the local app

When started through the launcher, **Stop app** asks for confirmation and requests
server shutdown, which lets the launcher exit. Download your workbook first.
The browser tab stays open with a shutdown message; you can close it yourself.
The button is disabled while this page is processing files. Stopping affects all
tabs connected to that launcher instance. The button and shutdown capability are
absent when running `python app.py` or a hosted WSGI server directly.

## Code responsibilities

- `launcher.py`: server lifecycle, local-only shutdown capability, setup and browser opening.
- `static/app.js`, `static/verification.js`, `static/lifecycle.js`: frontend interactions.
- `app.py`: HTTP adapter only; calls the comparison module or launcher callback.
- `workbook_reader.py`: shared input rules used by consolidation and comparison.
- `consolidator.py`: combining and exporting Excel data.
- `comparison.py`: comparing workbook values and duplicate counts.

Run all checks with `python -m unittest -v test_web test_launcher test_comparison`
using your project interpreter.

# Excel Consolidator web app

A small Flask web app with a separate Python consolidation module. Upload
workbooks, consolidate, review file/row counts, and download one Excel file.

## Run locally (PowerShell)

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
.\.venv\Scripts\python.exe -m unittest -v test_web
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

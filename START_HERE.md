# Open Excel Consolidator

1. Open this project folder in Windows File Explorer.
2. Double-click **Start Excel Consolidator.bat** (it may appear without `.bat`).
3. Wait for your browser to open, then choose your Excel files.

On the first run, the launcher prepares its own environment and downloads the
required libraries. You need **Python 3.12 or newer**, internet access during
setup, and a writable project folder. If Python is missing, the launcher shows
installation instructions. It first checks working project environments, then
the Windows Python launcher and Python on PATH. Later launches reuse the environment; dependencies
are installed again only when requirements change or libraries are missing.

**Keep the launcher window open while using the app. Close it or press Ctrl+C
to stop.** Closing the browser tab alone does not stop the app.

If the browser does not open, copy the address shown in the launcher window into
your browser. The port number may change each time. The app runs on your own
computer; launching it does not publish it online.

For an error, read the message in the launcher window. Check your connection
if library installation failed, then try again. A damaged launcher environment
can be rebuilt by renaming `.launcher-venv` and starting again; your workbooks
and developer environment are separate.

## Where each part lives

| Responsibility | Files |
| --- | --- |
| Launcher: Python detection, setup, server lifetime, browser opening | `Start Excel Consolidator.bat`, `launcher.py` |
| Frontend: page layout, styling, file selection, status, download link | `templates/index.html`, `static/style.css`, `static/app.js` |
| Web adapter: HTTP uploads, responses and errors | `app.py` |
| Excel processing: reading, column checks, combining and exporting | `consolidator.py` |

The launcher starts the web adapter. The web adapter calls the Excel module.
Neither the frontend nor the Excel module manages installation or startup.

See [WEB_APP.md](WEB_APP.md) for developer commands and supported workbook formats.

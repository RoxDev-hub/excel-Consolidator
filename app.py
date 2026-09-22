"""Run locally with python app.py; deploy with waitress-serve app:app."""
import secrets
from flask import Flask, jsonify, render_template, request, send_file
from consolidator import ConsolidationError, consolidate
from comparison import compare_workbooks

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


@app.get("/")
def index():
    return render_template("index.html", stop_token=app.config.get('LOCAL_STOP_TOKEN'))


@app.post('/compare')
def compare():
    if set(request.files) != {'actual', 'expected'} or any(len(request.files.getlist(k)) != 1 for k in request.files):
        return jsonify(error='Choose one expected workbook after consolidating your files.'), 400
    actual, expected = request.files['actual'], request.files['expected']
    try:
        return jsonify(compare_workbooks((actual.filename or '', actual.stream), (expected.filename or '', expected.stream)))
    except ConsolidationError as exc:
        return jsonify(error=str(exc)), 400


@app.post('/stop')
def stop_local_app():
    callback = app.config.get('LOCAL_STOP_CALLBACK')
    token = app.config.get('LOCAL_STOP_TOKEN')
    if not callback or not token:
        return jsonify(error='Stopping is available only through the local launcher.'), 404
    if (request.remote_addr != '127.0.0.1'
            or request.host_url.rstrip('/') != app.config.get('LOCAL_ORIGIN')
            or request.headers.get('Origin') != app.config.get('LOCAL_ORIGIN')
            or not secrets.compare_digest(request.headers.get('X-Stop-Token', ''), token)):
        return jsonify(error='Shutdown request was not authorized. Use the local app page.'), 403
    callback()
    return jsonify(message='The app is shutting down. You can close this tab.')


@app.post("/consolidate")
def process():
    uploads = request.files.getlist("files")
    try:
        result = consolidate([(upload.filename or "Unnamed file", upload.stream) for upload in uploads])
    except ConsolidationError as exc:
        return jsonify(error=str(exc)), 400
    response = send_file(result.content, as_attachment=True, download_name="consolidated.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response.headers["X-File-Count"] = str(result.files)
    response.headers["X-Row-Count"] = str(result.rows)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(413)
def too_large(error):
    return jsonify(error="Upload limit exceeded. Choose files totalling less than 25 MB."), 413


@app.errorhandler(500)
def unexpected_error(error):
    return jsonify(error="The files could not be processed. Please check the workbooks and try again."), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

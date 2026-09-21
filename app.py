"""Run locally with python app.py; deploy with waitress-serve app:app."""
from flask import Flask, jsonify, render_template, request, send_file
from consolidator import ConsolidationError, consolidate

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


@app.get("/")
def index():
    return render_template("index.html")


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

# app.py

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import json

from utils import (
    extract_text_from_file,
    calculate_similarity,
    get_top_matches
)

# ---------- SAFE CONFIGURATION (Windows + OneDrive friendly) ----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use an absolute path to avoid PermissionError
UPLOAD_FOLDER = os.path.join(BASE_DIR, "temp_files")

# Create the folder once if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB


def allowed_file(filename: str) -> bool:
    """Check if the file extension is supported."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def clear_upload_folder():
    """Delete all files inside the upload folder (but not the folder itself)."""
    for name in os.listdir(app.config["UPLOAD_FOLDER"]):
        path = os.path.join(app.config["UPLOAD_FOLDER"], name)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except PermissionError:
            # If Windows locks a file, just skip it instead of crashing
            pass


# ---------- MAIN APPLICATION ROUTE ----------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # 1. Get User Inputs and Validation
        job_description_raw = request.form.get("job_description", "").strip()
        resume_files = request.files.getlist("resumes")

        if not job_description_raw:
            return render_template(
                "index.html",
                error="Job Description cannot be empty.",
                matches=None,
                job_description=""
            )

        if not resume_files or all(f.filename.strip() == "" for f in resume_files):
            return render_template(
                "index.html",
                error="Please upload at least one resume.",
                matches=None,
                job_description=job_description_raw
            )

        # 2. Clean upload folder (only files, not the folder)
        clear_upload_folder()

        uploaded_filenames = []

        # 3. Save valid files
        for file in resume_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if not filename:
                    continue
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                uploaded_filenames.append(filename)

        if not uploaded_filenames:
            return render_template(
                "index.html",
                error="No valid resumes were uploaded. Check file types (PDF, DOCX, TXT).",
                matches=None,
                job_description=job_description_raw
            )

        # 4. NLP Processing: extract text from each resume
        resume_texts = []
        for filename in uploaded_filenames:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            resume_texts.append(extract_text_from_file(filepath))

        # Calculate similarity scores
        scores = calculate_similarity(job_description_raw, resume_texts)

        # 5. Get Top Matches
        top_matches = get_top_matches(uploaded_filenames, scores, top_n=5)

        # 6. Render Results
        return render_template(
            "index.html",
            job_description=job_description_raw,
            matches=top_matches,
            error=None
        )

    # Initial GET: show empty form
    return render_template("index.html", matches=None, job_description="")
    

if __name__ == "__main__":
    app.run(debug=True)

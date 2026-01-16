from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

DB_PATH = "tracker.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def db():
    return sqlite3.connect(DB_PATH)


@app.route("/")
def index():
    meals = [
        ("Breakfast", "Planned breakfast"),
        ("Mid-Morning", "Planned mid-morning"),
        ("Lunch", "Planned lunch"),
        ("Evening", "Planned evening"),
        ("Dinner", "Planned dinner"),
        ("Night", "Planned night"),
    ]
    return render_template("index.html", meals=meals)


@app.route("/log", methods=["POST"])
def log_meal():
    data = request.json
    con = db()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO meals
        (date, meal_type, planned_item, status, discomfort, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date, meal_type)
        DO UPDATE SET
            status=excluded.status,
            discomfort=excluded.discomfort,
            notes=excluded.notes,
            updated_at=excluded.updated_at
    """, (
        data["date"],
        data["meal_type"],
        data.get("planned_item"),
        data["status"],
        data.get("discomfort"),
        data.get("notes"),
        datetime.now().isoformat()
    ))

    con.commit()
    con.close()
    return jsonify({"ok": True})


@app.route("/logs/<date>")
def get_logs(date):
    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT meal_type, status, discomfort, notes, image
        FROM meals WHERE date=?
    """, (date,))

    rows = cur.fetchall()
    con.close()

    return jsonify([
        {
            "meal_type": r[0],
            "status": r[1],
            "discomfort": r[2],
            "notes": r[3],
            "image": r[4]
        } for r in rows
    ])


@app.route("/upload", methods=["POST"])
def upload_image():
    file = request.files.get("image")
    date = request.form.get("date")
    meal_type = request.form.get("meal_type")

    if not file:
        return jsonify({"error": "No file"}), 400

    filename = secure_filename(f"{date}_{meal_type}_{file.filename}")
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    con = db()
    cur = con.cursor()
    cur.execute("""
        UPDATE meals SET image=?
        WHERE date=? AND meal_type=?
    """, (filename, date, meal_type))
    con.commit()
    con.close()

    return jsonify({"ok": True, "filename": filename})


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/report/day/<date>")
def day_report(date):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT status FROM meals WHERE date=?", (date,))
    statuses = [r[0] for r in cur.fetchall()]
    con.close()

    skipped = statuses.count("skipped")
    eligible = len(statuses) - skipped
    completed = sum(1 for s in statuses if s in ("done", "partial"))
    percent = 0 if eligible == 0 else round((completed / eligible) * 100)

    return jsonify({
        "completed": completed,
        "eligible": eligible,
        "skipped": skipped,
        "percent": percent
    })


@app.route("/report/week/<start>")
def week_report(start):
    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT date, status FROM meals
        WHERE date >= date(?) AND date < date(?, '+7 day')
    """, (start, start))

    rows = cur.fetchall()
    con.close()

    summary = {}
    for d, s in rows:
        if d not in summary:
            summary[d] = {"c": 0, "e": 0, "s": 0}
        if s == "skipped":
            summary[d]["s"] += 1
        else:
            summary[d]["e"] += 1
            if s in ("done", "partial"):
                summary[d]["c"] += 1

    return jsonify([
        {
            "date": d,
            "percent": 0 if v["e"] == 0 else round((v["c"] / v["e"]) * 100),
            "completed": v["c"],
            "eligible": v["e"],
            "skipped": v["s"]
        }
        for d, v in sorted(summary.items())
    ])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

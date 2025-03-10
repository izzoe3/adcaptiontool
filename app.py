from flask import Flask, render_template, request, jsonify, send_file
import csv
import io
import google.generativeai as genai
import sqlite3
import json
import re

app = Flask(__name__)

# Set up Google AI API Key
API_KEY = "AIzaSyAxVViNcXOlgFom5Z05AzohgAJRJh8q7SI"
genai.configure(api_key=API_KEY)

# Predefined intakes and programs
INTAKES = ["February", "April", "July", "October"]
FOUNDATION_PROGRAMS = [
    "Foundation in Science",
    "Foundation in Arts",
    "Foundation in Business",
    "ACCA Foundation in Accountancy"
]
PLATFORMS = ["Meta", "Google"]

# Initialize SQLite database
def init_db():
    with sqlite3.connect("history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT,
                campaign_type TEXT,
                intake TEXT,
                tone TEXT,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_db()

# Save generated ad copy to history
def save_to_history(platform, campaign_type, intake, tone, result):
    with sqlite3.connect("history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO history (platform, campaign_type, intake, tone, result)
            VALUES (?, ?, ?, ?, ?)
        """, (platform, campaign_type, intake, tone, json.dumps(result)))
        conn.commit()

@app.route('/')
def home():
    return render_template('index.html', intakes=INTAKES, foundation_programs=FOUNDATION_PROGRAMS, platforms=PLATFORMS)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    platform = data['platform']
    campaign_type = data['campaign_type']
    intake = data['intake']
    tone = data['tone']
    min_words = int(data.get('min_words', 10))
    selected_programs = data.get('programs', [])
    add_on_text = data.get('add_on_text', '').strip()

    # Construct the appropriate prompt
    if campaign_type == "Foundation":
        programs_text = ", ".join(selected_programs) if selected_programs else ", ".join(FOUNDATION_PROGRAMS)
        program_text = f"for QIU's {intake} Intake focusing on {programs_text}"
    else:
        program_text = f"for QIU's {intake} Intake - {campaign_type} program"

    # ✅ **Modify Prompt to Integrate Add-On Text Naturally**
    if add_on_text:
        add_on_prompt = f" Try to incorporate the theme of '{add_on_text}' naturally in the copy."
    else:
        add_on_prompt = ""

    if platform == "Meta":
        prompt = f"""
        Generate exactly 5 ad captions (each at least {min_words} words) and 5 ad headlines (exactly 30 characters) {program_text} in {tone} tone.{add_on_prompt}

        **Format strictly as follows:**
        Captions:
        1. ...
        2. ...
        3. ...
        4. ...
        5. ...

        Headlines:
        1. ...
        2. ...
        3. ...
        4. ...
        5. ...
        """
    else:  # Google Ads
        prompt = f"""
        Generate exactly 15 ad headlines (each max 30 characters) and 4 ad descriptions (each max 90 characters) {program_text} in {tone} tone.{add_on_prompt}

        **Format strictly as follows:**
        Headlines:
        1. ...
        2. ...
        ...
        15. ...

        Descriptions:
        1. ...
        2. ...
        3. ...
        4. ...
        """

    # ✅ AI Call
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    response = model.generate_content(prompt)

    # ✅ Process AI Response
    captions, headlines, descriptions = [], [], []
    if response and hasattr(response, "candidates") and response.candidates:
        text = response.candidates[0].content.parts[0].text.split("\n")
        section = None

        for line in text:
            line = line.strip()
            if re.match(r"^Captions?:", line, re.IGNORECASE):
                section = "captions" if platform == "Meta" else None
            elif re.match(r"^Headlines?:", line, re.IGNORECASE):
                section = "headlines"
            elif re.match(r"^Descriptions?:", line, re.IGNORECASE):
                section = "descriptions" if platform == "Google" else None
            elif section and re.match(r"^\d+\.\s", line):
                content = line.split(".", 1)[1].strip()
                if section == "captions":
                    captions.append(content)
                elif section == "headlines":
                    headlines.append(content)
                elif section == "descriptions":
                    descriptions.append(content)

    # ✅ Ensure Proper Data Structure
    result = {
        "captions": captions[:5] if platform == "Meta" else [],
        "headlines": headlines[:5] if platform == "Meta" else headlines[:15],
        "descriptions": descriptions[:4] if platform == "Google" else []
    }

    save_to_history(platform, campaign_type, intake, tone, result)
    return jsonify(result)

@app.route('/generate_event', methods=['POST'])
def generate_event():
    data = request.json
    event_name = data['event_name']
    event_venue = data['event_venue']
    event_time = "2:00pm - 5:00pm"  # Fixed format
    tone = data['tone']
    add_on_text = data.get('add_on_text', '').strip()

    # Constructing the prompt
    prompt = f"""
    Generate exactly 5 engaging Meta ad captions to promote the following event in a {tone} tone:

    **Event Details:**
    - Event Name: {event_name}
    - Venue: {event_venue}
    - Time: {event_time}

    {"Additional Context: " + add_on_text if add_on_text else ""}

    **Format strictly as follows:**
    Captions:
    1. ...
    2. ...
    3. ...
    4. ...
    5. ...
    """

    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    response = model.generate_content(prompt)

    captions = []
    if response and hasattr(response, "candidates") and response.candidates:
        text = response.candidates[0].content.parts[0].text.split("\n")
        section = None

        for line in text:
            line = line.strip()
            if re.match(r"^Captions?:", line, re.IGNORECASE):
                section = "captions"
            elif section and re.match(r"^\d+\.\s", line):
                content = line.split(".", 1)[1].strip()
                captions.append(content)

    # Ensure we return exactly 5 captions
    result = {"captions": captions[:5]}

    # Save to history
    save_to_history("Meta", "Event", event_name, tone, result)

    return jsonify(result)


@app.route('/history')
def history():
    with sqlite3.connect("history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT platform, campaign_type, intake, tone, result, timestamp FROM history
            ORDER BY timestamp DESC
            LIMIT 2
        """)
        history_data = [{"platform": row[0], "campaign_type": row[1], "intake": row[2], 
                         "tone": row[3], "result": json.loads(row[4]), "timestamp": row[5]} 
                        for row in cursor.fetchall()]
    return render_template('history.html', history=history_data)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    with sqlite3.connect("history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
    return jsonify({"success": True, "message": "History cleared."})

# ✅ New: Export history to CSV
@app.route('/export_history')
def export_history():
    with sqlite3.connect("history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, platform, campaign_type, intake, tone, result FROM history ORDER BY timestamp DESC")
        history_data = cursor.fetchall()

    # ✅ Prepare CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # ✅ Write header
    writer.writerow(["Timestamp", "Platform", "Campaign Type", "Intake", "Tone", "Captions", "Headlines", "Descriptions"])

    # ✅ Write data
    for row in history_data:
        result_data = json.loads(row[5])  # Convert JSON string back to Python object
        writer.writerow([
            row[0], row[1], row[2], row[3], row[4],
            " | ".join(result_data.get("captions", [])),
            " | ".join(result_data.get("headlines", [])),
            " | ".join(result_data.get("descriptions", []))
        ])

    output.seek(0)

    # ✅ Return CSV file
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="ad_caption_history.csv"
    )

if __name__ == '__main__':
    app.run(debug=True)

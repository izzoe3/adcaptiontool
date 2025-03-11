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
    platform = data.get('platform')
    campaign_type = data.get('campaign_type')
    intake = data.get('intake')
    tone = data.get('tone')
    min_words = int(data.get('min_words', 10)) if platform == "Meta" else 10
    add_on_text = data.get('add_on_text', '').strip()
    programs = data.get('programs', [])

    # Validate required fields
    if not all([platform, campaign_type, intake, tone]):
        return jsonify({"error": "All fields except Add-On Text are required."}), 400

    # Handle campaign type logic
    if campaign_type == "General":
        campaign_desc = f"an intake promotion for Quest International University in {intake}"
    elif campaign_type == "Foundation" and programs:
        campaign_desc = f"the {', '.join(programs)} program(s) at Quest International University in {intake}"
    else:
        campaign_desc = f"the {campaign_type} program at Quest International University in {intake}"

    # Add-on text prompt
    add_on_prompt = f" Incorporate the theme of '{add_on_text}' naturally in the copy." if add_on_text else ""

    # Construct platform-specific prompt
    if platform == "Meta":
        prompt = f"""
        Generate exactly 5 engaging Meta ad captions (each at least {min_words} words) and 5 ad headlines (exactly 30 characters) to promote {campaign_desc} in a {tone} tone:

        **Details:**
        - University: Quest International University
        - Intake: {intake}

        {add_on_prompt}

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
    else:  # Google
        prompt = f"""
        Generate exactly 5 engaging Google ad headlines (exactly 30 characters) and 5 ad descriptions (exactly 90 characters) to promote {campaign_desc} in a {tone} tone:

        **Details:**
        - University: Quest International University
        - Intake: {intake}

        {add_on_prompt}

        **Format strictly as follows:**
        Headlines:
        1. ...
        2. ...
        3. ...
        4. ...
        5. ...

        Descriptions:
        1. ...
        2. ...
        3. ...
        4. ...
        5. ...
        """

    # AI Call
    model = genai.GenerativeModel("gemini-2.0-flash-lite")  # Replace with your model
    response = model.generate_content(prompt)

    # Process AI Response
    captions, headlines, descriptions = [], [], []
    if response and hasattr(response, "candidates") and response.candidates:
        text = response.candidates[0].content.parts[0].text.split("\n")
        section = None

        for line in text:
            line = line.strip()
            if re.match(r"^Captions?:", line, re.IGNORECASE):
                section = "captions"
            elif re.match(r"^Headlines?:", line, re.IGNORECASE):
                section = "headlines"
            elif re.match(r"^Descriptions?:", line, re.IGNORECASE):
                section = "descriptions"
            elif section and re.match(r"^\d+\.\s", line):
                content = line.split(".", 1)[1].strip()
                if section == "captions":
                    captions.append(content)
                elif section == "headlines":
                    headlines.append(content)
                elif section == "descriptions":
                    descriptions.append(content)

    # Ensure proper data structure
    result = {
        "captions": captions[:5] if platform == "Meta" else [],
        "headlines": headlines[:5],
        "descriptions": descriptions[:5] if platform == "Google" else []
    }

    # Save to history
    save_to_history(platform, campaign_type, intake, tone, result)

    return jsonify(result)

@app.route('/event_caption', methods=['GET', 'POST'])
def event_caption():
    if request.method == 'POST':
        data = request.json
        event_name = data.get('event_name')
        event_venue = data.get('event_venue')
        event_date = data.get('event_date')
        event_time = data.get('event_time')
        tone = data.get('tone')
        min_words = int(data.get('min_words', 10))
        add_on_text = data.get('add_on_text', '').strip()

        if not all([event_name, event_venue, event_date, event_time, tone]):
            return jsonify({"error": "All fields except Add-On Text are required."}), 400

        add_on_prompt = f" Incorporate the theme of '{add_on_text}' naturally in the copy." if add_on_text else ""

        prompt = f"""
        Generate exactly 5 engaging Meta ad captions (each at least {min_words} words) and 5 ad headlines (exactly 30 characters) to promote the following event organized by Quest International University in a {tone} tone:

        **Event Details:**
        - Event Name: {event_name}
        - Venue: {event_venue}
        - Date: {event_date}
        - Time: {event_time}
        - University: Quest International University

        {add_on_prompt}

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

        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt)

        captions, headlines = [], []
        if response and hasattr(response, "candidates") and response.candidates:
            text = response.candidates[0].content.parts[0].text.split("\n")
            section = None

            for line in text:
                line = line.strip()
                if re.match(r"^Captions?:", line, re.IGNORECASE):
                    section = "captions"
                elif re.match(r"^Headlines?:", line, re.IGNORECASE):
                    section = "headlines"
                elif section and re.match(r"^\d+\.\s", line):
                    content = line.split(".", 1)[1].strip()
                    if section == "captions":
                        captions.append(content)
                    elif section == "headlines":
                        headlines.append(content)

        result = {
            "captions": captions[:5],
            "headlines": headlines[:5]
        }

        save_to_history("Meta", "Event", event_name, tone, result)

        return jsonify(result)

    return render_template('event_caption.html')

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
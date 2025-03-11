from flask import Flask, render_template, request, jsonify, send_file
import csv
import io
import google.generativeai as genai
import sqlite3
import json
import re
from datetime import datetime
import os  # Add this
from dotenv import load_dotenv  # Already added in integration

app = Flask(__name__)

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or "AIzaSyAxVViNcXOlgFom5Z05AzohgAJRJh8q7SI"  # Fallback for testing
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
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  platform TEXT,
                  campaign_type TEXT,
                  intake TEXT,
                  tone TEXT,
                  result TEXT,
                  used TEXT DEFAULT '{}',
                  target_audience TEXT,
                  ad_goal TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Save generated ad copy to history
def save_to_history(platform, campaign_type, intake, tone, result, target_audience=None, ad_goal=None):
    # Assumes connection is passed from caller
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result_json = json.dumps(result)
    used_json = json.dumps({})
    c = sqlite3.connect('history.db').cursor()  # Temporary fallback if not fixed elsewhere
    c.execute("INSERT INTO history (timestamp, platform, campaign_type, intake, tone, result, used, target_audience, ad_goal) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (timestamp, platform, campaign_type, intake, tone, result_json, used_json, target_audience, ad_goal))
    c.connection.commit()

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
    min_words = int(data.get('min_words', 10)) if platform == "Meta" else None  # Only for Meta
    add_on_text = data.get('add_on_text', '').strip() if platform == "Meta" else ''  # Only for Meta
    programs = data.get('programs', [])
    target_audience = data.get('target_audience')
    ad_goal = data.get('ad_goal', '')

    if not all([platform, campaign_type, intake, tone, target_audience]):
        return jsonify({"error": "Required fields missing."}), 400

    if campaign_type == "General":
        campaign_desc = f"an intake promotion for Quest International University in {intake}"
    elif campaign_type == "Foundation" and programs:
        campaign_desc = f"the {', '.join(programs)} Foundation program(s) at Quest International University in {intake}"
    elif campaign_type == "Foundation":
        campaign_desc = f"the Foundation programs at Quest International University in {intake}"
    elif campaign_type == "MBBS":
        campaign_desc = f"the MBBS program at Quest International University in {intake}"
    elif campaign_type == "Pharmacy":
        campaign_desc = f"the Pharmacy program at Quest International University in {intake}"
    else:
        campaign_desc = f"a program at Quest International University in {intake}"

    add_on_prompt = f" Incorporate the theme of '{add_on_text}' naturally in the copy." if add_on_text and platform == "Meta" else ""
    goal_prompt = f" Focus on {ad_goal} as the ad goal (e.g., encourage clicks, sign-ups, or shares)." if ad_goal else ""

    if platform == "Meta":
        prompt = f"""
        Generate exactly 5 engaging Meta ad captions (each at least {min_words} words) and 5 ad headlines (exactly 30 characters) to promote {campaign_desc} in a {tone} tone, targeting {target_audience}:

        **Details:**
        - University: Quest International University
        - Intake: {intake}

        {add_on_prompt}
        {goal_prompt}

        Craft captions that hook the audience with a clear benefit or call-to-action relevant to {target_audience}.

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
        Generate exactly 5 engaging Google ad headlines (exactly 30 characters) and 5 ad descriptions (exactly 90 characters) to promote {campaign_desc} in a {tone} tone, targeting {target_audience}:

        **Details:**
        - University: Quest International University
        - Intake: {intake}

        {goal_prompt}

        Craft descriptions with a strong hook or benefit tailored to {target_audience}.

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

    model = genai.GenerativeModel("gemini-2.0-flash-lite")  # Updated from your code
    response = model.generate_content(prompt)

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
                content = re.sub(r"^\d+\.\s*", "", line).strip()
                if section == "captions":
                    captions.append(content)
                elif section == "headlines":
                    headlines.append(content)
                elif section == "descriptions":
                    descriptions.append(content)

    # Platform-specific result structure
    if platform == "Meta":
        result = {
            "captions": captions[:5],
            "headlines": headlines[:5]
        }
    else:  # Google
        result = {
            "headlines": headlines[:5],
            "descriptions": descriptions[:5]
        }

    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    save_to_history(platform, campaign_type, intake, tone, result, target_audience, ad_goal)
    item_id = c.lastrowid
    conn.close()

    print("Response:", {"result": result, "id": item_id})
    return jsonify({"result": result, "id": item_id})


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
        target_audience = data.get('target_audience')
        ad_goal = data.get('ad_goal', '')

        if not all([event_name, event_venue, event_date, event_time, tone, target_audience]):
            return jsonify({"error": "Required fields missing."}), 400

        add_on_prompt = f" Incorporate the theme of '{add_on_text}' naturally in the copy." if add_on_text else ""
        goal_prompt = f" Focus on {ad_goal} as the ad goal (e.g., encourage attendance, shares, or registrations)." if ad_goal else ""

        prompt = f"""
        Generate exactly 5 engaging Meta ad captions (each at least {min_words} words) and 5 ad headlines (exactly 30 characters) to promote the following event organized by Quest International University in a {tone} tone, targeting {target_audience}:

        **Details:**
        - University: Quest International University
        - Event Name: {event_name}
        - Venue: {event_venue}
        - Date: {event_date}
        - Time: {event_time}

        {add_on_prompt}
        {goal_prompt}

        Craft captions with a compelling hook or benefit tailored to {target_audience}.

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
                    content = re.sub(r"^\d+\.\s*", "", line).strip()
                    if section == "captions":
                        captions.append(content)
                    elif section == "headlines":
                        headlines.append(content)

        result = {
            "captions": captions[:5],
            "headlines": headlines[:5],
            "descriptions": []  # Always empty for events (Meta only)
        }

        conn = sqlite3.connect('history.db')
        c = conn.cursor()
        save_to_history("Meta", "Event", event_name, tone, result, target_audience, ad_goal)
        item_id = c.lastrowid  # Use lastrowid instead of query
        conn.close()

        print("Response:", {"result": result, "id": item_id})
        return jsonify({"result": result, "id": item_id})

    return render_template('event_caption.html')

@app.route('/history')
def history():
    conn = sqlite3.connect('history.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY timestamp DESC")
    history_data = c.fetchall()
    conn.close()

    history = []
    for row in history_data:
        result = json.loads(row['result'])
        used = json.loads(row['used']) if row['used'] else {}
        history.append({
            'id': row['id'],
            'timestamp': row['timestamp'],
            'platform': row['platform'],
            'campaign_type': row['campaign_type'],
            'intake': row['intake'],
            'tone': row['tone'],
            'result': result,
            'used': used,
            'target_audience': row['target_audience'],
            'ad_goal': row['ad_goal']
        })
    return render_template('history.html', history=history)

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
    
@app.route('/mark_used', methods=['POST'])
def mark_used():
    data = request.json
    item_id = data.get('id')
    caption = data.get('caption')  # Works for headlines too
    is_used = data.get('used', True)

    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute("SELECT result, used FROM history WHERE id = ?", (item_id,))
    row = c.fetchone()
    if row:
        result = json.loads(row[0])
        used = json.loads(row[1]) if row[1] else {}

        # Check if the content (caption/headline/description) exists in result
        if (caption in result.get('captions', []) or 
            caption in result.get('headlines', []) or 
            caption in result.get('descriptions', [])):
            if is_used:
                used[caption] = True
            else:
                used.pop(caption, None)
            c.execute("UPDATE history SET used = ? WHERE id = ?", (json.dumps(used), item_id))
            conn.commit()

    conn.close()
    return jsonify({"success": True})

@app.route('/persona', methods=['GET', 'POST'])
def persona():
    if request.method == 'POST':
        data = request.json
        industry = data.get('industry')
        product = data.get('product')
        demographic = data.get('demographic')
        tone = data.get('tone')  # Reuse tone from existing options

        if not all([industry, product, demographic, tone]):
            return jsonify({"error": "Required fields missing."}), 400

        prompt = (
            f"Create a customer persona for a {industry} company selling {product}. "
            f"Target: {demographic}. Provide exactly 10 fields in a {tone} tone:\n"
            "1. Name (fictional)\n2. Age\n3. Gender\n4. Location\n5. Job/Role\n"
            "6. Interests\n7. Pain Points\n8. Goals\n9. Preferred Marketing Channels\n10. Recommended Messaging Tone"
        )

        model = genai.GenerativeModel("gemini-1.5-flash")  # Use a real model
        response = model.generate_content(prompt)
        persona_text = response.text.strip()

        # Parse persona into a list
        persona_lines = [line.strip() for line in persona_text.split('\n') if line.strip() and re.match(r"^\d+\.", line)]
        result = {"persona": persona_lines[:10]}  # Ensure exactly 10 fields

        # Save to history (reuse existing function)
        conn = sqlite3.connect('history.db')
        c = conn.cursor()
        save_to_history("Persona", "Persona", product, tone, result, demographic, "Persona Creation")
        item_id = c.lastrowid
        conn.close()

        return jsonify({"result": result, "id": item_id})

    return render_template('persona.html', tones=["Professional", "Casual", "Exciting", "Inspirational", "Urgent", "Friendly"])

if __name__ == '__main__':
    app.run(debug=True)
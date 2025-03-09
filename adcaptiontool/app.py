from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import sqlite3
import re
import json  # Import json for proper parsing

app = Flask(__name__)

# Set up Google AI API Key
API_KEY = "AIzaSyAxVViNcXOlgFom5Z05AzohgAJRJh8q7SI"  # Replace with your actual API key
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

# Initialize database
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

# Save result to history
def save_to_history(platform, campaign_type, intake, tone, result):
    with sqlite3.connect("history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO history (platform, campaign_type, intake, tone, result)
            VALUES (?, ?, ?, ?, ?)
        """, (platform, campaign_type, intake, tone, json.dumps(result)))  # Saving the result as JSON
        conn.commit()

# Retrieve last 2 history items
def get_history():
    with sqlite3.connect("history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT platform, campaign_type, intake, tone, result, timestamp FROM history
            ORDER BY timestamp DESC
            LIMIT 2
        """)
        
        # Format the result into a dictionary for easier handling in the frontend
        history = []
        for row in cursor.fetchall():
            history_item = {
                "platform": row[0],
                "campaign_type": row[1],
                "intake": row[2],
                "tone": row[3],
                "result": json.loads(row[4]),  # Assuming result is a valid JSON string
                "timestamp": row[5]
            }
            history.append(history_item)
        
        return history

@app.route('/history')
def history():
    history = get_history()  # Fetch last two results
    return render_template('history.html', history=history)


@app.route('/')
def home():
    history = get_history()  # Fetch last two results
    return render_template(
        'index.html',
        intakes=INTAKES,
        foundation_programs=FOUNDATION_PROGRAMS,
        platforms=PLATFORMS,
        history=history
    )

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    platform = data.get('platform', 'Meta')
    campaign_type = data.get('campaign_type', 'General')
    intake = data.get('intake', 'April')
    tone = data.get('tone', 'Casual')
    custom_message = data.get('custom_message', '')
    min_words = int(data.get('min_words', 10))
    selected_programs = data.get('programs', [])

    # Construct the program text for the prompt
    if campaign_type == "General":
        program_text = f"for QIU's {intake} Intake"
    elif campaign_type == "Foundation":
        programs_list = ", ".join(selected_programs) if selected_programs and "All" not in selected_programs else ", ".join(FOUNDATION_PROGRAMS)
        program_text = f"for QIU's {intake} Intake focusing on {programs_list}"
    else:
        program_text = f"for QIU's {intake} Intake - {campaign_type} program"

    # Define the correct prompt structure based on platform
    if platform == "Meta":
        prompt = f"""Generate exactly 5 ad captions (each {min_words} words minimum) and 5 headlines (exactly 30 characters) {program_text} in {tone} tone.
        DO NOT generate descriptions. Only return the following format:

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
        prompt = f"""Generate exactly 15 headlines (each exactly 30 characters) and 4 descriptions (each exactly 90 characters) {program_text} in {tone} tone.
        DO NOT generate anything other than the following format:

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

    # Call the AI model
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    response = model.generate_content(prompt)

    captions, headlines, descriptions = [], [], []

    if response and hasattr(response, "candidates") and response.candidates:
        text = response.candidates[0].content.parts[0].text
        lines = text.split("\n")

        section = None  # Track which section is being parsed

        for line in lines:
            line = line.strip()

            if "Captions:" in line:
                section = "captions" if platform == "Meta" else None
            elif "Headlines:" in line:
                section = "headlines"
            elif "Descriptions:" in line:
                section = "descriptions" if platform == "Google" else None
            elif section and re.match(r"^\d+\.\s", line):  # Ensure it's a numbered item
                content = line.split(".", 1)[1].strip()
                if section == "captions":
                    captions.append(content)
                elif section == "headlines":
                    headlines.append(content)
                elif section == "descriptions":
                    descriptions.append(content)

    # Ensure Meta ads do NOT include descriptions
    if platform == "Meta":
        descriptions = []  # Force-clear descriptions

    # Ensure correct output format
    result = {
        "captions": captions[:5] if platform == "Meta" else [],
        "headlines": headlines[:5] if platform == "Meta" else headlines[:15],
        "descriptions": descriptions[:4] if platform == "Google" else []
    }

    # Save to history with clean data (no HTML)
    save_to_history(platform, campaign_type, intake, tone, result)

    return jsonify(result)

@app.route('/history', methods=['GET'])
def fetch_history():
    return jsonify(get_history())

@app.route('/clear_history', methods=['POST'])
def clear_history():
    with sqlite3.connect("history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
    return jsonify({"message": "History cleared"})

if __name__ == '__main__':
    app.run(debug=True)

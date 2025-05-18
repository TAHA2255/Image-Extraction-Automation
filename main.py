from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import openai
import json
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env file

openai.api_key = os.getenv("OPENAI_API_KEY")
creds_json = os.getenv("GOOGLE_CREDENTIALS")

app = Flask(__name__)

 #Load credentials from environment variable



# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
if creds_json:
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
else:
    raise Exception("Missing GOOGLE_CREDENTIALS environment variable")
#creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Your target sheet
dest_sheet = client.open("Online Clients Weight Analysis NEW (Responses)").worksheet("Image Data")



def extract_text_from_drive_link(image_url):
    try:
        # Step 1: Download image from Drive
        #file_id = image_url.split("/d/")[1].split("/")[0]
        if "/d/" in image_url:
            file_id = image_url.split("/d/")[1].split("/")[0]
        elif "id=" in image_url:
            file_id = image_url.split("id=")[1].split("&")[0]
        else:
            return {"error": "Invalid Google Drive link format", "url": image_url}
        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(direct_url)
        img = Image.open(BytesIO(response.content))

        # Step 2: Extract text via OCR
        text = pytesseract.image_to_string(img)

        # Step 3: Send text to OpenAI for structuring
        prompt = f"""
You are a medical assistant. Extract key patient data, vitals, diagnoses, test results, medications, and relevant structured info from this medical text. Return the result as JSON like: {{"data": ...}}.

Medical Text:
{text}
        """

        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Or "gpt-3.5-turbo" if needed
            messages=[
                {"role": "system", "content": "You are a medical information extractor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        ai_response = completion['choices'][0]['message']['content']

        # Clean the code block markers
        if ai_response.startswith("```"):
            ai_response = ai_response.strip("`")  # remove all backticks
            ai_response = ai_response.split("\n", 1)[1]  # remove `json` line
            ai_response = ai_response.rsplit("\n", 1)[0]  # remove ending ```

        # Try to parse and return the JSON
        try:
            structured_data = json.loads(ai_response)
            return structured_data
        except json.JSONDecodeError:
            return {"error": "Failed to parse cleaned AI response", "raw": ai_response}

    except Exception as e:
        return {"error": str(e)}



@app.route("/")
def home():
    return "Flask app is working!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    image_url = data.get("image_url")
    name = data.get("name")

    if image_url:
        extracted_text = extract_text_from_drive_link(image_url)
        row = [name,json.dumps(extracted_text)]
        dest_sheet.append_row(row)
        return jsonify({"status": "success", "text": extracted_text})
    else:
        return jsonify({"status": "error", "message": "Missing image_url"}), 400

if __name__ == "__main__":
    app.run('0.0.0.0')
    


#ss = "https://drive.google.com/file/d/1Io4L0C5eGN2a4kgQJAoawYWNmtR0APqH/view"
#print(extract_text_from_drive_link(ss))

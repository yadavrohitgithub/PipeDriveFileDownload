import requests
import os
import json
from tqdm import tqdm
from pathvalidate import sanitize_filename
from dotenv import load_dotenv
import platform
import time

# Constants
BASE_URL = "https://api.pipedrive.com/v1/files"
PAGE_LIMIT = 100  # Max files per page per API docs
WIN_PREFIX = "\\\\?\\" if platform.system() == "Windows" else ""  # Windows long path support
SAVE_PATH = "./pipedrive-files"

# Load API_TOKEN from environment variables
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN not found in .env file")

# Create folder if it doesn't exist
os.makedirs(SAVE_PATH, exist_ok=True)

# File list is paginated
page = 0
while True:
    # Get and write page index
    index_path = os.path.join(SAVE_PATH, f"index_{page:04d}_files.json")
    if not os.path.exists(index_path):
        response = requests.get(
            f"{BASE_URL}?api_token={API_TOKEN}&start={page * PAGE_LIMIT}&limit={PAGE_LIMIT}"
        )
        if response.status_code != 200:
            print(f"Error fetching file list [Page {page}, Code {response.status_code}]: {response.text}")
            break
        files = response.json().get("data", [])
        with open(index_path, "w", encoding="utf-8") as json_file:
            json.dump(files, json_file, indent=4, ensure_ascii=False)
    else:
        with open(index_path, "r", encoding="utf-8") as json_file:
            files = json.load(json_file)

    # Get and write files
    if files:
        for file in tqdm(files, desc=f"Page {page:04d}", unit="file"):
            if file.get("remote_location") != "googledocs":
                file_id = file.get("id")
                file_deal = file.get("deal_id", 0)  # Default to 0 if deal_id is missing or None
                file_name = file.get("name", "unnamed_file")  # Default name if missing
                if file_id is None:
                    print(f"Skipping file with missing ID on page {page}")
                    continue
                if file_name is None:
                    file_name = "unnamed_file"
                file_name = sanitize_filename(file_name)
                # Ensure file_deal is an integer
                file_deal = int(file_deal) if file_deal is not None else 0
                file_name = f"{file_id:05d}_{file_deal:04d}_{file_name}"
                file_path = os.path.abspath(os.path.join(SAVE_PATH, file_name))
                if WIN_PREFIX:
                    file_path = f"{WIN_PREFIX}{file_path}"

                if not os.path.exists(file_path):
                    # Use the download endpoint
                    file_response = requests.get(
                        f"{BASE_URL}/{file_id}/download?api_token={API_TOKEN}"
                    )
                    if file_response.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(file_response.content)
                    else:
                        print(
                            f"\nError downloading {file_name} [Code {file_response.status_code}]: {file_response.text}"
                        )
                    time.sleep(0.1)  # Avoid rate limiting
    else:
        print("No files found.")
        break

    page += 1

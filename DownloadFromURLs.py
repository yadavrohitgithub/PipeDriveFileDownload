import requests
import os
from tqdm import tqdm
from pathvalidate import sanitize_filename
from dotenv import load_dotenv
import platform
import time

# Constants
WIN_PREFIX = "\\\\?\\" if platform.system() == "Windows" else ""  # Windows long path support
SAVE_PATH = "./downloaded-files"

# Load API_TOKEN from environment variables
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN not found in .env file")

# Create folder if it doesn't exist
os.makedirs(SAVE_PATH, exist_ok=True)

# List of URLs to download
URLS = [
"url1",
"url2"
]

# Download files
for url in tqdm(URLS, desc="Downloading files", unit="file"):
    # Extract file ID from URL
    try:
        file_id = url.split('/')[-2]  # Gets the file ID from URL (e.g., 12782)
        file_name = f"file_{file_id}"  # Default filename using file ID
        
        # Sanitize filename
        file_name = sanitize_filename(file_name)
        file_path = os.path.abspath(os.path.join(SAVE_PATH, file_name))
        if WIN_PREFIX:
            file_path = f"{WIN_PREFIX}{file_path}"

        # Check if file already exists
        if not os.path.exists(file_path):
            # Append API token to URL
            url_with_token = f"{url}?api_token={API_TOKEN}"
            
            # Download the file
            response = requests.get(url_with_token)
            if response.status_code == 200:
                # Try to get filename from Content-Disposition header if available
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition and 'filename=' in content_disposition:
                    # Extract filename from header
                    fname = content_disposition.split('filename=')[-1].strip('";')
                    file_name = sanitize_filename(fname)
                    file_path = os.path.abspath(os.path.join(SAVE_PATH, file_name))
                    if WIN_PREFIX:
                        file_path = f"{WIN_PREFIX}{file_path}"

                with open(file_path, "wb") as f:
                    f.write(response.content)
            else:
                print(f"\nError downloading {url} [Code {response.status_code}]: {response.text}")
            time.sleep(0.1)  # Avoid rate limiting
        else:
            print(f"\nFile {file_name} already exists, skipping.")
            
    except Exception as e:
        print(f"\nError processing {url}: {str(e)}")

print("Download complete.")

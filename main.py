import logging
import os
import shutil
import webbrowser
import zipfile
from datetime import datetime
from flask import jsonify

import deepl
from flask import Flask, redirect, render_template, request, send_file, url_for

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
LOG_FILE = 'log.txt'
PROCESSED_COUNT = 0

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)


auth_key = 'YOUR_AUTH_KEY_HERE'
translator = deepl.Translator(auth_key)


def process_zip(file):
  with zipfile.ZipFile(file, 'r') as zip_ref:
    zip_ref.extractall(QUEUE_FOLDER)
  log_to_file(f'Files Unzipped: {file}')


def log_to_file(message):
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  with open(LOG_FILE, 'a') as log:
    log.write(f'[{timestamp}] {message}\n')


def translate_and_upload_documents():
    translated_files = []
    output_folder = 'translated_files'  # Define the output folder for translated files
    with open(LOG_FILE, 'a') as log:
        for root, dirs, files in os.walk(QUEUE_FOLDER):
            for filename in files:
                input_path = os.path.join(root, filename)
                relative_path = os.path.relpath(input_path, QUEUE_FOLDER)
                output_path = os.path.join(output_folder, relative_path)
                output_dir = os.path.dirname(output_path)
                os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
                try:
                    # Translate the document
                    translator.translate_document_from_filepath(input_path,
                                                                output_path,
                                                                target_lang="EN-US")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log.write(
                        f"[{timestamp}] Translated '{filename}' and saved as '{output_path}'\n"
                    )
                    translated_files.append(output_path)  # Append translated file path to list
                except deepl.DocumentTranslationException as error:
                    # Handle translation errors
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log.write(
                        f"[{timestamp}] Error translating document '{filename}': {error}\n"
                    )
                except deepl.DeepLException as error:
                    # Handle other DeepL errors
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log.write(f"[{timestamp}] Error occurred: {error}\n")

    log_to_file('Translated files saved in folder: translated_files')

    return output_folder  # Return the name of the output folder
  

# Define the download route
def zip_translated_files():
  output_folder = 'translated_files'
  zip_file_name = 'translated_files.zip'
  with zipfile.ZipFile(zip_file_name, 'w') as zipf:
      for root, dirs, files in os.walk(output_folder):
          for file in files:
              zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), output_folder))
  return zip_file_name

@app.route('/download')
def download_file():
  zip_file_path = zip_translated_files()
  return send_file(zip_file_path, as_attachment=True)
  
@app.route('/')
def index():
    return render_template('index.html')




@app.errorhandler(Exception)
def handle_error(e):
    error_message = "An unexpected error occurred."
    # Log the error for debugging purposes
    logging.error(str(e))
    return jsonify({"error": error_message}), 500

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)

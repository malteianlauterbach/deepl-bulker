import logging
import os
import shutil
import webbrowser
import zipfile
from datetime import datetime

import deepl
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
LOG_FILE = 'log.txt'
QUEUE_FOLDER = 'queue'
OUTPUT_FOLDER = 'output'
PROCESSED_COUNT = 0

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(QUEUE_FOLDER):
  os.makedirs(QUEUE_FOLDER)

if not os.path.exists(OUTPUT_FOLDER):
  os.makedirs(OUTPUT_FOLDER)

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
  with open(LOG_FILE, 'a') as log:
      for root, dirs, files in os.walk(QUEUE_FOLDER):
          for filename in files:
              input_path = os.path.join(root, filename)
              relative_path = os.path.relpath(input_path, QUEUE_FOLDER)
              output_path = os.path.join(OUTPUT_FOLDER, relative_path)
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
                  error = handle_error(deepl.DeepLException)
      # Zip the translated files
      zip_file_name = 'output.zip'
      with zipfile.ZipFile(zip_file_name, 'w') as zipf:
          for file_path in translated_files:
              zipf.write(file_path, os.path.relpath(file_path, OUTPUT_FOLDER))
  
      log_to_file(f'Translated files zipped: {zip_file_name}')
  
  return zip_file_name  # Return the name of the zip file
  

# Define the download route
@app.route('/download')
def download_file():
  zip_file_path = translate_and_upload_documents()
  log_to_file(f'Translated files downloaded: {zip_file_path}')
  return send_file(zip_file_path, as_attachment=True)

@app.route('/submit', methods=['POST', 'GET'])
def submit_data():
    global PROCESSED_COUNT
    translated_files = []

    PROCESSED_COUNT = 0
    log_to_file("Data submission received. Resetting folders and zip file.")
    if os.path.exists(QUEUE_FOLDER):
        log_to_file(f"Emptying {QUEUE_FOLDER} directory.")
        shutil.rmtree(QUEUE_FOLDER)
    if os.path.exists(UPLOAD_FOLDER):
        log_to_file(f"Emptying {UPLOAD_FOLDER} directory.")
        shutil.rmtree(UPLOAD_FOLDER)
    if os.path.exists(OUTPUT_FOLDER):
        log_to_file(f"Emptying {OUTPUT_FOLDER} directory.")
        shutil.rmtree(OUTPUT_FOLDER)
    log_to_file("Creating empty directories.")
    os.makedirs(QUEUE_FOLDER)
    os.makedirs(UPLOAD_FOLDER)
    os.makedirs(OUTPUT_FOLDER)
    if os.path.exists('output.zip'):
        log_to_file("Removing existing output.zip file.")
        os.remove('output.zip')
    files = request.files.getlist('files')
    for file in files:
        filename = file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        log_to_file(f'File Written: {filename}')
        if filename.endswith('.zip'):
            process_zip(os.path.join(UPLOAD_FOLDER, filename))
        else:
            os.rename(os.path.join(UPLOAD_FOLDER, filename),
                      os.path.join(QUEUE_FOLDER, filename))
            log_to_file(f'File Moved to Queue: {filename}')
        PROCESSED_COUNT += 1
    log_to_file(f"Total count of processed files: {PROCESSED_COUNT}")
    translated_files = translate_and_upload_documents()

    return redirect(url_for('download_file'))
@app.route('/', methods=['GET'])

def index():
    return render_template('index.html')




@app.errorhandler(Exception)
def handle_error(e):
    error_message = "An unexpected error occurred."
    # Log the error for debugging purposes
    return jsonify({"error": error_message}), 500

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)

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
QUEUE_FOLDER = 'queue'
OUTPUT_FOLDER = 'output'
PROCESSED_COUNT = 0

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(QUEUE_FOLDER):
  os.makedirs(QUEUE_FOLDER)

if not os.path.exists(OUTPUT_FOLDER):
  os.makedirs(OUTPUT_FOLDER)

auth_key = '25f7e418-b8ee-4ee1-97e6-5b68253a90f2'
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

@app.route('/', methods=['GET', 'POST'])
def index():
    global PROCESSED_COUNT
    translated_files = []

    # Reset and empty folders and zip file on page reload
    if request.method == 'GET':
        PROCESSED_COUNT = 0
        log_to_file("Page reloaded. Resetting folders and zip file.")
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

    if request.method == 'POST':
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
        translated_files = translate_and_upload_documents(
        )  # Call translation function after processing files
        webbrowser.open_new_tab('/download'
                                )  # Open a new tab with the download route
        return redirect(url_for('download_file'))  # Redirect to the download route

    return render_template('index.html', translated_files=translated_files)




@app.errorhandler(Exception)
def handle_error(e):
    error_message = "An unexpected error occurred."
    # Log the error for debugging purposes
    logging.error(str(e))
    return jsonify({"error": error_message}), 500

if __name__ == '__main__':
  app.run(debug=True)

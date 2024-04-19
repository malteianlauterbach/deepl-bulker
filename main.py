import os
import zipfile
import deepl
from datetime import datetime
from flask import Flask, request, render_template, send_file, redirect, url_for
import webbrowser

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
  for root, dirs, files in os.walk(QUEUE_FOLDER):
    for filename in files:
      input_path = os.path.join(root, filename)
      output_path = os.path.join(OUTPUT_FOLDER, f"translated_{filename}")
      try:
        # Translate the document
        translator.translate_document_from_filepath(input_path,
                                                    output_path,
                                                    target_lang="EN-US")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_to_file(
            f"[{timestamp}] Translated '{filename}' and saved as 'translated_{filename}'\n"
        )
        translated_files.append(
            output_path)  # Append translated file path to list
      except deepl.DocumentTranslationException as error:
        # Handle translation errors
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_to_file(
            f"[{timestamp}] Error translating document '{filename}': {error}\n"
        )
      except deepl.DeepLException as error:
        # Handle other DeepL errors
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_to_file(f"[{timestamp}] Error occurred: {error}\n")
        print(f"Error occurred: {error}")  # Output error message to console
        log_to_file(
            f"[{timestamp}] Error occurred: {error}")  # Log error message

      if filename[-5:] not in [
          ".docx", ".doc", ".txt", ".xlsx", ".pdf", ".xliff", ".xlf", ".pptx",
          ".html"
      ]:
        print(f"Invalid file type detected: {filename}"
              )  # Output error message to console
        log_to_file(f"[{timestamp}] Invalid file type detected: {filename}"
                    )  # Log error message

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
    print(f"Total count of processed files: {PROCESSED_COUNT}")
    log_to_file(f'Total count of processed files: {PROCESSED_COUNT}')
    translated_files = translate_and_upload_documents(
    )  # Call translation function after processing files
    webbrowser.open_new_tab(
        '/download')  # Open a new tab with the download route
    return redirect(url_for('download_file'))  # Redirect to the download route

  return render_template('index.html', translated_files=translated_files)


if __name__ == '__main__':
  app.run(debug=True)

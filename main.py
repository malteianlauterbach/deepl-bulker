import os
import zipfile
import deepl
from datetime import datetime
from flask import Flask, request, render_template

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

auth_key = '25f7e418-b8ee-4ee1-97e6-5b68253a90f2'  # Replace with your DeepL API key
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
    for filename in os.listdir(QUEUE_FOLDER):
      input_path = os.path.join(QUEUE_FOLDER, filename)
      output_path = os.path.join(OUTPUT_FOLDER, f"translated_{filename}")
      try:
        # Translate the document
        translator.translate_document_from_filepath(input_path,
                                                    output_path,
                                                    target_lang="EN-US")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(
            f"[{timestamp}] Translated '{filename}' and saved as 'translated_{filename}'\n"
        )
        translated_files.append(
            output_path)  # Append translated file path to list
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
    zip_file_name = f"translated_files_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"
    with zipfile.ZipFile(zip_file_name, 'w') as zipf:
      for file_path in translated_files:
        zipf.write(file_path, os.path.basename(file_path))

    log_to_file(f'Translated files zipped: {zip_file_name}')

  return translated_files  # Return the list of translated files


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
    translated_files = translate_and_upload_documents(
    )  # Call translation function after processing files
  return render_template('index.html', translated_files=translated_files)


if __name__ == '__main__':
  app.run(debug=True)

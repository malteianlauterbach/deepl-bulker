import os
import zipfile
from datetime import datetime
from flask import Flask, request, render_template

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
LOG_FILE = 'log.txt'
QUEUE_FOLDER = 'queue'
PROCESSED_COUNT = 0

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(QUEUE_FOLDER):
  os.makedirs(QUEUE_FOLDER)


def process_zip(file):
  with zipfile.ZipFile(file, 'r') as zip_ref:
    zip_ref.extractall(QUEUE_FOLDER)
  log_to_file(f'Files Unzipped: {file}')


def log_to_file(message):
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  with open(LOG_FILE, 'a') as log:
    log.write(f'[{timestamp}] {message}\n')


@app.route('/', methods=['GET', 'POST'])
def index():
  global PROCESSED_COUNT
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
  return render_template('index.html')


if __name__ == '__main__':
  app.run(debug=True)

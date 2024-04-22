import os
import shutil
import zipfile
import logging
import deepl
from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime

app = Flask(__name__)
auth_key = 'YOUR_AUTH_KEY_HERE'
translator = deepl.Translator(auth_key)

UPLOADS_FOLDER = 'uploads'
OUTPUT_FOLDER = 'translated'
LOG_FILE = 'app.log'

app.config['UPLOADS_FOLDER'] = UPLOADS_FOLDER

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_dirs():
    if not os.path.exists(app.config['UPLOADS_FOLDER']):
        os.makedirs(app.config['UPLOADS_FOLDER'])
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

def unzip_file(file_path, extract_folder):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)

def translate_and_upload_documents():
    translated_files = []
    with open(LOG_FILE, 'a') as log:
        for root, dirs, files in os.walk(UPLOADS_FOLDER):
            for filename in files:
                input_path = os.path.join(root, filename)
                relative_path = os.path.relpath(input_path, UPLOADS_FOLDER)
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

        log.write(f'Translated files zipped: {zip_file_name}')

    return zip_file_name  # Return the name of the zip file

@app.route('/', methods=['GET', 'POST'])
def index():
    ensure_dirs()  # Ensure 'uploads' directory exists
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            error_message = "No file selected!"
            logging.error(error_message)
            return render_template('index.html', error=error_message)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            error_message = "No file selected!"
            logging.error(error_message)
            return render_template('index.html', error=error_message)
        if file:
            # Delete all old files in the 'uploads' folder
            for filename in os.listdir(app.config['UPLOADS_FOLDER']):
                file_path = os.path.join(app.config['UPLOADS_FOLDER'], filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        logging.info(f"Deleted old file: {filename}")
                except Exception as e:
                    logging.error(f"Error deleting file: {filename} - {e}")
            # Save the uploaded file
            filename = file.filename
            file_path = os.path.join(app.config['UPLOADS_FOLDER'], filename)
            file.save(file_path)
            logging.info(f"Uploaded file: {filename}")
            # Check if the uploaded file is a zip file
            if filename.endswith('.zip'):
                unzip_file(file_path, app.config['UPLOADS_FOLDER'])
                logging.info(f"Unzipped file: {filename}")
            # Translate and upload documents
            translated_zip_file = translate_and_upload_documents()
            return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

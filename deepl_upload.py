import os
import deepl
from datetime import datetime

auth_key = '25f7e418-b8ee-4ee1-97e6-5b68253a90f2'  # Replace with your DeepL API key
translator = deepl.Translator(auth_key)

QUEUE_FOLDER = 'queue'
LOG_FILE = 'translation_log.txt'
OUTPUT_FOLDER = 'output'

def translate_and_upload_documents():
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

        # Upload the translated document to your API or do further processing
        # Upload code goes here
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


if __name__ == "__main__":
  translate_and_upload_documents()

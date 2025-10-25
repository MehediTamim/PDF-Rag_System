import json
from pathlib import Path
from pdf2image import convert_from_path
import google.generativeai as genai
from config.settings import settings
from config.prompts import extraction_prompt
from utils.logger import Logger

logger = Logger.get_logger('pdf_extractor')


class GeminiPDFExtractor:
    def __init__(self, api_key=None):
        try:
            if api_key is None:
                api_key = settings.GEMINI_API_KEY
                if not api_key:
                    raise ValueError("API key required. Set GEMINI_API_KEY env variable or pass api_key parameter")

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
            self.extraction_prompt = extraction_prompt
            logger.info(f"Gemini PDF Extractor initialized with model: {settings.GEMINI_MODEL_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini PDF Extractor: {e}")
            raise

    def pdf_to_images(self, pdf_path, dpi=None):
        try:
            dpi = dpi or settings.PDF_DPI
            images = convert_from_path(pdf_path, dpi=dpi)
            logger.info(f"Converted PDF to {len(images)} images")
            return images
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise

    def extract_page(self, image, page_num):
        try:
            response = self.model.generate_content([
                self.extraction_prompt,
                image
            ])

            response_text = response.text.strip()

            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            content_blocks = json.loads(response_text)

            if not isinstance(content_blocks, list):
                content_blocks = [{"content": response_text, "data_type": "text"}]

            logger.debug(f"Extracted page {page_num} with {len(content_blocks)} content blocks")

            return {
                'page_number': page_num,
                'content_blocks': content_blocks
            }

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error on page {page_num}: {e}")
            return {
                'page_number': page_num,
                'content_blocks': [
                    {"content": response.text, "data_type": "text"}
                ]
            }
        except Exception as e:
            logger.error(f"Error extracting page {page_num}: {e}")
            return {
                'page_number': page_num,
                'content_blocks': [
                    {"content": f'[Error extracting page: {str(e)}]', "data_type": "text"}
                ]
            }

    def extract_pdf(self, pdf_path, output_json=None):
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            images = self.pdf_to_images(pdf_path)
            pages = []

            for i, image in enumerate(images, 1):
                page_data = self.extract_page(image, i)
                pages.append(page_data)

            result = {
                'pages': pages,
                'total_pages': len(images)
            }

            if output_json:
                output_path = Path(output_json)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"Extraction results saved to: {output_path}")

            logger.info(f"PDF extraction complete: {len(images)} pages")
            return result

        except Exception as e:
            logger.error(f"Error in extract_pdf: {e}")
            raise

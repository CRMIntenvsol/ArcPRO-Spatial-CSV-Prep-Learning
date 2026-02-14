# PDF to Markdown Converter Script Instructions

This script allows you to batch convert a folder of PDF files (including scanned ones) into Markdown format. It extracts text, tables, and uses OCR (Optical Character Recognition) for images.

## Prerequisites

1.  **Python 3.x:** Ensure Python is installed on your machine.
2.  **Tesseract OCR:** You must install the Tesseract OCR engine for scanned PDF support.
    *   **Windows:** Download the installer from [UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki). Add the installation path (e.g., `C:\Program Files\Tesseract-OCR`) to your system PATH environment variable.
    *   **Mac:** `brew install tesseract`
    *   **Linux:** `sudo apt-get install tesseract-ocr`

## Installation

Open your terminal or command prompt and install the required Python libraries:

```bash
pip install pdfplumber pytesseract Pillow tqdm
```

## How to Run

1.  Place all your PDF files in a single folder (e.g., `input_pdfs`).
2.  Create an empty folder for the output (e.g., `output_md`).
3.  Run the script:

```bash
python batch_pdf_to_md.py input_pdfs output_md
```

## Output

The script will generate a `.md` file for each PDF in the output directory.
-   **Text:** Extracted text from pages.
-   **Tables:** Simple Markdown tables.
-   **Scanned Text:** Extracted via OCR if the page is an image.

## Troubleshooting

-   **"Tesseract Not Found":** Make sure Tesseract is installed and added to your PATH. You may need to specify the path in the script: `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'` inside `batch_pdf_to_md.py`.
-   **Image Extraction:** Currently, the script focuses on text/table extraction. Complex charts are converted to text if possible or ignored if they are purely visual without embedded text.

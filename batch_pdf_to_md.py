import os
import sys
import argparse
import pdfplumber
import pytesseract
from PIL import Image
from tqdm import tqdm
import re

def clean_text(text):
    if not text:
        return ""
    # Remove excessive newlines and whitespace
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_page(page, page_num, image_output_dir, filename_base):
    md_content = []

    # 1. Try to extract text directly (Native PDF)
    text = page.extract_text()

    # 2. If little to no text found, try OCR (Scanned PDF)
    if not text or len(text.strip()) < 50:
        # Convert page to image for OCR
        im = page.to_image(resolution=300).original
        text = pytesseract.image_to_string(im)

    if text:
        md_content.append(clean_text(text))
        md_content.append("\n\n")

    # 3. Extract Tables
    tables = page.extract_tables()
    for table in tables:
        md_content.append(f"\n**Table found on Page {page_num}**\n")
        # Simple markdown table generation
        if table:
            # Header
            header = table[0]
            md_content.append("| " + " | ".join([str(c).replace('\n', ' ') if c else '' for c in header]) + " |")
            md_content.append("| " + " | ".join(['---'] * len(header)) + " |")
            # Rows
            for row in table[1:]:
                md_content.append("| " + " | ".join([str(c).replace('\n', ' ') if c else '' for c in row]) + " |")
            md_content.append("\n\n")

    # 4. Extract Images/Charts
    # Note: pdfplumber extracts image objects, but visual charts are often vector paths which are hard to extract as "images".
    # We will extract bitmap images found on the page.
    for i, img in enumerate(page.images):
        try:
            # Get image data
            # Note: This part can be tricky as pdfplumber provides image objects but not direct extraction methods easily.
            # A more robust way for images is using the page.to_image() snapshot if we want to capture the visual layout.
            # For this script, we will save the whole page as an image if it looks like a full-page chart/figure.
            pass
        except Exception as e:
            pass

    # As a fallback/feature: Save a snapshot of the page to assets if requested or if it looks like a figure
    # For now, let's keep it text-focused to keep the script simple and fast.

    return "".join(md_content)

def convert_pdf_to_md(pdf_path, output_dir):
    filename = os.path.basename(pdf_path)
    name_base = os.path.splitext(filename)[0]

    # Create directory for this PDF's assets (images)
    assets_dir = os.path.join(output_dir, "assets", name_base)
    os.makedirs(assets_dir, exist_ok=True)

    md_filename = os.path.join(output_dir, f"{name_base}.md")

    print(f"Processing {filename}...")

    full_md = [f"# {name_base}\n\n"]

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(tqdm(pdf.pages, desc="Pages", unit="pg")):
                page_content = process_page(page, i+1, assets_dir, name_base)
                full_md.append(f"## Page {i+1}\n\n")
                full_md.append(page_content)
                full_md.append("\n---\n\n")

        with open(md_filename, "w", encoding="utf-8") as f:
            f.write("".join(full_md))

        print(f"Saved Markdown to {md_filename}")

    except Exception as e:
        print(f"Error processing {filename}: {e}")

def get_input(prompt):
    """
    Robust input function that handles Windows paths and quotes.
    """
    val = input(prompt)
    # Remove surrounding quotes if user pasted path with quotes
    val = val.strip().strip('"').strip("'")
    return val

def main():
    if len(sys.argv) > 1:
        # Command line arguments provided
        parser = argparse.ArgumentParser(description="Batch convert PDFs to Markdown with OCR support.")
        parser.add_argument("input_dir", help="Directory containing PDF files")
        parser.add_argument("output_dir", help="Directory to save Markdown files")
        parser.add_argument("--tesseract_cmd", help="Path to Tesseract executable (optional)", default=None)
        args = parser.parse_args()

        input_dir = args.input_dir
        output_dir = args.output_dir
        tesseract_cmd = args.tesseract_cmd
    else:
        # Interactive mode
        print("Interactive Mode: Please enter the directory paths.")
        print("Note: You can paste Windows paths directly.")

        # Ask for Tesseract path
        print("\nOCR Configuration:")
        tesseract_cmd = get_input("Enter path to Tesseract executable (leave empty if in PATH): ")

        print("\nDirectories:")
        input_dir = get_input("Enter input directory containing PDFs: ")
        output_dir = get_input("Enter output directory for Markdown files: ")

    # Configure Tesseract
    if tesseract_cmd:
        if os.path.isfile(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            print(f"Using Tesseract at: {tesseract_cmd}")
        else:
            print(f"Warning: Tesseract executable not found at '{tesseract_cmd}'. Utilizing system PATH instead.")

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print("No PDF files found in the input directory.")
        sys.exit(0)

    print(f"Found {len(pdf_files)} PDF files. Starting conversion...")

    for pdf_file in pdf_files:
        convert_pdf_to_md(os.path.join(input_dir, pdf_file), output_dir)

    print("Batch conversion complete!")

if __name__ == "__main__":
    main()

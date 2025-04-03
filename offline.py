import fitz
import os
import tempfile
import shutil

PDF_DIR = os.path.join(os.getcwd(), "assets/pdf")
FONT_PATH = os.path.join(os.getcwd(), "assets/font/LexendDeca-Regular.ttf")
HEYGION_PDF = os.path.join(PDF_DIR, "HEYGION_HEALTH_REPORT.pdf")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

DEFAULT_NAME = "Prasid Mandal"
DEFAULT_COLLEGE_ID = "23/V/KPC-CST/36"

def estimate_text_width(text: str, fontsize: int, fontname: str) -> float:
    average_char_width = 0.6
    text_length = len(text) * average_char_width * fontsize
    return text_length

def edit_REPORT_pdf(name: str) -> str:
    name = name.upper()
    doc = fitz.open(HEYGION_PDF)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    output_pdf = temp_pdf.name

    pages_to_edit = [3, 9, 13, 17, 24, 31, 33]

    font_name = "LexendDeca"
    fontsize = 14

    for page_num, page in enumerate(doc):
        width, height = page.rect.width, page.rect.height
        page.insert_font(fontname=font_name, fontfile=FONT_PATH)

        if page_num in pages_to_edit:
            text_y = 700
            text_width = estimate_text_width(name, fontsize=fontsize, fontname=font_name)
            right_gap = 100
            adjusted_text_x = width - right_gap - text_width
            page.insert_text(
                (adjusted_text_x, text_y),
                name,
                fontsize=fontsize,
                color=(0, 0, 0),
                fontname=font_name,
                overlay=True
            )

    doc.save(output_pdf)
    doc.close()

    final_report_path = os.path.join(DOWNLOADS_DIR, "Health_Report_Generated.pdf")
    shutil.move(output_pdf, final_report_path)

    return final_report_path

def main():
    print("Welcome to the Health Report Generator!")

    name = input(f"Please enter your full name (default: {DEFAULT_NAME}): ").strip()
    if not name:
        name = DEFAULT_NAME
    name = ' '.join(word.capitalize() for word in name.split())

    college_id = input(f"Please enter your college ID (default: {DEFAULT_COLLEGE_ID}): ").strip()
    if not college_id:
        college_id = DEFAULT_COLLEGE_ID

    print(f"Generating your health report for {name}...")

    report_pdf_path = edit_REPORT_pdf(name)

    print(f"Health report PDF generated: {report_pdf_path}")
    print(f"Health report saved as: {os.path.basename(report_pdf_path)}")

if __name__ == "__main__":
    main()

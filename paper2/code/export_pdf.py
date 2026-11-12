import os
import win32com.client

word = win32com.client.Dispatch("Word.Application")
word.Visible = False
try:
    docx_path = os.path.abspath("paper2/draft/paper2_manuscript.docx")
    pdf_path = os.path.abspath("paper2/draft/paper2_manuscript.pdf")
    doc = word.Documents.Open(docx_path)
    page_count = doc.ComputeStatistics(2)
    print(f"Word COM Page Count: {page_count} pages")
    doc.SaveAs(pdf_path, 17) # 17 = wdFormatPDF
    doc.Close(False)
    print(f"Exported PDF successfully to {pdf_path} ({os.path.getsize(pdf_path):,} bytes)")
finally:
    word.Quit()

import os
import shutil
import win32com.client

word = win32com.client.Dispatch("Word.Application")
word.Visible = False
try:
    docx_path = os.path.abspath("draft/paper2_manuscript.docx" if os.path.exists("draft/paper2_manuscript.docx") else "paper2/draft/paper2_manuscript.docx")
    pdf_path = os.path.abspath("draft/paper2_manuscript.pdf" if os.path.exists("draft") else "paper2/draft/paper2_manuscript.pdf")
    doc = word.Documents.Open(docx_path)
    page_count = doc.ComputeStatistics(2)
    print(f"Word COM Page Count: {page_count} pages")
    doc.SaveAs(pdf_path, 17) # 17 = wdFormatPDF
    doc.Close(False)
    print(f"Exported PDF successfully to {pdf_path} ({os.path.getsize(pdf_path):,} bytes)")
    
    # Sync to clean_experiments_isolated
    target_pdf = os.path.abspath("clean_experiments_isolated/manuscript/paper2_manuscript.pdf")
    shutil.copyfile(pdf_path, target_pdf)
    print(f"Synchronized PDF to {target_pdf}")
finally:
    word.Quit()

"""Turn an uploaded file into plain text. Phase 0 supports .docx, .pdf, .txt, .md."""
import io

class UnsupportedFile(Exception):
    pass

def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".docx"):
        import docx
        d = docx.Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in d.paragraphs if p.text.strip())
    if name.endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n\n".join((pg.extract_text() or "") for pg in pdf.pages)
    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="ignore")
    raise UnsupportedFile("Upload a .docx, .pdf, .txt or .md file")

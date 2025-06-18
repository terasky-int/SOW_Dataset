from docx import Document
import os

def load_templates(template_dir: str = "templates") -> list:
    templates = []
    for filename in os.listdir(template_dir):
        if filename.endswith(".docx"):
            doc_path = os.path.join(template_dir, filename)
            doc = Document(doc_path)
            full_text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
            templates.append(full_text)
    return templates

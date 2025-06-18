import os
from difflib import SequenceMatcher
from typing import List, Tuple, Dict
from docx import Document
import json

TEMPLATE_DIR = "templates"
TEMPLATE_DB_PATH = "template_db.json"

def load_templates(template_dir: str = TEMPLATE_DIR) -> List[Dict]:
    templates = []
    for filename in os.listdir(template_dir):
        if filename.endswith(".docx"):
            doc_path = os.path.join(template_dir, filename)
            doc = Document(doc_path)
            full_text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
            templates.append({
                "template_name": filename,
                "content": full_text
            })
    return templates

def save_templates_to_db(templates: List[Dict], db_path: str = TEMPLATE_DB_PATH) -> None:
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2)

def load_templates_from_db(db_path: str = TEMPLATE_DB_PATH) -> List[Dict]:
    if not os.path.exists(db_path):
        return []
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_similar_to_any_template(chunk: str, templates: List[Dict], threshold: float = 0.9) -> Tuple[bool, float, str]:
    best_score = 0.0
    best_name = ""
    for template in templates:
        score = SequenceMatcher(None, chunk, template["content"]).ratio()
        if score > best_score:
            best_score = score
            best_name = template["template_name"]
    return best_score >= threshold, best_score, best_name

if __name__ == "__main__":
    # templates = load_templates()
    # save_templates_to_db(templates)
    # print(f"Saved {len(templates)} templates to {TEMPLATE_DB_PATH}")

    # Step 1: Load templates from DB
    templates = load_templates_from_db()
    print(f"Loaded {len(templates)} templates from {TEMPLATE_DB_PATH}")

    # Step 2: Test string — replace this with your real input later
    test_chunk = """
    This Scope of Work outlines the responsibilities of TeraSky to deliver consulting services
    for the implementation of cloud infrastructure, including setup, testing, and documentation.
    """

    # Step 3: Run the similarity check
    is_match, score, matched_template = is_similar_to_any_template(test_chunk, templates)

    # Step 4: Output the result
    print("MATCH RESULT")
    print("------------")
    print(f"Is template-like?      : {is_match}")
    print(f"Similarity score       : {score:.3f}")
    print(f"Matched template name  : {matched_template}")
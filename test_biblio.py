import asyncio
from services.docx_service import generate_docx_from_template

content = """# KIRISH
Test kirish

# FOYDALANILGAN ADABIYOTLAR RO'YXATI
[1] Test kitob"""

docx_bytes = generate_docx_from_template(content, 'Test Mavzu', 'Test Avtor', 'mustaqil', 'Test Uni')
with open('test_biblio.docx', 'wb') as f:
    f.write(docx_bytes)

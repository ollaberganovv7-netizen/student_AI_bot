import asyncio
from services.ai_service import generate_document_section
from services.docx_service import generate_docx_from_template

async def main():
    bib_title = "FOYDALANILGAN ADABIYOTLAR RO'YXATI"
    topic = "Kelajak askari"
    bib_count = "5-8"
    
    bib_text = await generate_document_section(
        topic=topic, 
        section_title=bib_title, 
        extra_details=(
            f"Mavzu bo'yicha kamida {bib_count} ta REAL ilmiy manbalarni yoz.\n"
            "TARKIBI:\n"
            "- 40% O'zbek mualliflari (O'zbekiston nashriyotlari: Fan, Iqtisod-Moliya, Sharq, TDIU). "
            "Masalan: Karimov A.K., Abdullayev B.M., Xo'jayev N.R. kabi.\n"
            "- 60% Xorijiy mualliflar (Pearson, McGraw-Hill, Cambridge, Springer). "
            "Masalan: Samuelson P., Mankiw G., Porter M. kabi.\n"
            "FORMAT: [1] Familiya I.O. Kitob nomi. - Shahar: Nashriyot, yil. - bet soni.\n"
            "Faqat ro'yxat ber, boshqa hech narsa qo'shma. Izoh yoki sarlavha yozma."
        ),
        language="uz",
        quality="standard",
        service_type="article"
    )
    
    print("AI OUTPUT:")
    print(bib_text)
    print("="*50)
    
    full_content = [f"# XULOSA\nXulosa text here", f"# {bib_title}\n\n{bib_text}"]
    content = "\n\n".join(full_content)
    
    docx_bytes = generate_docx_from_template(content, topic, "Test Avtor", "mustaqil")
    with open("test_full_generation.docx", "wb") as f:
        f.write(docx_bytes)

if __name__ == "__main__":
    asyncio.run(main())

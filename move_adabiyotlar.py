import os

path = r'services\ai_service.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

adabiyotlar_block = '''    # ── 4. ADABIYOTLAR slide (Slayd 5) ─────────────────────────
    if progress_callback:
        try: await progress_callback(completed_steps, total_steps, "Adabiyotlar ro'yxati...")
        except: pass

    a_prompt = (
        f"Mavzu: {topic}\\nTil: {language}\\n"
        "Ushbu mavzu bo'yicha AYNAN MAVZUGA MOS va ISHONCHLI 4-5 ta haqiqiy akademik adabiyotlar (kitoblar, darsliklar yoki ilmiy maqolalar, mualliflari va yili bilan) ro'yxatini shakllantiring.\\n"
        "Adabiyotlar to'qima bo'lmasin, soha bo'yicha nufuzli manbalar bo'lishi shart.\\n"
        "FAQAT JSON: {\\"content\\": [\\"1. Muallif. Kitob nomi. Yil\\", \\"2. ...\\"]}"
    )
    try:
        raw = await _call_ai([{"role": "user", "content": a_prompt}], max_tokens=1000, temperature=0.7, json_mode=True)
        a_data = json.loads(raw)
        
        q_content = a_data.get("content") or a_data.get("points")
        if not q_content:
            raise ValueError("No content found")
            
        slides_data.append({
            "title": "Foydalanilgan adabiyotlar",
            "content": q_content
        })
    except Exception:
        slides_data.append({"title": "Foydalanilgan adabiyotlar", "content": [
            "1. Oliy ta'lim muassasalari fan dasturi asosidagi o'quv adabiyotlari",
            "2. Mavzuga doir xalqaro va milliy ilmiy maqolalar",
            "3. Ziyonet.uz va milliy elektron kutubxona manbalari"
        ]})
    completed_steps += 1'''

# We want to remove this block from its current place and put it right before Rahmat slide
if adabiyotlar_block in content:
    content = content.replace(adabiyotlar_block, "")
    
    rahmat_target = '''    # ── 5. RAHMAT slide ───────────────────────────────────────'''
    new_adabiyotlar = adabiyotlar_block.replace("4. ADABIYOTLAR slide (Slayd 5)", "ADABIYOTLAR slide (Oxirida)")
    
    content = content.replace(rahmat_target, new_adabiyotlar + "\n\n" + rahmat_target)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Moved Adabiyotlar to the end")
else:
    print("FAILED: Could not find Adabiyotlar block")

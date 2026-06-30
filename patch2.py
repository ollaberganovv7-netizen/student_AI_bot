import os
import re

file_path = 'services/docx_service.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

def patch_junk_func(text, func_name):
    # Find the ALL-CAPS fallback block
    pattern = r'(if len\(clean_line\) < 120 and line\.strip\(\)\.isupper\(\):\n\s+def _norm\(t\): return re\.sub\(r\'\[\^A-Z0-9 \]\', \'\', t\)\n\s+tw = set\(_norm\(topic_upper\)\.split\(\)\)\n\s+lw = set\(_norm\(clean_line\)\.split\(\)\)\n\s+match_count = sum\(1 for t_word in tw if any\(t_word in l_word or l_word in t_word for l_word in lw\)\)\n\s+if tw and match_count >= len\(tw\) \* 0\.5: return True)'
    
    replacement = r'''\1
            
            stripped_sec_for_fallback = re.sub(r'^\d+(?:\.\d+)*\.*\-?\s*', '', clean_sec).strip()
            sw = set(_norm(stripped_sec_for_fallback).split())
            match_count_sec = sum(1 for s_word in sw if any(s_word in l_word or l_word in s_word for l_word in lw))
            if len(sw) > 1 and match_count_sec >= len(sw) * 0.5: return True'''
            
    return re.sub(pattern, replacement, text)

new_text = patch_junk_func(text, "_is_junk_for_docx")

if text != new_text:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Successfully patched docx_service.py")
else:
    print("Failed to patch or already patched.")

import os

path = os.path.join(r'C:\Users\Шухрат\Desktop\Новая папка\student_AI_bot', 'services', 'pptx_service.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the old calls with new premium design calls
old_block = '''    # \u2728\u2728 3. Unique Design, Animations & Save \u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728
    try:
        apply_unique_ai_design(prs)
        apply_modern_animations(prs)
    except Exception as e:
        pass  # non-critical'''

new_block = '''    # \u2728\u2728 3. Premium Design & Professional Transitions \u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728\u2728
    try:
        from services.premium_design import apply_premium_design, apply_premium_transitions
        apply_premium_design(prs, topic)
        apply_premium_transitions(prs)
    except Exception as e:
        pass  # non-critical'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: pptx_service.py updated')
else:
    print('WARNING: exact block not found, trying alternative...')
    # Try to find the section with a more flexible match
    import re
    pattern = r"(    # .* 3\. Unique Design.*?\n    try:\n        apply_unique_ai_design\(prs\)\n        apply_modern_animations\(prs\)\n    except.*?pass.*?# non-critical)"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content.replace(match.group(0), new_block)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('SUCCESS: pptx_service.py updated (alt method)')
    else:
        # Most flexible: just replace the function calls
        content = content.replace('apply_unique_ai_design(prs)', 
            'from services.premium_design import apply_premium_design, apply_premium_transitions; apply_premium_design(prs, topic)')
        content = content.replace('apply_modern_animations(prs)', 'apply_premium_transitions(prs)')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('SUCCESS: pptx_service.py updated (inline method)')

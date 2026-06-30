import os

path = r"services\pptx_service.py"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = '''    try:
        apply_unique_ai_design(prs)
        apply_modern_animations(prs)
    except Exception as e:
        pass  # non-critical'''

new_code = '''    try:
        from services.premium_design import apply_premium_design, apply_premium_transitions
        apply_premium_design(prs, topic)
        apply_premium_transitions(prs)
    except Exception as e:
        import traceback
        print("Premium Design Error:", e)
        traceback.print_exc()
        pass  # non-critical'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Replaced design function calls in pptx_service.py")
else:
    print("FAILED: Could not find exact block")

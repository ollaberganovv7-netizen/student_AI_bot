from __future__ import annotations
from services.pptx_service import analyze_template
import json

res = analyze_template("templates/power point/test.pptx")
print(json.dumps(res, indent=2))

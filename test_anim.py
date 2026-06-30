import os
from pptx import Presentation
from pptx.oxml import parse_xml

prs = Presentation('doc_templates/Taqdimot 1.pptx')
for slide in prs.slides:
    transition_xml = '<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" spd="med"><p:fade/></p:transition>'
    transition_element = parse_xml(transition_xml)
    # Insert transition tag right after <p:cSld>
    # cSld is always first in p:sld
    slide._element.insert(1, transition_element)

prs.save('test_anim.pptx')
print("Saved with animations!")

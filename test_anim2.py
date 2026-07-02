import xml.etree.ElementTree as ET

def build_anim_xml(shape_ids):
    timing = ET.Element('{http://schemas.openxmlformats.org/presentationml/2006/main}timing')
    tnLst = ET.SubElement(timing, '{http://schemas.openxmlformats.org/presentationml/2006/main}tnLst')
    par1 = ET.SubElement(tnLst, '{http://schemas.openxmlformats.org/presentationml/2006/main}par')
    cTn1 = ET.SubElement(par1, '{http://schemas.openxmlformats.org/presentationml/2006/main}cTn', {'id': '1', 'dur': 'indefinite', 'restart': 'never', 'nodeType': 'tmRoot'})
    childTnLst1 = ET.SubElement(cTn1, '{http://schemas.openxmlformats.org/presentationml/2006/main}childTnLst')
    seq = ET.SubElement(childTnLst1, '{http://schemas.openxmlformats.org/presentationml/2006/main}seq', {'concurrent': '1', 'nextAc': 'seek'})
    cTn2 = ET.SubElement(seq, '{http://schemas.openxmlformats.org/presentationml/2006/main}cTn', {'id': '2', 'dur': 'indefinite', 'nodeType': 'mainSeq'})
    main_childTnLst = ET.SubElement(cTn2, '{http://schemas.openxmlformats.org/presentationml/2006/main}childTnLst')

    current_id = 3
    for spid in shape_ids:
        par2 = ET.SubElement(main_childTnLst, '{http://schemas.openxmlformats.org/presentationml/2006/main}par')
        cTn3 = ET.SubElement(par2, '{http://schemas.openxmlformats.org/presentationml/2006/main}cTn', {'id': str(current_id), 'fill': 'hold'})
        stCondLst1 = ET.SubElement(cTn3, '{http://schemas.openxmlformats.org/presentationml/2006/main}stCondLst')
        ET.SubElement(stCondLst1, '{http://schemas.openxmlformats.org/presentationml/2006/main}cond', {'delay': 'indefinite'})
        childTnLst2 = ET.SubElement(cTn3, '{http://schemas.openxmlformats.org/presentationml/2006/main}childTnLst')
        
        par3 = ET.SubElement(childTnLst2, '{http://schemas.openxmlformats.org/presentationml/2006/main}par')
        cTn4 = ET.SubElement(par3, '{http://schemas.openxmlformats.org/presentationml/2006/main}cTn', {'id': str(current_id+1), 'fill': 'hold'})
        stCondLst2 = ET.SubElement(cTn4, '{http://schemas.openxmlformats.org/presentationml/2006/main}stCondLst')
        ET.SubElement(stCondLst2, '{http://schemas.openxmlformats.org/presentationml/2006/main}cond', {'delay': '0'})
        childTnLst3 = ET.SubElement(cTn4, '{http://schemas.openxmlformats.org/presentationml/2006/main}childTnLst')
        
        par4 = ET.SubElement(childTnLst3, '{http://schemas.openxmlformats.org/presentationml/2006/main}par')
        cTn5 = ET.SubElement(par4, '{http://schemas.openxmlformats.org/presentationml/2006/main}cTn', {
            'id': str(current_id+2), 'presetID': '10', 'presetClass': 'entr', 'presetSubtype': '0', 'fill': 'hold', 'nodeType': 'clickEffect'
        }) # presetID 10 is Fade
        stCondLst3 = ET.SubElement(cTn5, '{http://schemas.openxmlformats.org/presentationml/2006/main}stCondLst')
        ET.SubElement(stCondLst3, '{http://schemas.openxmlformats.org/presentationml/2006/main}cond', {'delay': '0'})
        childTnLst4 = ET.SubElement(cTn5, '{http://schemas.openxmlformats.org/presentationml/2006/main}childTnLst')
        
        set_node = ET.SubElement(childTnLst4, '{http://schemas.openxmlformats.org/presentationml/2006/main}set')
        cBhvr = ET.SubElement(set_node, '{http://schemas.openxmlformats.org/presentationml/2006/main}cBhvr')
        cTn6 = ET.SubElement(cBhvr, '{http://schemas.openxmlformats.org/presentationml/2006/main}cTn', {'id': str(current_id+3), 'dur': '1', 'fill': 'hold'})
        stCondLst4 = ET.SubElement(cTn6, '{http://schemas.openxmlformats.org/presentationml/2006/main}stCondLst')
        ET.SubElement(stCondLst4, '{http://schemas.openxmlformats.org/presentationml/2006/main}cond', {'delay': '0'})
        tgtEl = ET.SubElement(cBhvr, '{http://schemas.openxmlformats.org/presentationml/2006/main}tgtEl')
        ET.SubElement(tgtEl, '{http://schemas.openxmlformats.org/presentationml/2006/main}spTgt', {'spid': str(spid)})
        attrNameLst = ET.SubElement(cBhvr, '{http://schemas.openxmlformats.org/presentationml/2006/main}attrNameLst')
        attrName = ET.SubElement(attrNameLst, '{http://schemas.openxmlformats.org/presentationml/2006/main}attrName')
        attrName.text = 'style.visibility'
        
        to_node = ET.SubElement(set_node, '{http://schemas.openxmlformats.org/presentationml/2006/main}to')
        ET.SubElement(to_node, '{http://schemas.openxmlformats.org/presentationml/2006/main}strVal', {'val': 'visible'})
        
        current_id += 4
        
    return timing

xml_str = ET.tostring(build_anim_xml([5, 6, 7]), encoding='unicode')
print(xml_str)

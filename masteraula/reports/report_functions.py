import re

def apply_regex_program(regex, sub_string, status_string, all_ids, all_texts, force_stay=False):
    program = re.compile(regex)
    clean = []
    texts = []
    ids = []
    status = []

    for _id, text in zip(all_ids, all_texts):
        has = False
        clean_text = text

        while(program.search(clean_text)):
            has = True
            clean_text = program.sub(sub_string, clean_text)
        if has or force_stay:
            ids.append(_id)
            texts.append(text)
            clean.append(clean_text)
            status.append(status_string if has else '')
    return ids, texts, clean, status

def process_tags_p_space(all_ids, all_texts, force_stay=False, get_status=False):
    program = '</p><p>'

    ids, texts, clean, status = apply_regex_program(program, '</p>\n<p>', 'Given spaces between tags <p>', all_ids, all_texts, force_stay)

    if get_status:
        return ids, texts, clean, status
    return ids, texts, clean
    
def process_tags_div(all_ids, all_texts, force_stay=False, get_status=False):
    program1 = '<div[^<]*>(.*?)<\/div>'         
    program2 = '<div[^<]*>'

    ids, texts, clean, status = apply_regex_program(program1, '<p>\\1</p>', 'Removed <div>', all_ids, all_texts, force_stay)
    _, _, clean, _ = apply_regex_program(program2, '', '', ids, clean, True)

    if get_status:
        return (ids, texts, clean, status)
    return ids, texts, clean

def process_tags_br_inside_p(all_ids, all_texts, force_stay=False, get_status=False):
    program = '(<p((?!</p>)[\s\S])*>((?!</p>)[\s\S])*)(<[\/\s]*?br[\/\s]*?>)([\s\S]*?<\/p>)'

    ids, texts, clean, status = apply_regex_program(program, '\\1 </p><p> \\5', 'Removed <br> inside <p>', all_ids, all_texts, force_stay)

    if get_status:
        return (ids, texts, clean, status)
    return ids, texts, clean

def process_tags_p_inside_p(all_ids, all_texts, force_stay=False, get_status=False):
    program = '(<p[^>]*?>((?!<\/p>)[\s\S])*?)<p[^>]*?>([\s\S]*?)<\/p>'

    ids, texts, clean, status = apply_regex_program(program, '\\1 </p><p> \\3', 'Removed <p> inside <p>', all_ids, all_texts, force_stay)

    if get_status:
        return ids, texts, clean, status
    return ids, texts, clean

def process_empty_p_tags(all_ids, all_texts, force_stay=False, get_status=False):
    program = '<p[^>]*?>\s*</p>'

    ids, texts, clean, status = apply_regex_program(program, '', 'Removed empty <p>', all_ids, all_texts, force_stay)

    if get_status:
        return ids, texts, clean, status
    return ids, texts, clean

def process_tags_texto_associado_inside_p(all_ids, all_texts, force_stay=False, get_status=False):
    program = '<p[^<]*texto_associado_questao[^<]*>([\s\S]*?)<\/p>'
    
    ids, texts, clean, status = apply_regex_program(program, '<p>\\1</p>', 'Replace texto_associado_questao', all_ids, all_texts, force_stay)

    if get_status:
        return ids, texts, clean, status
    return ids, texts, clean

def process_line_heigth(all_ids, all_texts, force_stay=False, get_status=False):
    program = '<span[^<]*line-height ?:[^<]*>([\s\S]*?)<\/span>'
    
    ids, texts, clean, status = apply_regex_program(program, '<p>\\1</p>', 'Remove line heigth', all_ids, all_texts, force_stay)

    if get_status:
        return ids, texts, clean, status
    return ids, texts, clean

def process_super_sub(all_ids, all_texts, force_stay=False, get_status=False):
    program_super = re.compile('<span[^<]*vertical-align ?: ?super[^<]*>([\s\S]*?)<\/span>')
    program_sub = re.compile('<span[^<]*vertical-align ?: ?sub[^<]*>([\s\S]*?)<\/span>')

    clean = []
    texts = []
    ids = []
    status = []

    for _id, text in zip(all_ids, all_texts):
        has = False
        clean_text = text

        while program_super.search(clean_text):
            has = True
            clean_text = program_super.sub('<sup>\\1</sup>', clean_text)

        while program_sub.search(clean_text):
            has = True
            clean_text = program_sub.sub('<sub>\\1</sub>', clean_text)
        
        if has or force_stay:
            ids.append(_id)
            texts.append(text)
            clean.append(clean_text)
            status.append('Got Sup or Sub' if has else '')
    if get_status:
        return ids, texts, clean, status
    return ids, texts, clean

def process_bold_italic(all_ids, all_texts, force_stay=False, get_status=False):
    program_bold = re.compile('<span[^<]*font-weight ?: ?bold[^<]*>([\s\S]*?)<\/span>')
    program_italic = re.compile('<span[^<]*font-style ?: ?italic[^<]*>([\s\S]*?)<\/span>')

    clean = []
    texts = []
    ids = []
    status = []

    for _id, text in zip(all_ids, all_texts):
        has = False
        clean_text = text

        # bold first
        match = program_bold.search(clean_text)
        while match:
            has = True
            if program_italic.search(match.group(0)):
                clean_text = program_bold.sub('<strong><em>\\1</em></strong>', clean_text)
            else:
                clean_text = program_bold.sub('<strong>\\1</strong>', clean_text)
            match = program_bold.search(clean_text)

        while program_italic.search(clean_text):
            has = True
            clean_text = program_italic.sub('<em>\\1</em>', clean_text)
        
        if has or force_stay:
            ids.append(_id)
            texts.append(text)
            clean.append(clean_text)
            status.append('Got Strong or Em' if has else '')
    if get_status:
        return ids, texts, clean, status
    return ids, texts, clean
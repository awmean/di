import re


def format_text(text):
    if not text:
        return ""

    # 1. Жирный текст **text** -> <strong class="desc-strong">text</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong class="desc-strong">\1</strong>', text)

    # 2. Переносы строк \n -> <br>
    text = text.replace('\n', '<br>')

    # 3. Обработка заголовков и списков
    lines = text.split('<br>')
    formatted_lines = []
    in_list = False

    for line in lines:
        stripped_line = line.strip()

        # Заголовки первого уровня # text -> <h1 class="desc-h1">text</h1>
        if stripped_line.startswith('# '):
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            header_text = stripped_line[2:].strip()
            formatted_lines.append(f'<div class="desc-h1">{header_text}</div>')

        # Списки - строки, начинающиеся с "- " или "• "
        elif stripped_line.startswith('- ') or stripped_line.startswith('• '):
            if not in_list:
                formatted_lines.append('<ul class="desc-ul">')
                in_list = True
            # Убираем "- " или "• " и оборачиваем в <li>
            item_text = stripped_line[2:].strip()
            formatted_lines.append(f'<li class="desc-li">{item_text}</li>')

        # Обычные строки
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            # Добавляем все строки, включая пустые (для переносов)
            formatted_lines.append(line if line.strip() else '')

    # Закрываем список если он остался открытым
    if in_list:
        formatted_lines.append('</ul>')

    return '<br>'.join(formatted_lines)

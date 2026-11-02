import xml.etree.ElementTree as ET
from pathlib import Path

# TXT 파일 읽기 및 공백 정리
project_root = Path(__file__).resolve().parent.parent
text_path = project_root / 'data' / 'sample.txt'
with text_path.open('r', encoding='utf-8') as f:
    lines = [line.strip() for line in f]

categories = [
    'Characters',
    'Creatures',
    'Droids',
    'Locations',
    'Organizations',
    'Vehicles',
    'Character Specific'
]

# 분류 제목과 빈 줄을 기준으로 항목 구분
text = []
current_category = None
current_entry = []

for line in lines:
    if line in categories:
        if current_entry:
            text.append({'category': current_category, 'entry': current_entry})
            current_entry = []
        current_category = line
    elif line == '':
        if current_entry:
            text.append({'category': current_category, 'entry': current_entry})
            current_entry = []
    else:
        current_entry.append(line)

if current_entry:
    text.append({'category': current_category, 'entry': current_entry})

# 일반 항목과 인물 관계 데이터 분리
entry_data = []
relation_data = []
relation_line_count = 0

for item in text:
    name = item['entry'][0]
    if item['category'] != 'Character Specific':
        description = ' '.join(item['entry'][1:-1])
        source = item['entry'][-1].split(':', 1)[1].strip()
        entry_data.append({
            'category': item['category'],
            'name': name,
            'description': description,
            'source': source
        })
    else:
        for relation in item['entry'][1:]:
            relation_line_count += 1
            relation_type, targets = relation.split(':', 1)
            relation_type = relation_type.strip()
            for target in targets.split(','):
                target = target.strip()
                relation_data.append({
                    'character': name,
                    'type': relation_type,
                    'target': target
                })

# XML 구조화
root = ET.Element(
    'star_wars_encyclopedia',
    attrib={'version': '1.0'}
)
entries = ET.SubElement(root, 'entries')
character_specific = ET.SubElement(root, 'character_specific')

category_elements = {}
for name in categories:
    if name != 'Character Specific':
        category_element = ET.SubElement(
            entries,
            'category',
            {'name': name}
        )
        category_elements[name] = category_element

for entry in entry_data:
    category_element = category_elements[entry['category']]
    entry_element = ET.SubElement(category_element, 'entry')
    entry_element.set(
        'id',
        f'{entry["category"].lower()}-{len(category_element):03d}'
    )
    ET.SubElement(entry_element, 'name').text = entry['name']
    ET.SubElement(entry_element, 'description').text = entry['description']
    ET.SubElement(
        entry_element,
        'source',
        {'name': 'Star Wars Databank', 'url': entry['source']}
    )

character_elements = {}
for relation in relation_data:
    name = relation['character']
    if name not in character_elements:
        specific_element = ET.SubElement(
            character_specific,
            'character',
            {'name': name}
        )
        character_elements[name] = specific_element
    ET.SubElement(
        character_elements[name],
        'relation',
        {'type': relation['type'], 'target': relation['target']}
    )

# XML 저장
tree = ET.ElementTree(root)
ET.indent(tree, space='\t')
output_path = project_root / 'data' / 'starwars.xml'
tree.write(
    output_path,
    encoding='utf-8',
    xml_declaration=True,
)

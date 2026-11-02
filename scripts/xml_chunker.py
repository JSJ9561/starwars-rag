import xml.etree.ElementTree as ET
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
xml_path = project_root / 'data' / 'starwars.xml'
tree = ET.parse(xml_path)
root = tree.getroot()
entries = root.find('entries')
character_specific = root.find('character_specific')

# 청킹
chunks = []
for category in entries.findall('category'):
    category_name = category.get('name')
    for entry in category.findall('entry'):
        entry_id = entry.get('id')
        entry_name = entry.findtext('name')
        entry_description = entry.findtext('description')
        entry_source_url = entry.find('source').get('url')
        chunks.append({
            'id': entry_id,
            'category': category_name,
            'name': entry_name,
            'text': f'{entry_name}\n{entry_description}',
            'source_url': entry_source_url
        })

for relation_index, character in enumerate(character_specific.findall('character'), start=1):
    relation_lines = []
    specific_name = character.get('name')
    for relation in character.findall('relation'):
        relation_type = relation.get('type')
        relation_target = relation.get('target')
        relation_lines.append(f'{relation_type}: {relation_target}')
    relation_text = '\n'.join(relation_lines)

    chunks.append({
        'id': f'relations-{relation_index:03d}',
        'category': 'Character Specific',
        'name': specific_name,
        'text': f'{specific_name}\n{relation_text}',
        'source_url': None
    })

# JSON 저장
json_path = project_root / 'data' / 'chunks.json'

with json_path.open('w', encoding='utf-8') as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

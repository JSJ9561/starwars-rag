import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

# JSON에서 텍스트 추출
project_root = Path(__file__).resolve().parent.parent
json_path = project_root / 'data' / 'chunks.json'

with json_path.open('r', encoding='utf-8') as f:
    chunks = json.load(f)

texts = []
for item in chunks:
    texts.append(item['text'])

# 기존 임베딩 파일 확인
npy_path = project_root / 'data' / 'embeddings.npy'

if npy_path.exists():
    print('임베딩 파일이 이미 존재합니다. 작업을 종료합니다.')
    raise SystemExit(0)

# 모델 불러오기
model = SentenceTransformer(
    'BAAI/bge-m3',
    device = 'xpu',
    cache_folder='models'
)

# 전체 청크 임베딩
embeddings = model.encode(
    texts,
    batch_size=8,
    show_progress_bar=True,
    convert_to_numpy=True
)

# 임베딩 저장
npy_path = project_root / 'data' / 'embeddings.npy'
np.save(npy_path, embeddings)

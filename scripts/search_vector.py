import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

# 인덱스, JSON 불러오기
project_root = Path(__file__).resolve().parent.parent
json_path = project_root / 'data' / 'chunks.json'
faiss_path = project_root / 'data' / 'starwars.index'

with json_path.open('r', encoding='utf-8') as f:
    chunks = json.load(f)

index = faiss.deserialize_index(
    np.frombuffer(faiss_path.read_bytes(), dtype=np.uint8)
)

# 모델 불러오기
model = SentenceTransformer(
    'BAAI/bge-m3',
    device = 'xpu',
    cache_folder=str(project_root / 'models')
)

# 테스트 질문 임베딩
'''
예시 질문
"Who is Anakin Skywalker's mentor?"
"아나킨 스카이워커의 스승은 누구야?"
"파드메 아미달라의 고향 행성은 어디야?"
"팰퍼틴 의장과 다스 시디어스는 같은 인물이야?"
"파드메 아미달라의 정확한 생년월일은 언제야?"
'''
# 사용자 질문 입력
query = input('질문: ').strip()

query_embedding = model.encode(
    query,
    batch_size=1,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)
query_embedding = query_embedding.astype(np.float32).reshape(1, -1)

# Top-k 설정
k = 3
scores, indices = index.search(query_embedding, k)

# 검색 결과와 원본 청크 연결
for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1):
    chunk = chunks[int(idx)]

    print(f'\n검색 순위: {rank}')
    print(f'유사도: {score:.4f}')
    print(f'이름: {chunk["name"]}')
    print(f'분류: {chunk["category"]}')
    print(f'본문: {chunk["text"]}')
    print(f'출처: {chunk["source_url"] or "없음"}')

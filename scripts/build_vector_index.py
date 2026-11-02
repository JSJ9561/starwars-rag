import json
import numpy as np
import faiss
from pathlib import Path

# JSON, npy 불러오기
project_root = Path(__file__).resolve().parent.parent
json_path = project_root / 'data' / 'chunks.json'
npy_path = project_root / 'data' / 'embeddings.npy'

with json_path.open('r', encoding='utf-8') as f:
    chunks = json.load(f)

embeddings = np.load(npy_path)

# FAISS 인덱스 생성 및 등록
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)

# FAISS 인덱스 저장
faiss_path = project_root / 'data' / 'starwars.index'
faiss_path.write_bytes(faiss.serialize_index(index).tobytes())


loaded_index = faiss.deserialize_index(
    np.frombuffer(faiss_path.read_bytes(), dtype=np.uint8)
)

print(loaded_index.d)
print(loaded_index.ntotal)
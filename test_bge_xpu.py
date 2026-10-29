import torch
from sentence_transformers import SentenceTransformer

assert torch.xpu.is_available(), "XPU를 사용할 수 없습니다."

# BGE-M3 모델 로딩
model = SentenceTransformer(
    "BAAI/bge-m3",
    device="xpu",
    cache_folder="models"
)

# 한국어 및 영어 문장 임베딩
texts = [
    "Anakin Skywalker comes from Tatooine.",
    "아나킨 스카이워커의 고향은 타투인이다."
]

embeddings = model.encode(
    texts,
    batch_size=1,
    normalize_embeddings=True,
    show_progress_bar=False
)

print("Device:", model.device)
print("Embedding shape:", embeddings.shape)
print("Similarity:", float(embeddings[0] @ embeddings[1]))

assert str(model.device).startswith("xpu")
assert embeddings.shape == (2, 1024)

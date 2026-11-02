# Star Wars Episode III RAG Chatbot

**Star Wars: Episode III – Revenge of the Sith**를 중심으로 구축하는 RAG(Retrieval-Augmented Generation) 기반 AI 백과사전 챗봇 프로젝트입니다.

스타워즈의 인물, 생물, 드로이드, 장소, 조직, 탈것 등의 정보를 구조화하고, 사용자가 자연어로 질문하면 관련 문서를 검색하여 답변하는 챗봇 구현을 목표로 합니다.

## 1. 프로젝트 개요

본 프로젝트는 대학 수업에서 학습한 자연어 처리(NLP), 사전학습 언어모델(PLM), 임베딩 및 생성형 AI 기술을 실제 서비스 형태로 구현하기 위한 프로젝트입니다.

**주요 목표**

- 스타워즈 에피소드 III 중심의 백과사전 데이터 구축
- TXT 데이터를 XML 형태로 구조화
- 문서 청킹 및 BGE-M3 텍스트 임베딩
- FAISS 기반 의미 검색
- 검색 결과를 활용한 RAG 답변 생성
- HTML 기반 웹 챗봇 인터페이스 구현

## 2. 데이터 구성

Star Wars 공식 Databank의 설명을 참고하여 에피소드 III 관련 데이터를 정리했습니다.

| Category | Records |
|---|---:|
| Characters | 63 |
| Creatures | 3 |
| Droids | 18 |
| Locations | 20 |
| Organizations | 17 |
| Vehicles | 21 |
| **Total** | **142** |

이와 별도로 `Character Specific` 영역에 주요 인물 9명의 관계 정보를 정리했습니다. 관계 데이터는 총 39개의 개별 관계로 구성되며, `mentor`, `apprentice`, `affiliation`, `homeworld`, `spouse`, `child`, `same_person_as` 등의 속성을 포함합니다.

일반 백과사전 항목은 항목별로 하나의 청크를 생성하고, 인물 관계는 인물별로 하나의 청크를 생성했습니다. **최종 청크 수는 151개(일반 항목 142개 + 인물 관계 9개)**입니다.

데이터는 에피소드 III를 중심으로 선정했지만, 개별 설명에는 다른 에피소드와 관련된 내용도 포함될 수 있습니다.

원본 데이터 및 가공 데이터는 저작권을 고려하여 공개 Git 저장소에 포함하지 않습니다. XML 구조와 청킹 규칙은 [`docs/xml-schema.md`](docs/xml-schema.md)를 참고하세요.

## 3. 기술 스택

| 구분 | 기술 | 상태 |
|---|---|---|
| Language | Python 3.12 | 사용 중 |
| Deep Learning | PyTorch 2.15.0+xpu | Intel XPU 환경 검증 완료 |
| Embedding | BAAI/bge-m3 | 151개 청크 임베딩 완료 |
| Embedding Library | SentenceTransformers 6.2.0 | 사용 중 |
| GPU Acceleration | Intel XPU / NVIDIA CUDA | XPU 테스트 및 CUDA 임베딩 수행 |
| Vector Search | FAISS (`IndexFlatIP`, `faiss-cpu`) | 인덱스 생성 및 저장 완료 |
| Backend | FastAPI | 도입 예정 |
| Frontend | HTML / CSS / JavaScript | 구현 예정 |
| LLM | 외부 API 기반 모델 검토 | 미정 |
| Version Control | Git / GitHub | 구성 완료 |

## 4. 시스템 아키텍처

본 프로젝트의 RAG 파이프라인은 다음과 같습니다.

**데이터 구축 과정 (1단계 완료)**

```text
TXT → XML → JSON Chunking → BGE-M3 Embedding → FAISS IndexFlatIP
```

- `chunks.json`: 청크 본문과 식별자, 분류, 이름, 출처 URL 저장
- `embeddings.npy`: 151 × 1024 크기의 임베딩 벡터 저장
- `starwars.index`: 151개 벡터를 등록한 FAISS 검색 인덱스 저장
- FAISS 검색 결과의 벡터 번호를 `chunks.json`의 항목 순서와 연결하여 원문과 출처를 확인하는 구조

**질문 처리 과정 (구현 예정)**

```text
User Question → BGE-M3 Query Embedding → FAISS Top-k Search
              → Context Retrieval → LLM → Answer
```

검색된 문서를 LLM의 입력 문맥으로 제공하여 데이터에 근거한 답변 생성을 목표로 합니다. 실제 질문의 검색 정확도와 한국어 고유명사 처리는 다음 단계에서 검증할 예정입니다.

## 5. 프로젝트 구조

현재 구축된 주요 파일은 다음과 같습니다.

```text
starwars-rag/
├── data/                       # 원본 및 생성 데이터 (Git 제외)
│   ├── sample.txt
│   ├── starwars.xml
│   ├── chunks.json
│   ├── embeddings.npy
│   └── starwars.index
├── docs/
│   └── xml-schema.md           # XML 구조 및 청킹 기준
├── scripts/
│   ├── txt_to_xml.py           # TXT → XML 변환
│   ├── xml_chunker.py          # XML → JSON 청킹
│   ├── embed_chunks.py         # BGE-M3 임베딩
│   └── build_vector_index.py   # FAISS 인덱스 생성 및 저장
├── models/                     # 모델 캐시 (Git 제외)
├── venv/                       # Python 가상환경 (Git 제외)
├── .gitignore
├── README.md
├── test_bge_xpu.py             # BGE-M3 XPU 임베딩 검증
└── xpu-constraints.txt         # XPU 환경 주요 패키지 버전 고정
```

`data/`, `models/`, `venv/`는 `.gitignore`에 따라 버전 관리 대상에서 제외합니다. 따라서 저장소를 복제하더라도 데이터 파일과 FAISS 인덱스는 별도로 준비해야 합니다.

## 6. 현재 개발 상태

**1단계 — 데이터 및 벡터 검색 인덱스 구축 (완료)**

- [x] 스타워즈 백과사전 원본 TXT 데이터 정리
- [x] Python 가상환경 및 GitHub 저장소 구성
- [x] Intel Arc GPU 및 PyTorch XPU 연산 검증
- [x] BGE-M3 다국어 임베딩 테스트
- [x] TXT → XML 변환
- [x] XML 데이터 청킹 및 `chunks.json` 생성
- [x] BGE-M3 임베딩 및 `embeddings.npy` 저장
- [x] FAISS `IndexFlatIP` 생성 및 `starwars.index` 저장

**2단계 — 검색 기능 구현 (예정)**

- [ ] 사용자 질문 임베딩 및 FAISS Top-k 검색
- [ ] 검색 결과와 원본 청크·출처 연결
- [ ] 한국어 고유명사 검색 정확도 검증 및 검색 설정 조정

**3~5단계 — 챗봇 서비스 구현 (예정)**

- [ ] LLM API 연동 및 RAG 답변 생성
- [ ] FastAPI 백엔드 개발
- [ ] HTML 챗봇 프론트엔드 개발
- [ ] 전체 시스템 통합 및 테스트

## 7. BGE-M3 XPU 테스트

Intel Arc Graphics 환경에서 BGE-M3 모델을 사용한 한국어 및 영어 문장 임베딩 생성을 검증했습니다.

**테스트 환경**

- Python 3.12
- PyTorch 2.15.0+xpu
- NumPy 2.5.4
- SentenceTransformers 6.2.0
- Intel Arc Graphics

**검증 결과**

```text
Device: xpu:0
Embedding shape: (2, 1024)
Similarity: 0.6382403373718262
```

1024차원의 임베딩 벡터 생성과 Intel XPU 추론 실행이 정상적으로 완료되었습니다. 전체 151개 청크의 임베딩은 별도의 NVIDIA CUDA 환경에서 생성했습니다.

기존 테스트 환경에서 다음 명령어로 다시 검증할 수 있습니다.

```powershell
python .\test_bge_xpu.py
```

최초 실행 시 Hugging Face에서 BGE-M3 모델 가중치를 다운로드해야 합니다.

## 8. 데이터 및 저작권

Star Wars 및 관련 명칭과 콘텐츠의 권리는 해당 권리자에게 있습니다.

본 프로젝트는 교육 및 학습 목적으로 개발하는 비공식 프로젝트이며, Lucasfilm 또는 Disney와 공식적인 관련이 없습니다.

원본 Databank 설명과 가공 데이터, 모델 캐시 및 API 인증정보 등은 공개 Git 저장소에서 제외합니다. 해당 데이터의 사용과 배포에는 관련 저작권 및 이용 조건이 적용됩니다.

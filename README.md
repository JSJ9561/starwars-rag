# Star Wars Episode III RAG Chatbot

**Star Wars: Episode III – Revenge of the Sith**를 중심으로 구축한 RAG(Retrieval-Augmented Generation) 기반 AI 백과사전 챗봇 프로젝트입니다.

스타워즈의 인물, 생물, 드로이드, 장소, 조직, 탈것 및 영화의 공식 소개문을 구조화하고, 사용자의 자연어 질문에 관련 문서를 검색하여 답변합니다.

## 1. 프로젝트 개요

본 프로젝트는 대학 수업에서 학습한 자연어 처리(NLP), 사전학습 언어모델(PLM), 텍스트 임베딩 및 생성형 AI 기술을 실제 웹 서비스 형태로 구현하기 위한 프로젝트입니다.

**주요 기능**

- 스타워즈 에피소드 III 중심의 백과사전 및 영화 소개 데이터 구축
- TXT → XML 변환 및 JSON 청킹
- BGE-M3 임베딩과 FAISS 기반 의미 검색
- 검색된 문서를 근거로 하는 LLM 답변 생성
- HTML / CSS / JavaScript 기반 웹 챗봇 인터페이스
- 답변과 함께 참고 문서 이름 및 원문 링크 표시

## 2. 데이터 구성

주요 항목은 [Star Wars 공식 Databank](https://www.starwars.com/databank)의 설명을 참고하여 정리했습니다. 영화 개요는 [Episode III 공식 영화 페이지](https://www.starwars.com/films/star-wars-episode-iii-revenge-of-the-sith)의 소개문을 별도로 추가했습니다.

| Category | Records |
|---|---:|
| Characters | 63 |
| Creatures | 3 |
| Droids | 18 |
| Locations | 20 |
| Organizations | 17 |
| Vehicles | 21 |
| Short Plot | 1 |
| **일반 항목 합계** | **143** |

이와 별도로 `Character Specific` 영역에 주요 인물 9명의 관계 정보를 정리했습니다. 관계 데이터는 총 39개의 개별 관계로 구성되며, `mentor`, `apprentice`, `affiliation`, `homeworld`, `spouse`, `child`, `same_person_as` 등의 속성을 포함합니다.

일반 항목과 공식 소개문은 항목별로 하나의 청크를, 인물 관계는 인물별로 하나의 청크를 생성합니다.

**최종 청크 수는 152개(기존 백과사전 142개 + 공식 소개문 1개 + 인물 관계 9개)**입니다.

`Short Plot`에는 영화의 전체 대본이나 상세한 사건별 줄거리가 아닌 **공식 소개문 한 건**이 포함됩니다. 따라서 세부 장면에 관한 모든 질문에 답할 수 있는 것은 아닙니다. 또한 에피소드 III를 중심으로 데이터를 선정했지만, 개별 Databank 설명에는 다른 에피소드의 내용도 포함될 수 있습니다.

원본 및 가공 데이터는 공개 Git 저장소에 포함하지 않습니다. XML 구조와 청킹 규칙은 [`docs/xml-schema.md`](docs/xml-schema.md)를 참고하세요.

## 3. 기술 스택

| 구분 | 기술 | 상태 |
|---|---|---|
| Language | Python 3.12 | 사용 중 |
| Deep Learning | PyTorch 2.15.0+xpu | Intel XPU 환경 검증 완료 |
| Embedding | BAAI/bge-m3 | 152개 청크 임베딩 완료 |
| Embedding Library | SentenceTransformers 6.2.0 | 사용 중 |
| GPU Acceleration | Intel XPU / NVIDIA CUDA | XPU 테스트 및 CUDA 임베딩 수행 |
| Vector Search | FAISS (`IndexFlatIP`, `faiss-cpu`) | 인덱스 구축 및 검색 검증 완료 |
| Backend | FastAPI / Uvicorn | 웹 서버 및 채팅 API 구현 |
| Frontend | HTML / CSS / JavaScript | 웹 인터페이스 구현 |
| LLM | Groq API / Gemini API 연동 코드 | Groq 답변 생성 동작 확인 |
| Version Control | Git / GitHub | 구성 완료 |

## 4. 시스템 아키텍처

**데이터 구축 과정**

```text
TXT → XML → JSON Chunking → BGE-M3 Embedding → FAISS IndexFlatIP
```

- `chunks.json`: 청크 ID, 분류, 이름, 본문, 출처 URL 저장
- `embeddings.npy`: 152 × 1024 크기의 임베딩 벡터 저장
- `starwars.index`: 152개 벡터가 등록된 FAISS 검색 인덱스
- FAISS 검색 결과의 벡터 번호를 `chunks.json`의 항목 순서와 대응시켜 원문과 출처를 조회

**질문 처리 과정**

```text
User Question → BGE-M3 Query Embedding → FAISS Top-3 Search
              → Context Retrieval → LLM API → Answer + References
```

검색된 문서를 LLM의 입력 문맥으로 전달하며, 질문 언어에 맞춰 답변하도록 프롬프트를 구성했습니다. 웹 화면에서는 생성된 답변과 참고 문서를 함께 표시합니다.

## 5. 프로젝트 구조

```text
starwars-rag/
├── backend/
│   └── main.py                 # FastAPI 서버 및 API
├── frontend/
│   ├── index.html              # 챗봇 화면
│   ├── style.css               # 화면 스타일
│   └── app.js                  # 프론트엔드 동작
├── scripts/
│   ├── txt_to_xml.py           # TXT → XML 변환
│   ├── xml_chunker.py          # XML → JSON 청킹
│   ├── embed_chunks.py         # BGE-M3 임베딩 생성
│   ├── build_vector_index.py   # FAISS 인덱스 생성
│   ├── search_vector.py        # 벡터 검색 테스트
│   └── rag_answer.py           # RAG 검색 및 LLM 답변 생성
├── docs/
│   └── xml-schema.md           # XML 구조 및 청킹 기준
├── data/                       # 원본 및 생성 데이터 (Git 제외)
│   ├── sample.txt
│   ├── starwars.xml
│   ├── chunks.json
│   ├── embeddings.npy
│   └── starwars.index
├── models/                     # 임베딩 모델 캐시 (Git 제외)
├── venv/                       # Python 가상환경 (Git 제외)
├── .env                        # API 인증정보 (Git 제외)
├── .gitignore
├── README.md
├── test_bge_xpu.py             # Intel XPU 임베딩 검증
└── xpu-constraints.txt         # XPU 환경 주요 패키지 버전 고정
```

`data/`, `models/`, `venv/`, `.env`는 `.gitignore`에 따라 공개 저장소에서 제외합니다. 저장소 복제만으로 데이터 파일이나 API 인증정보를 얻을 수 없으므로 별도로 준비해야 합니다.

## 6. 현재 개발 상태

**데이터 구축 및 검색 기능**

- [x] 스타워즈 백과사전 TXT 데이터 정리
- [x] 공식 영화 소개문 `Short Plot` 추가
- [x] TXT → XML 변환 및 JSON 청킹
- [x] BGE-M3 기반 152개 청크 임베딩 생성
- [x] FAISS `IndexFlatIP` 구축 및 청크 연동
- [x] 한국어·영어 질문의 벡터 검색 동작 검증

**챗봇 서비스**

- [x] 검색 문맥 기반 RAG 답변 생성 기능 구현
- [x] Groq API 답변 생성 확인
- [x] FastAPI 백엔드 및 웹 프론트엔드 구현
- [x] 한국어 영화 줄거리 질문의 웹 챗봇 동작 확인
- [x] 답변 참고 문서 및 원문 링크 표시 확인
- [ ] 다양한 질문에 대한 검색 품질 평가 및 개선
- [ ] Gemini 모델별 실제 응답 추가 검증

**검색 품질 관련 참고**

공식 영화 소개문 청크는 영화의 영문 원제가 포함된 질문에서 1위로 검색되었습니다. 반면 `스타워즈 에피소드 3의 전체적인 줄거리를 요약해 줘`라는 한국어 질문에서는 3위로 검색되었습니다. 두 경우 모두 Top-3에는 포함되었지만, 검색 순위는 질문 표현에 따라 달라질 수 있습니다.

## 7. BGE-M3 XPU 테스트

Intel Arc Graphics 환경에서 BGE-M3 모델을 사용한 한국어 및 영어 문장 임베딩 생성을 검증했습니다.

**테스트 환경**

- Python 3.12
- PyTorch 2.15.0+xpu
- NumPy 2.5.4
- SentenceTransformers 6.2.0
- Intel Arc Graphics

**기존 테스트 결과**

```text
Device: xpu:0
Embedding shape: (2, 1024)
Similarity: 0.6382403373718262
```

1024차원 임베딩 생성과 Intel XPU 추론이 정상적으로 완료되었습니다. 전체 152개 청크의 임베딩은 별도의 NVIDIA CUDA 환경에서 생성했습니다.

```powershell
python .\test_bge_xpu.py
```

최초 실행 시 BGE-M3 모델 가중치 다운로드가 필요할 수 있습니다.

## 8. 챗봇 실행

Python 가상환경, 필요한 패키지, `data/chunks.json`, `data/starwars.index`, 임베딩 모델 및 API 키가 준비된 환경에서 프로젝트 루트에서 실행합니다.

```powershell
python -m uvicorn backend.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000/`에 접속합니다. 종료할 때는 실행 중인 터미널에서 `Ctrl + C`를 누릅니다.

현재 백엔드는 서버 시작 시 Groq와 Gemini 클라이언트를 모두 초기화하므로 `.env`에 `GROQ_API_KEY`와 `GEMINI_API_KEY`가 모두 설정되어 있어야 합니다. API 키를 Git 저장소에 커밋하지 마세요.

벡터 검색만 확인하려면 다음 스크립트를 사용할 수 있습니다.

```powershell
python scripts/search_vector.py
```

## 9. 데이터 및 저작권

Star Wars 및 관련 명칭과 콘텐츠의 권리는 해당 권리자에게 있습니다.

본 프로젝트는 교육 및 학습 목적으로 개발한 비공식 프로젝트이며, Lucasfilm 또는 Disney와 공식적인 관련이 없습니다.

원본 Databank 설명, 공식 영화 소개문, 가공 데이터, 모델 캐시 및 API 인증정보 등은 공개 Git 저장소에서 제외합니다. 해당 데이터의 사용과 배포에는 관련 저작권 및 이용 조건이 적용됩니다.
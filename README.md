# Star Wars Episode III RAG Chatbot

**Star Wars: Episode III – Revenge of the Sith**를 중심으로 구축한 RAG(Retrieval-Augmented Generation) 기반 AI 백과사전 챗봇 프로젝트입니다.

스타워즈의 인물, 생물, 드로이드, 장소, 조직, 탈것 등의 정보를 구조화하고, 사용자가 자연어로 질문하면 관련 문서를 검색하여 답변과 참고 자료를 제공하는 웹 챗봇입니다.

## 1. 프로젝트 개요

본 프로젝트는 대학 수업에서 학습한 자연어 처리(NLP), 사전학습 언어모델(PLM), 임베딩 및 생성형 AI 기술을 실제 서비스 형태로 구현하기 위한 프로젝트입니다.

**주요 구현 기능**

- 스타워즈 에피소드 III 중심의 백과사전 데이터 구축
- TXT 데이터를 XML 형태로 구조화
- 문서 청킹 및 BGE-M3 텍스트 임베딩
- FAISS 기반 의미 검색
- 외부 LLM API를 활용한 RAG 답변 생성
- FastAPI 기반 웹 백엔드 구축
- HTML/CSS/JavaScript 기반 대화형 웹 인터페이스
- 사용자별 질문에 따른 LLM 모델 선택
- 답변에 활용한 참고 문서 및 출처 표시

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

일반 백과사전 항목은 항목별로 하나의 청크를 생성하고, 인물 관계는 인물별로 하나의 청크를 생성했습니다.

**최종 청크 수는 151개(일반 항목 142개 + 인물 관계 9개)**입니다.

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
| Vector Search | FAISS (`IndexFlatIP`, `faiss-cpu`) | 구현 완료 |
| Backend | FastAPI / Uvicorn | 구현 완료 |
| Frontend | HTML / CSS / JavaScript | 구현 완료 |
| LLM API | Groq / Google Gemini | 연동 완료 |
| Environment | python-dotenv | API 키 관리 |
| Version Control | Git / GitHub | 구성 완료 |

### 사용 LLM

| 화면 표시명 | 실제 API 모델 ID | 검증 결과 |
|---|---|---|
| groq | `openai/gpt-oss-120b` | 답변 생성 성공 |
| gemini 3.5 lite | `gemini-3.5-flash-lite` | 답변 생성 성공 |
| gemini 3.8 flash | `gemini-3.8-flash` | 연동 및 오류 처리 확인, 정상 답변 생성 미확인 |

사용자는 웹 인터페이스에서 질문을 전송할 때 LLM을 선택할 수 있습니다.

Gemini 3.8 Flash에서는 테스트 중 503·504 서버 오류가 발생했으며, 현재 해당 오류를 사용자에게 표시하는 기능을 구현했습니다.

## 4. 시스템 아키텍처

본 프로젝트의 RAG 파이프라인은 데이터 구축, 검색, 답변 생성, 웹 서비스 단계로 구성됩니다.

### 4.1 데이터 구축

```text
TXT
  ↓
XML
  ↓
JSON Chunking
  ↓
BGE-M3 Embedding
  ↓
FAISS IndexFlatIP
```

생성되는 주요 파일은 다음과 같습니다.

- `chunks.json`: 청크 본문, 식별자, 분류, 이름, 출처 URL 저장
- `embeddings.npy`: 151 × 1024 크기의 임베딩 벡터 저장
- `starwars.index`: 151개 벡터를 등록한 FAISS 검색 인덱스

FAISS 검색 결과의 벡터 번호를 `chunks.json`의 항목 순서와 연결하여 원문과 출처를 확인합니다.

### 4.2 RAG 질문 처리

```text
User Question
      ↓
BGE-M3 Query Embedding
      ↓
FAISS Top-3 Search
      ↓
Context Retrieval
      ↓
Prompt Construction
      ↓
Selected LLM API
      ↓
Answer + References
```

사용자 질문을 BGE-M3로 임베딩하고, FAISS에서 가장 유사한 문서 3개를 검색합니다.

검색된 문서의 이름, 분류, 본문 및 출처를 문맥으로 구성한 뒤 LLM에 전달합니다.

LLM은 제공된 문맥을 기반으로 답변하며, 관련 정보가 부족하면 추측하지 않고 확인할 수 없다고 안내하도록 설계했습니다.

한국어와 영어 질문을 지원하며, 답변은 질문과 동일한 언어로 생성하도록 지시합니다.

답변 본문과 참고 문서는 구분하여 표시합니다.

### 4.3 웹 서비스

```text
HTML / CSS / JavaScript
          ↓
      FastAPI
          ↓
    RAG Pipeline
          ↓
    Groq / Gemini
          ↓
     JSON Response
          ↓
    Web Chat Interface
```

FastAPI 서버가 시작될 때 BGE-M3 모델과 FAISS 인덱스를 로딩하고, 이후 사용자 요청에서 재사용합니다.

프론트엔드는 FastAPI의 `/chat` 엔드포인트를 호출하여 답변과 참고 문서를 받아 표시합니다.

## 5. 프로젝트 구조

주요 파일 구성은 다음과 같습니다.

```text
starwars-rag/
├── backend/
│   └── main.py                 # FastAPI 백엔드
├── frontend/
│   ├── index.html              # 웹 화면 구조
│   ├── style.css               # 웹 디자인
│   └── app.js                  # 질문 전송 및 답변 표시
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
│   ├── build_vector_index.py   # FAISS 인덱스 생성 및 저장
│   ├── search_vector.py        # FAISS 의미 검색
│   └── rag_answer.py           # RAG 검색 및 답변 생성
├── models/                     # 모델 캐시 (Git 제외)
├── venv/                       # Python 가상환경 (Git 제외)
├── .env                        # API 키 (Git 제외)
├── .gitignore
├── README.md
├── test_bge_xpu.py             # BGE-M3 XPU 임베딩 검증
└── xpu-constraints.txt         # XPU 환경 주요 패키지 버전
```

`data/`, `models/`, `venv/`, `.env`는 버전 관리 대상에서 제외합니다.

따라서 저장소를 복제하더라도 필요한 데이터 파일, FAISS 인덱스, 모델 가중치 및 API 인증정보는 별도로 준비해야 합니다.

## 6. 실행 방법

### 6.1 실행 환경

- Python 3.12
- 필요한 Python 패키지가 설치된 가상환경
- BGE-M3 모델 및 FAISS 인덱스
- Groq 및 Gemini API 키
- 해당 환경에서 지원되는 PyTorch 연산 장치

현재 RAG 실행 환경은 Intel Arc Graphics의 XPU를 사용하도록 설정되어 있습니다.

### 6.2 API 키 설정

프로젝트 루트의 `.env` 파일에 API 키를 설정합니다.

```dotenv
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

실제 API 키를 GitHub에 커밋하지 않도록 주의해야 합니다.

### 6.3 CLI 실행

프로젝트 루트에서 다음 명령어를 실행합니다.

```powershell
python scripts/rag_answer.py
```

터미널에서 질문을 입력하면 RAG 검색 및 LLM 답변을 실행하고 참고 문서를 출력합니다.

CLI의 기본 모델은 코드에서 지정하며, 웹 프론트엔드에서는 요청별로 모델을 선택할 수 있습니다.

### 6.4 웹 챗봇 실행

프로젝트 루트에서 FastAPI 서버를 실행합니다.

```powershell
python -m uvicorn backend.main:app --reload
```

서버가 정상적으로 실행되면 웹 브라우저에서 다음 주소에 접속합니다.

- 웹 챗봇: http://127.0.0.1:8000/
- FastAPI API 문서: http://127.0.0.1:8000/docs

`--reload`는 개발용 자동 재시작 옵션입니다.

서버 종료 시 실행 중인 터미널에서 `Ctrl + C`를 누릅니다.

### 6.5 API 엔드포인트

| 메서드 | 경로 | 기능 |
|---|---|---|
| GET | `/models` | 사용 가능한 모델 식별자 조회 |
| POST | `/chat` | 질문을 처리하고 답변 및 참고 문서 반환 |

질문 요청 예시:

```json
{
  "query": "아나킨 스카이워커의 스승은 누구야?",
  "model_choice": "groq"
}
```

정상 응답에는 `answer`와 `references` 필드가 포함됩니다.

## 7. 웹 챗봇 주요 기능

### 질문 및 답변

사용자는 웹페이지에서 자연어 질문을 입력하고, 검색 기반 답변을 받을 수 있습니다.

사용자 질문과 AI 답변은 구분된 말풍선으로 표시됩니다.

### LLM 모델 선택

Groq, Gemini 3.5 Lite, Gemini 3.8 Flash 중 사용할 모델을 선택할 수 있습니다.

### 참고 문서

각 답변 아래에 FAISS에서 검색한 문서 3개를 표시합니다.

참고 문서 목록은 접고 펼칠 수 있으며, 출처 URL이 있는 경우 원문 링크를 제공합니다.

### 입력 및 대화 인터페이스

- Enter: 질문 전송
- Shift + Enter: 줄바꿈
- 입력 길이에 따른 질문 입력창 자동 확장
- 답변 생성 중 로딩 상태 표시
- 오류 발생 시 안내 메시지 출력
- 새 대화 버튼으로 화면의 대화 기록 초기화

현재 대화 기록은 웹페이지에 표시되는 용도이며, 이전 대화 내용을 다음 LLM 요청에 전달하는 다중 턴 기억 기능은 구현하지 않았습니다.

## 8. 개발 및 검증 현황

### 1단계 — 데이터 및 검색 인덱스 구축 (완료)

- [x] 스타워즈 백과사전 원본 TXT 데이터 정리
- [x] Python 가상환경 및 GitHub 저장소 구성
- [x] Intel Arc GPU 및 PyTorch XPU 연산 검증
- [x] BGE-M3 다국어 임베딩 테스트
- [x] TXT → XML 변환
- [x] XML 데이터 청킹 및 `chunks.json` 생성
- [x] BGE-M3 임베딩 및 `embeddings.npy` 저장
- [x] FAISS `IndexFlatIP` 생성 및 저장

### 2단계 — RAG 검색 및 답변 생성 (완료)

- [x] 사용자 질문 임베딩 및 FAISS Top-3 검색
- [x] 검색 결과와 원본 청크·출처 연결
- [x] 한국어·영어 질문 기본 검색 검증
- [x] Groq API 연동 및 답변 생성
- [x] Gemini 3.5 Lite API 연동 및 답변 생성
- [x] LLM API 예외 처리
- [x] CLI 질문 및 답변 출력

### 3단계 — FastAPI 백엔드 (완료)

- [x] RAG 모델 및 FAISS 인덱스 로딩
- [x] 질문 처리 API 구현
- [x] 요청별 LLM 모델 선택
- [x] 참고 문서 JSON 반환
- [x] API 오류의 HTTP 응답 변환
- [x] FastAPI 자동 API 문서 테스트

### 4단계 — 웹 프론트엔드 (완료)

- [x] HTML/CSS/JavaScript 기반 챗봇 구현
- [x] 스타워즈 테마 적용
- [x] 모델 선택 UI
- [x] 대화형 메시지 표시
- [x] 참고 문서 및 원문 링크 제공
- [x] 자동 확장 질문 입력창
- [x] 새 대화 기능
- [x] 로딩 및 오류 메시지 표시

### 5단계 — 통합 테스트 (기본 검증 완료)

- [x] Groq 웹 질문 및 답변 테스트
- [x] Gemini 3.5 Lite 웹 질문 및 답변 테스트
- [x] Gemini 3.8 Flash 오류 처리 테스트
- [x] 참고 문서 및 모델명 표시 테스트
- [x] 새 대화 및 입력창 동작 테스트
- [x] 서버 연결 실패 및 재시작 후 복구 테스트
- [ ] Gemini 3.8 Flash 정상 답변 생성 검증

## 9. BGE-M3 XPU 테스트

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

1024차원의 임베딩 벡터 생성과 Intel XPU 추론 실행이 정상적으로 완료되었습니다.

전체 151개 청크의 임베딩은 별도의 NVIDIA CUDA 환경에서 생성했습니다.

기존 테스트 환경에서 다음 명령어로 다시 검증할 수 있습니다.

```powershell
python .\test_bge_xpu.py
```

최초 실행 시 Hugging Face에서 BGE-M3 모델 가중치를 다운로드해야 할 수 있습니다.

## 10. 현재 한계

### 데이터 범위

본 프로젝트는 Episode III를 중심으로 데이터를 선정했지만, Star Wars Databank의 개별 설명에는 다른 에피소드의 사건이 포함될 수 있습니다.

따라서 생성된 답변이 Episode III의 내용만으로 엄격하게 제한되는 것은 아닙니다.

### 검색 품질

FAISS는 질문과 가장 유사한 문서를 검색하므로, 질문과 직접 관련되지 않은 문서가 검색 결과에 포함될 수 있습니다.

검색 결과의 관련성이 충분하지 않은 경우 LLM이 답변을 보류하도록 지시하지만, 모든 부정확한 답변을 방지하는 것은 아닙니다.

### LLM 응답

외부 API의 요청 한도나 서버 상태에 따라 답변 생성이 실패할 수 있습니다.

특히 Gemini 3.8 Flash는 테스트 과정에서 503·504 오류가 발생하여 정상적인 답변 생성이 확인되지 않았습니다.

### 대화 기억

현재 각 질문은 독립적으로 처리됩니다. 웹페이지에는 이전 대화가 표시되지만 LLM이 이전 대화 내용을 기억하지는 않습니다.

## 11. 데이터 및 저작권

Star Wars 및 관련 명칭과 콘텐츠의 권리는 해당 권리자에게 있습니다.

본 프로젝트는 교육 및 학습 목적으로 개발하는 비공식 프로젝트이며, Lucasfilm 또는 Disney와 공식적인 관련이 없습니다.

원본 Databank 설명과 가공 데이터, 모델 캐시 및 API 인증정보 등은 공개 Git 저장소에서 제외합니다.

해당 데이터의 사용과 배포에는 관련 저작권 및 이용 조건이 적용됩니다.

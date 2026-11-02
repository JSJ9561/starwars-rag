# Star Wars RAG — XML 데이터 구조 및 편찬 원칙

## 1. 목적

본 문서는 스타워즈 에피소드 III 중심의 백과사전 TXT 데이터를 XML로 구조화하기 위한 기준을 정의한다.

변환된 XML은 이후 문서 청킹, BGE-M3 임베딩 및 FAISS 벡터 검색 인덱스 구축에 사용한다.

**설계 원칙**

- 원본 TXT의 분류와 설명을 최대한 유지한다.
- 데이터에 없는 정보를 추측하거나 추가하지 않는다.
- 각 항목의 이름, 분류, 본문, 관계를 구분한다.
- 검색 결과에서 근거가 된 항목을 추적할 수 있도록 한다.
- 중복되거나 불필요한 청킹은 최소화한다.

## 2. 원본 데이터 구성

기준 자료: 최종 `sample.txt`

실제 프로그램 입력 경로: `data/sample.txt`

| Category | Records |
|---|---:|
| Characters | 63 |
| Creatures | 3 |
| Droids | 18 |
| Locations | 20 |
| Organizations | 17 |
| Vehicles | 21 |
| **Total** | **142** |

별도로 `Character Specific`에 주요 인물 9명의 관계 기록이 존재한다.

관계 데이터는 28개 속성 줄로 구성되며, 쉼표로 구분된 복수 대상을 개별 관계로 펼치면 총 39개의 관계가 된다.

`Character Specific`은 백과사전의 일곱 번째 일반 분류가 아니라 별도 관계 데이터 영역으로 취급한다.

## 3. TXT 파싱 규칙

### 3.1. 분류 인식

다음 문자열이 한 줄 전체와 일치할 때 분류 제목으로 인식한다.

- `Characters`
- `Creatures`
- `Droids`
- `Locations`
- `Organizations`
- `Vehicles`
- `Character Specific`

분류 제목은 개별 항목에 포함하지 않는다.

### 3.2. 항목 구분

일반 항목은 빈 줄을 기준으로 구분한다.

- 공백이나 탭만 포함된 줄도 빈 줄로 처리한다.
- 연속된 빈 줄은 하나의 구분자로 처리한다.
- 분류 제목이 나타나면 이전 분류를 종료하고 새로운 분류로 전환한다.
- 파일 끝에 남아 있는 마지막 항목도 정상 처리한다.

### 3.3. 일반 항목의 구조

현재 원본에서는 일반 항목이 다음 구조를 따른다.

```text
항목 이름
항목 설명
source: https://www.starwars.com/databank/...

다음 항목 이름
다음 항목 설명
source: https://www.starwars.com/databank/...
```

파싱 기준:

1. 첫 번째 줄을 항목 이름으로 인식한다.
2. 마지막 `source:` 줄에서 Star Wars Databank URL을 추출한다.
3. 이름과 `source:` 사이의 줄을 설명으로 인식하고, 여러 줄이면 원래 순서대로 결합한다.
4. 원문 내용과 영문 표기를 보존하며, 이름·설명·출처 누락 여부를 검증한다.

### 3.4. Character Specific 구조

일반 항목과 달리 첫 줄은 인물 이름이고 이후 줄은 `속성명: 값` 형식이다.

```text
Anakin Skywalker
    homeworld: Tatooine
    mentor: Obi-Wan Kenobi
    spouse: Padmé Amidala
    affiliation: Jedi Order, Galactic Republic
```

파싱 기준:

1. 첫 줄을 관계의 주체인 인물 이름으로 인식한다.
2. 이후 줄은 첫 번째 `:`를 기준으로 속성과 값으로 구분한다.
3. 하나의 속성에 여러 대상이 있는 경우 개별 관계로 분리한다.
4. 분리하더라도 원본의 속성명과 대상 표기를 그대로 보존한다.
5. 원본에 없는 역방향 관계를 자동 생성하지 않는다.

현재 사용되는 관계 속성은 다음 10개다.

`homeworld`, `mentor`, `apprentice`, `spouse`, `child`, `affiliation`, `piloted`, `same_person_as`, `trained`, `trained_by`

## 4. XML 구조

최상위 요소는 `<star_wars_encyclopedia>`로 한다.

XML은 일반 백과사전 항목과 주요 인물 관계를 별도 영역으로 구분한다.

### 4.1. 일반 항목

```xml
<?xml version="1.0" encoding="UTF-8"?>
<star_wars_encyclopedia version="1.0">
    <entries>
        <category name="Characters">
            <entry id="characters-003">
                <name>Anakin Skywalker</name>
                <description>원본 설명을 그대로 삽입</description>
                <source name="Star Wars Databank" url="https://www.starwars.com/databank/anakin-skywalker" />
            </entry>
        </category>
    </entries>

    <character_specific>
    </character_specific>
</star_wars_encyclopedia>
```

위 XML은 구조 설명을 위한 예시이며, 실제 `starwars.xml`에는 일반 분류 6개와 항목 142개가 포함된다.

각 요소의 역할은 다음과 같다.

| 요소 | 설명 |
|---|---|
| `star_wars_encyclopedia` | XML 최상위 요소 |
| `entries` | 일반 백과사전 데이터 |
| `category` | 항목이 속한 분류 |
| `entry` | 개별 백과사전 항목 |
| `id` | 항목의 고유 식별자 |
| `name` | 원본 항목 이름 |
| `description` | 원본 설명문 |
| `source` | Star Wars Databank 출처 (`name`, `url` 속성) |
| `character_specific` | 별도 인물 관계 영역 |
| `character` | 관계의 주체인 인물 (`name` 속성) |
| `relation` | 관계 유형과 대상 (`type`, `target` 속성) |

항목 ID는 분류와 항목 순번을 조합하여 생성한다. 같은 XML 안에서 중복되어서는 안 된다. 원본 항목 순서가 달라지면 순번 기반 ID도 달라질 수 있으므로 데이터 갱신 시 확인한다.

### 4.2. 인물 관계

```xml
<character_specific>
    <character name="Anakin Skywalker">
        <relation type="homeworld" target="Tatooine" />
        <relation type="mentor" target="Obi-Wan Kenobi" />
        <relation type="spouse" target="Padmé Amidala" />
        <relation type="affiliation" target="Jedi Order" />
        <relation type="affiliation" target="Galactic Republic" />
    </character>
</character_specific>
```

이 예시는 일부 관계만 표시한 것이다.

`relation`은 관계 유형과 대상의 조합으로 구성한다. 복수 대상은 각각 독립된 `relation` 요소로 저장한다.

`same_person_as`는 원본의 동일 인물 관계를 나타내는 속성으로 보존한다. 해당 관계가 존재한다고 해서 서로 다른 이름의 일반 백과사전 항목을 자동 병합하지는 않는다.

## 5. 원본 정보 보존 및 전거 관리

백과사전 항목의 원문을 임의로 요약하거나 수정하지 않는다.

- 이름과 설명은 원본의 영문 표기를 유지한다.
- Unicode 문자와 고유명사를 보존한다.
- XML 특수문자는 올바르게 이스케이프한다.
- 입력 파일의 항목 순서를 유지한다.
- 원본에 없는 관계나 배경지식을 추가하지 않는다.

일반 항목은 XML의 `<source>` 요소에 Databank 출처 이름과 URL을 기록한다. 인물 관계 영역에는 별도의 출처 URL이 지정되어 있지 않다.

청킹 결과인 `chunks.json`은 다음 필드를 사용한다.

| 필드 | 내용 |
|---|---|
| `id` | 청크 고유 식별자 (`characters-001`, `relations-001` 등) |
| `category` | 일반 분류 또는 `Character Specific` |
| `name` | 항목 이름 또는 관계 주체의 이름 |
| `text` | 임베딩에 사용하는 이름과 설명/관계 문자열 |
| `source_url` | 일반 항목의 Databank URL, 인물 관계에서는 `null` |

입력 TXT 파일 경로는 변환 프로그램 설정으로 관리하며, `chunks.json`의 개별 필드에는 저장하지 않는다. 출처 URL이 없는 경우 임의로 생성하지 않는다.

챗봇에서는 가능한 경우 Databank URL을 제시하고, URL이 없는 관계 청크는 해당 관계가 별도 정리 자료임을 구분해야 한다.

## 6. 청킹 원칙

### 6.1. 일반 설명

기본적으로 **백과사전 항목 1개를 청크 1개로 처리**한다.

청크에는 항목 이름과 설명을 함께 포함한다.

`text` 필드의 예시:

```text
Anakin Skywalker
원본 설명
```

분류(`Characters`)와 출처 URL은 본문에 별도 접두어로 넣지 않고 청크 메타데이터에 저장한다.

청크를 생성할 때 다음을 확인한다.

- 항목 이름이 누락되지 않을 것
- 설명문 전체가 포함될 것
- 서로 다른 항목의 설명이 합쳐지지 않을 것
- 제목과 분류가 검색 메타데이터로 보존될 것

BGE-M3 토크나이저로 실제 길이를 측정한 후 모델의 입력 길이를 초과하거나 검색 품질에 문제가 있는 항목만 추가 분할한다.

### 6.2. 인물 관계

인물 관계는 주체별로 하나의 검색 단위를 구성한다.

`text` 필드의 예시:

```text
Anakin Skywalker
homeworld: Tatooine
mentor: Obi-Wan Kenobi
spouse: Padmé Amidala
affiliation: Jedi Order
affiliation: Galactic Republic
child: Luke Skywalker
child: Leia Organa
piloted: Eta-2 Jedi Starfighter
```

관계 유형과 대상을 `유형: 대상` 형태로 한 줄씩 보존하며, 주체 이름을 첫 줄에 포함한다. 주체별 청크 ID는 `relations-001`부터 `relations-009`까지 부여한다.

### 6.3. 확정 청크 수

현재 `xml_chunker.py`로 생성하고 검증한 청크 수는 다음과 같다.

| 청크 유형 | 개수 |
|---|---:|
| 백과사전 설명 | 142 |
| 인물 관계 | 9 |
| **총합** | **151** |

현재는 일반 항목별·인물별 추가 분할 없이 청크를 생성했다. 이 151개 청크는 BGE-M3로 각각 1024차원 벡터로 변환되어 `embeddings.npy`에 저장되며, 동일한 순서로 FAISS 인덱스에 등록된다. 토큰 길이와 검색 품질에 따른 추가 분할은 향후 검토 사항이다.

## 7. XML 변환 검증 기준

변환 및 후속 데이터 구축 결과에서 다음 사항을 확인한다.

| 검증 항목 | 기대 결과 |
|---|---|
| 일반 분류 개수 | 6개 |
| 일반 항목 개수 | 142개 |
| Characters | 63개 |
| Creatures | 3개 |
| Droids | 18개 |
| Locations | 20개 |
| Organizations | 17개 |
| Vehicles | 21개 |
| Character Specific 주체 | 9명 |
| 관계 속성 원본 줄 | 28개 |
| 개별 관계로 분리한 결과 | 39개 |
| 빈 이름 또는 설명 | 0개 |
| 중복 항목 ID | 0개 |
| XML 문법 오류 | 0개 |

추가로 XML에서 추출한 이름과 설명이 원본 TXT의 내용과 일치하는지 검증한다.

개수 불일치, 누락된 본문, 알 수 없는 속성, 잘못된 XML 구조가 발견되면 원본을 임의로 보정하지 않고 입력 파일과 변환 로직을 확인한다. 파일 갱신 시 `chunks.json`, `embeddings.npy`, `starwars.index`의 데이터 개수와 순서도 함께 재검증한다.

## 8. 파일 및 디렉터리

```text
스타워즈RAG/
├── data/
│   ├── sample.txt
│   ├── starwars.xml
│   ├── chunks.json
│   ├── embeddings.npy
│   └── starwars.index
├── docs/
│   └── xml-schema.md
└── scripts/
    ├── txt_to_xml.py
    ├── xml_chunker.py
    ├── embed_chunks.py
    └── build_vector_index.py
```

- `data/sample.txt`: 최종 원본 데이터
- `data/starwars.xml`: XML 변환 결과
- `data/chunks.json`: 151개 청크와 메타데이터
- `data/embeddings.npy`: BGE-M3 임베딩 배열 (`151 × 1024`, `float32`)
- `data/starwars.index`: FAISS `IndexFlatIP` 검색 인덱스
- `docs/xml-schema.md`: 구조 및 검증 기준
- `scripts/txt_to_xml.py`: TXT → XML 변환 프로그램
- `scripts/xml_chunker.py`: XML → JSON 청킹 프로그램
- `scripts/embed_chunks.py`: JSON → BGE-M3 임베딩 및 파일 저장
- `scripts/build_vector_index.py`: 임베딩 → FAISS 인덱스 생성 및 저장

원본 및 가공 데이터는 `.gitignore`에 따라 공개 Git 저장소에서 제외한다. 프로그램 소스와 설계 문서는 Git으로 관리한다.

## 9. 향후 검토 사항

XML 변환·청킹·임베딩·FAISS 인덱스 구축을 완료했으며, 다음 항목은 검색 및 답변 단계에서 검토한다.

- BGE-M3 토크나이저 기반 청크 길이 측정 및 추가 분할 필요성
- 한국어 질문과 영문 고유명사 간 검색 정확도
- 인물 관계 및 `same_person_as` 검색 정확도
- 항목별 출처 표시와 출처 없는 관계 데이터의 구분
- 청크 중복 여부 및 FAISS Top-k 검색 결과 평가
- 실제 질문에 대한 RAG 답변의 전거 충실도

추가 세부 주제 분류는 초기 단계에서 도입하지 않는다. 기본 6개 분류만으로 검색 평가를 진행한 뒤 필요성이 확인되면 검토한다.

import os
import json
import numpy as np
import faiss
import httpx
from sentence_transformers import SentenceTransformer
from pathlib import Path
from dotenv import load_dotenv
from google.genai import types
from google import genai
from groq import Groq, RateLimitError, InternalServerError, APIConnectionError, APITimeoutError, APIStatusError
from google.genai.errors import ServerError, ClientError

# 예외 처리
class LLMAPIError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(message)

# 모델 선택
MODEL_IDS = {
    'gemini_lite': 'gemini-3.5-flash-lite',
    'gemini_flash': 'gemini-3.8-flash',
    'groq': 'openai/gpt-oss-120b'
}

# 질문 임베딩 및 FAISS 검색 함수
def search_vectors(query, model, index, k=3):
    query_embedding = model.encode(
        query,
        batch_size=1,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    query_embedding = query_embedding.astype(np.float32).reshape(1, -1)

    k = min(k, index.ntotal)
    scores, indices = index.search(query_embedding, k)

    return scores, indices

# 공통 문맥 구성 함수
def build_context(indices, chunks):
    context = []
    for idx in indices[0]:
        chunk = chunks[int(idx)]
        context.append(chunk)

    context_text = []
    for chunk in context:
        source_url = chunk['source_url']
        if source_url is None:
            source_url = '출처 없음'
        temp = []
        temp.append(chunk['name'])
        temp.append(chunk['category'])
        temp.append(chunk['text'])
        temp.append(source_url)
        context_text.append('\n'.join(temp))

    context_text = '\n\n'.join(context_text)

    return context, context_text

# 공통 프롬프트 구성 함수
def build_prompt(query, context_text):
    prompt = f'''역할: 스타워즈 "Episode III: 시스의 복수" 관련 질문에 답변하는 챗봇
근거: 검색된 문맥에 포함된 정보만 사용할 것
정보 부족: 근거가 없으면 추측하지 않고 모른다고 답변할 것
언어 규칙:
- 한국어 질문에는 한국어로 답변할 것
- 영어 질문에는 영어로 답변할 것
- 검색된 문맥의 언어와 관계없이 사용자 질문의 언어를 우선할 것
출력 형식: 답변은 자연스러운 일반 텍스트로 작성하고 Markdown 문법을 사용하지 말 것
출처 표시: 답변 본문에는 URL, 출처 인용, 참고 문서 표기를 포함하지 말 것

검색된 문맥: {context_text}
사용자 질문: {query}
'''

    return prompt

# LLM API 호출 함수
def generate_answer(prompt, model_choice, model_id, client):
    if model_choice == 'groq':
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
            answer = response.choices[0].message.content
        except RateLimitError as e:
            raise LLMAPIError(429, 'Groq API 요청 한도를 초과했습니다.') from e
        except InternalServerError as e:
            raise LLMAPIError(503, 'Groq 서버 오류로 답변을 생성하지 못했습니다.') from e
        except APITimeoutError as e:
            raise LLMAPIError(504, 'Groq API 요청 시간이 초과됐습니다.') from e
        except APIConnectionError as e:
            raise LLMAPIError(503, 'Groq API 서버에 연결하지 못했습니다.') from e
        except APIStatusError as e:
            raise LLMAPIError(e.status_code, 'Groq API 요청 처리 중 오류가 발생했습니다.') from e
    else:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt
            )
            answer = response.text
        except ClientError as e:
            if e.code == 429:
                raise LLMAPIError(429, 'Gemini API 요청 한도를 초과했습니다.') from e
            else:
                raise LLMAPIError(e.code, 'Gemini API 요청 처리 중 오류가 발생했습니다.') from e
        except ServerError as e:
            if e.code == 503:
                raise LLMAPIError(503, 'Gemini 서버가 혼잡하여 답변을 생성하지 못했습니다.') from e
            elif e.code == 504:
                raise LLMAPIError(504, 'Gemini 서버가 제한 시간 내에 응답하지 못했습니다.') from e
            else:
                raise LLMAPIError(e.code, 'Gemini 서버 오류로 답변을 생성하지 못했습니다.') from e
        except httpx.TimeoutException as e:
            raise LLMAPIError(504, 'Gemini API 요청 시간이 초과됐습니다.') from e
        except httpx.RequestError as e:
            raise LLMAPIError(503, 'Gemini API 서버에 연결하지 못했습니다.') from e

    if not isinstance(answer, str) or not answer.strip():
        raise LLMAPIError(502, 'LLM이 유효한 답변을 반환하지 않았습니다.')

    return answer

# LLM 클라이언트 생성 함수
def create_llm_client(model_choice, project_root):
    load_dotenv(project_root / '.env')

    if model_choice == 'groq':
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError('Groq API 키가 없습니다.')

        client = Groq(
            api_key=api_key,
            timeout=20.0,
            max_retries=0
        )
    else:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError('Gemini API 키가 없습니다.')

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=30000,
                retry_options=types.HttpRetryOptions(attempts=1)
            )
        )

    return client

# FastAPI 호출 함수
def answer_question(query, model_choice, model, index, chunks, client):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('질문을 입력해야 합니다.')

    if model_choice not in MODEL_IDS:
        raise ValueError(f'지원하지 않는 모델입니다: {model_choice}')

    model_id = MODEL_IDS[model_choice]

    scores, indices = search_vectors(query, model, index)
    context, context_text = build_context(indices, chunks)
    prompt = build_prompt(query, context_text)
    answer = generate_answer(prompt, model_choice, model_id, client)

    return answer, context

# RAG 데이터 및 모델 로딩 함수
def load_rag_resources(project_root):
    json_path = project_root / 'data' / 'chunks.json'
    faiss_path = project_root / 'data' / 'starwars.index'

    # JSON 파일 로딩
    try:
        with json_path.open('r', encoding='utf-8') as f:
            chunks = json.load(f)
    except FileNotFoundError as e:
        raise ValueError('문서 JSON 파일이 없습니다.') from e
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        raise ValueError('문서 JSON 파일을 읽을 수 없거나 형식이 올바르지 않습니다.') from e

    if not isinstance(chunks, list):
        raise ValueError('문서 JSON 데이터가 리스트 형식이 아닙니다.')

    # FAISS 인덱스 로딩
    try:
        index = faiss.deserialize_index(np.frombuffer(faiss_path.read_bytes(), dtype=np.uint8))
    except FileNotFoundError as e:
        raise ValueError('FAISS 인덱스 파일이 없습니다.') from e
    except (OSError, RuntimeError) as e:
        raise ValueError('FAISS 인덱스 파일을 읽거나 복원하지 못했습니다.') from e

    # 데이터 일치 여부 검증
    if index.ntotal == 0:
        raise ValueError('검색할 데이터가 없습니다.')

    if len(chunks) != index.ntotal:
        raise ValueError('검색 인덱스와 문서 데이터 개수가 일치하지 않습니다.')

    # 청크 데이터 구조 검증
    required_fields = {'id', 'name', 'category', 'text', 'source_url'}

    for i, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f'{i}번 청크의 데이터 형식이 올바르지 않습니다.')

        missing_fields = required_fields - chunk.keys()
        if missing_fields:
            raise ValueError(f'{i}번 청크에 필수 필드가 없습니다: {missing_fields}')

        for field in ('name', 'category', 'text'):
            if not isinstance(chunk[field], str) or not chunk[field].strip():
                raise ValueError(f'{i}번 청크의 {field} 값이 올바르지 않습니다.')

        if chunk['source_url'] is not None and not isinstance(chunk['source_url'], str):
            raise ValueError(f'{i}번 청크의 출처 형식이 올바르지 않습니다.')

    # 임베딩 모델 로딩
    model = SentenceTransformer(
        'BAAI/bge-m3',
        device='xpu',
        cache_folder=str(project_root / 'models')
    )

    # 임베딩 모델과 FAISS 차원 일치 검증
    embedding_dim = model.get_embedding_dimension()

    if embedding_dim != index.d:
        raise ValueError(
            f'임베딩 차원 불일치: 모델 {embedding_dim}, FAISS {index.d}'
        )

    return model, index, chunks

# 메인 함수
def main():
    # 질문 검증
    query = input('질문: ').strip()
    if not query:
        print('질문을 입력해야 합니다')
        raise SystemExit(1)

    # 모델 선택
    model_choice = 'groq'

    # 프로젝트 경로 설정
    project_root = Path(__file__).resolve().parent.parent

    try:
        if model_choice not in MODEL_IDS:
            raise ValueError(f'지원하지 않는 모델입니다: {model_choice}')
        model, index, chunks = load_rag_resources(project_root)

        with create_llm_client(model_choice, project_root) as client:
            answer, context = answer_question(query, model_choice, model, index, chunks, client)
    except LLMAPIError as e:
        print(f'API 오류 ({e.status_code}): {e}')
        raise SystemExit(1)
    except ValueError as e:
        print(f'오류: {e}')
        raise SystemExit(1)

    print('답변:', answer)
    print('\n참고 문서:')
    for rank, chunk in enumerate(context, start=1):
        print(f"{rank}. {chunk['name']}")
        print(f"   출처: {chunk['source_url'] or '없음'}")

# 메인 호출
if __name__ == '__main__':
    main()

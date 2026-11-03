from contextlib import asynccontextmanager, ExitStack
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from scripts.rag_answer import (MODEL_IDS, LLMAPIError, load_rag_resources, create_llm_client, answer_question)

# 프로젝트 경로 설정
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 질문 요청 데이터 정의
class ChatRequest(BaseModel):
    query: str
    model_choice: str

# 서버 시작 및 종료 시 자원 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    model, index, chunks = load_rag_resources(PROJECT_ROOT)

    with ExitStack() as stack:
        groq_client = stack.enter_context(
            create_llm_client('groq', PROJECT_ROOT)
        )
        gemini_client = stack.enter_context(
            create_llm_client('gemini_lite', PROJECT_ROOT)
        )

        app.state.model = model
        app.state.index = index
        app.state.chunks = chunks
        app.state.clients = {
            'groq': groq_client,
            'gemini_lite': gemini_client,
            'gemini_flash': gemini_client
        }

        yield

# FastAPI 애플리케이션 생성
app = FastAPI(lifespan=lifespan)

# 사용 가능한 모델 목록
@app.get('/models')
def get_models():
    return {'models': list(MODEL_IDS.keys())}

# 질문 및 답변 API
@app.post('/chat')
def chat(data: ChatRequest, request: Request):
    try:
        if data.model_choice not in MODEL_IDS:
            raise ValueError(f'지원하지 않는 모델입니다: {data.model_choice}')
        answer, context = answer_question(
            data.query,
            data.model_choice,
            request.app.state.model,
            request.app.state.index,
            request.app.state.chunks,
            request.app.state.clients[data.model_choice]
        )
    except LLMAPIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e)
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        ) from e

    return {
        'answer': answer,
        'references': [
            {
                'name': chunk['name'],
                'source_url': chunk['source_url']
            }
            for chunk in context
        ]
    }

# 프론트엔드 파일 제공
app.mount(
    '/',
    StaticFiles(directory=PROJECT_ROOT / 'frontend', html=True),
    name='frontend'
)
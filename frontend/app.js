// HTML 요소 연결
const questionInput = document.getElementById('question-input');
const chatForm = document.getElementById('chat-form');
const chatMessages = document.getElementById('chat-messages');
const chatContainer = document.querySelector('.chat-container');
const modelSelect = document.getElementById('model-select');
const sendButton = document.getElementById('send-button');
const resetButton = document.getElementById('reset-button');
const statusMessage = document.getElementById('status-message');

// 시작 화면 보관
const welcomeTemplate = document.querySelector('.welcome-message').cloneNode(true);

let isSubmitting = false;

// 질문 입력창 높이 자동 조절
function resizeQuestionInput() {
    questionInput.style.height = '40px';

    const maxHeight = 160;
    const nextHeight = Math.min(questionInput.scrollHeight, maxHeight);

    questionInput.style.height = nextHeight + 'px';
    questionInput.style.overflowY =
        questionInput.scrollHeight > maxHeight ? 'auto' : 'hidden';
}

// 대화 영역 스크롤
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 로딩 상태 변경
function setLoading(loading) {
    isSubmitting = loading;

    sendButton.disabled = loading;
    modelSelect.disabled = loading;
    questionInput.disabled = loading;
    resetButton.disabled = loading;

    sendButton.textContent = loading ? '전송 중...' : '전송';

    statusMessage.textContent = loading
        ? '자료를 검색하고 AI 답변을 생성하고 있습니다...'
        : '';
}

// 답변의 굵은 글씨 표시
function appendFormattedText(element, text) {
    const parts = String(text).split(/(\*\*[^*]+\*\*)/g);

    for (const part of parts) {
        if (part.startsWith('**') && part.endsWith('**')) {
            const strong = document.createElement('strong');
            strong.textContent = part.slice(2, -2);
            element.appendChild(strong);
        } else {
            element.appendChild(document.createTextNode(part));
        }
    }
}

// 참고 문서 구성
function createReferences(references) {
    const details = document.createElement('details');
    details.className = 'references';

    const summary = document.createElement('summary');
    summary.textContent = `참고 문서 ${references.length}개`;
    details.appendChild(summary);

    const list = document.createElement('ul');

    for (const reference of references) {
        const item = document.createElement('li');

        const name = document.createElement('span');
        name.textContent = reference.name || '이름 없는 문서';
        item.appendChild(name);

        let validUrl = null;

        if (reference.source_url) {
            try {
                const url = new URL(reference.source_url);
                if (url.protocol === 'https:' || url.protocol === 'http:') {
                    validUrl = url.href;
                }
            } catch {
                validUrl = null;
            }
        }

        if (validUrl) {
            const link = document.createElement('a');
            link.href = validUrl;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = '원문 보기';
            item.appendChild(link);
        } else {
            const noSource = document.createElement('span');
            noSource.className = 'reference-no-source';
            noSource.textContent = '출처 없음';
            item.appendChild(noSource);
        }

        list.appendChild(item);
    }

    details.appendChild(list);
    return details;
}

// 대화 메시지 출력
function appendMessage(role, text, references = [], modelName = '', isError = false) {
    const welcome = chatMessages.querySelector('.welcome-message');

    if (welcome) {
        welcome.remove();
    }

    const message = document.createElement('div');
    message.className = `message ${role}-message`;

    if (isError) {
        message.classList.add('error-message');
    }

    const content = document.createElement('div');
    content.className = 'message-text';

    content.textContent = text;
    message.appendChild(content);

    if (Array.isArray(references) && references.length > 0) {
        message.appendChild(createReferences(references));
    }

    if (role === 'assistant' && modelName) {
        const modelInfo = document.createElement('div');
        modelInfo.className = 'message-model';
        modelInfo.textContent = modelName;
        message.appendChild(modelInfo);
    }

    chatMessages.appendChild(message);
    scrollToBottom();
}

// 질문 전송 및 FastAPI 연동
async function sendQuestion(event) {
    event.preventDefault();

    if (isSubmitting) {
        return;
    }

    const query = questionInput.value.trim();

    if (!query) {
        questionInput.focus();
        return;
    }

    const modelChoice = modelSelect.value;
    const modelName = modelSelect.selectedOptions[0].textContent.trim();

    appendMessage('user', query);

    questionInput.value = '';
    resizeQuestionInput();

    setLoading(true);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                model_choice: modelChoice
            })
        });

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error('서버 응답을 읽을 수 없습니다.');
        }

        if (!response.ok) {
            const detail = typeof data.detail === 'string'
                ? data.detail
                : `HTTP ${response.status} 오류가 발생했습니다.`;

            throw new Error(detail);
        }

        if (typeof data.answer !== 'string') {
            throw new Error('답변 데이터 형식이 올바르지 않습니다.');
        }

        appendMessage(
            'assistant',
            data.answer,
            data.references || [],
            modelName
        );

    } catch (error) {
        const message = error instanceof TypeError
            ? '서버에 연결하지 못했습니다. FastAPI 실행 상태를 확인해 주세요.'
            : error.message;

        appendMessage(
            'assistant',
            `오류: ${message}`,
            [],
            modelName,
            true
        );

    } finally {
        setLoading(false);
        questionInput.focus();
    }
}

// Enter 전송 및 Shift+Enter 줄바꿈
questionInput.addEventListener('keydown', (event) => {
    if (
        event.key === 'Enter' &&
        !event.shiftKey &&
        !event.isComposing
    ) {
        event.preventDefault();

        if (!event.repeat && !isSubmitting && questionInput.value.trim()) {
            chatForm.requestSubmit();
        }
    }
});

// 입력창 자동 확장
questionInput.addEventListener('input', resizeQuestionInput);

// 전송 버튼 및 폼 제출
chatForm.addEventListener('submit', sendQuestion);

// 새 대화 버튼
resetButton.addEventListener('click', () => {
    if (isSubmitting) {
        return;
    }

    chatMessages.replaceChildren(welcomeTemplate.cloneNode(true));

    questionInput.value = '';
    statusMessage.textContent = '';

    resizeQuestionInput();
    questionInput.focus();
});

// 최초 입력창 크기 설정
resizeQuestionInput();

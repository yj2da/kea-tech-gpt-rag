# 🚀 KEA Enterprise Tech-GPT RAG Platform (v2.0)

[![Streamlit Cloud App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://kea-tech-gpt.streamlit.app)
![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FAISS Vector DB](https://img.shields.io/badge/FAISS-Vector%20DB-00599C?style=flat)
![Groq Llama 3.3](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F05032?style=flat)

**한국전자정보통신산업진흥회(KEA) 생성형 AI 기반 대화형 기술 플랫폼 구축 및 운영 (Tech-GPT)**  
고비용 모델 파인튜닝 없이 **0원 FAISS + BM25 RRF 하이브리드 RAG 인덱싱**과 **3단계 신뢰성 파이프라인(Clarification Loop, Query Contextualizer, L2 Guardrail 1.45)** 및 **서드파티 시드 데이터 마켓(Tech-GPT Store)**을 제공하는 엔터프라이즈 RAG 솔루션입니다.

---

## 🌐 24시간 상시 라이브 서비스 배포 주소
- **Public Live URL**: [https://kea-tech-gpt.streamlit.app](https://kea-tech-gpt.streamlit.app)

---

## 🔑 주요 아키텍처 및 핵심 기능

### 1. 0원 파인튜닝 하이브리드 RAG (FAISS + BM25 RRF)
- **Reciprocal Rank Fusion (RRF)**: FAISS(시맨틱 유사도 점수)와 BM25(한국어 조사 분리 키워드 토크나이저) 검색 결과를 RRF 수식($1 / (60 + rank)$)으로 공정하게 순위 융합 정렬합니다.
- **Top-K 3 청크 최소 참조**: 문서 탐색 정확도 95%+ 달성 및 토큰 비용 최소화.

### 2. 3단계 신뢰성 파이프라인 (3-Tier Reliability Engine)
1. **Clarification Loop (스마트 역질문 Form)**: 모호한 질의("사양 알려줘") 감지 시 3가지 세부 관점 선택지 Form을 동적으로 제시합니다.
2. **Query Contextualizer (멀티턴 맥락 재구성)**: 지시대명사("그거", "아까 말한 항목") 감지 시 최근 대화 이력을 참조해 독립적 RAG 검색어로 자동 재작성합니다.
3. **FAISS L2 Distance Guardrail (환각 사전 차단)**: 50개 샘플 실측 분석 기반 FAISS L2 Distance > 1.45 시 LLM 호출을 사전에 100% 차단하여 환각을 방지하고 비용을 0원으로 방어합니다.

### 3. Tech-GPT Store (서드파티 시드 데이터 마켓)
- **콜드 스타트 완화 시드 모듈 4종**: KEA R&D 요약 에이전트, JSON API 파라미터 변환기, 특허 청구항 비교 매퍼, On-Premise Ollama 보안 모듈 탑재.
- **단일 선택 활성화 제어 (`active_store_module`)**: 1회당 1개 특화 모듈만 RAG 대화 엔진에 결합되도록 UI/UX 제어.
- **비동기 이메일 및 원자적 보관**: 서드파티 모듈 등록 신청 시 네이버 SMTP (`oyjcat@naver.com`) 비동기 쓰레드(`threading.Thread`) 0초 UI 응답 처리 및 Atomic Write 보관.

### 4. 멀티유저 데이터 완전 격리 (`st.session_state`)
- 브라우저 탭 단위 독립 세션 메모리로 전환하여 클라우드 멀티유저 환경에서 동시 사용자 간 대화 유출을 100% 차단했습니다.

---

## 🛠️ 기술 스택 (Tech Stack)

| 구분 | 기술 스택 |
| :--- | :--- |
| **Frontend / UI** | Streamlit, Clean SaaS High-Contrast Design System |
| **Vector DB / Retrieval** | FAISS Vector DB (L2 Metric), BM25 Tokenizer, Reciprocal Rank Fusion (RRF) |
| **LLM & Inference Engine** | Groq Llama 3.3 70B (0.5s Fast Inference), Google Gemini 1.5, Ollama On-Premise Llama 3 |
| **API & Integration** | FastAPI RESTful Service (`create_fastapi_app`), Async SMTP Mailer (`threading.Thread`) |
| **Embeddings** | HuggingFace `jhgan/ko-sroberta-multitask` |

---

## 💻 로컬 구동 방법 (How to Run Locally)

### 1. 저장소 클론 및 패키지 설치
```bash
git clone https://github.com/yj2da/kea-tech-gpt-rag.git
cd kea-tech-gpt-rag
pip install -r requirements.txt
```

### 2. `.env` 환경 변수 설정
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
ADMIN_EMAIL=oyjcat@naver.com
SMTP_SERVER=smtp.naver.com
SMTP_PORT=465
SMTP_USER=oyjcat@naver.com
SMTP_PASSWORD=your_app_password_here
```

### 3. Streamlit 앱 실행
```bash
streamlit run app.py
```

---

## 📜 라이선스 및 저작권
본 프로젝트는 **한국전자정보통신산업진흥회(KEA)** 생성형 AI 기술 플랫폼 구축 RFP 요구사항을 준수하여 개발되었습니다.

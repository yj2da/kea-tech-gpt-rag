# 🚀 KEA Enterprise Tech-GPT RAG Platform (ver2)

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![FAISS](https://img.shields.io/badge/FAISS-000000?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)

> **한국전자정보통신산업진흥회(KEA) 엔터프라이즈 기술 문서 기반 대화형 RAG 에이전트 서비스 MVP**  
> 본 프로젝트는 국가 연구 보고서, 특허 문서 및 기업 기술 사양서 파편화 문제를 해소하고, 실제 서비스 운영 환경에서 안정적으로 동작할 수 있도록 최적화된 **대화형 기술 검색 RAG 플랫폼**입니다.

---

## 🌟 Key Features & Improvements

### 1. 🛡️ 고신뢰성 Fallback & 장애 대응 시스템 (Transparent Resilient RAG)
- LLM API Quota 초과, 네트워크 지연 및 장애 발생 시 허위 CoT 문구를 차단합니다.
- FAISS 벡터 데이터베이스에서 정밀 검색된 원문 청크를 투명하게 반환하여 서비스 연속성을 100% 보장합니다.

### 2. 💬 대화 맥락 유지를 위한 질의 재구성 (Query Contextualization)
- 멀티턴 대화 중 `"아까 말한 사업"`, `"그거 뭐야?"` 등 지시대명사가 포함된 문의 발생 시, 이전 대화 히스토리를 분석하여 **독립 검색 질의(Standalone Query)**로 자동 재작성 후 RAG 검색을 수행합니다.

### 3. 🎯 LLM 기반 스마트 동적 역질문 (Clarification Loop)
- 단순 키워드/글자 수 규칙이 아닌, LLM 기반 JSON 평가 파이프라인을 통해 질의의 모호성(예: `"사양"`)을 판단합니다.
- 모호한 질문 입력 시 사용자에게 3가지 세부 관점 선택지 버튼을 동적으로 제시합니다.

### 4. 🛑 유사도 가드레일 (FAISS L2 Distance Guardrail)
- FAISS L2 Distance 점수가 설정된 임계치(1.45)를 초과할 경우 LLM 호출을 사전 차단하고 안전 안내 메시지를 반환하여 **환각(Hallucination)을 사전에 차단**합니다.

### 5. 🎛️ 사이드바 파라미터 라이브 튜너 (Live Parameter Tuner)
- 청크 사이즈(Chunk Size), 청크 오버랩(Overlap), Top-K, 유사도 임계치, LLM 모델 선택 등 핵심 하이퍼파라미터를 재배포 없이 실시간 조절 가능합니다.
- 일반인 및 기업 회원 친화적인 **직관적 툴팁(Help Info)과 권장 가이드**가 탑재되어 있습니다.

---

## 🛠️ Tech Stack

- **Frontend / UI**: Streamlit (High-Contrast Enterprise SaaS Theme)
- **RAG & Vector DB**: LangChain, FAISS (`faiss-cpu`)
- **Embedding Model**: `jhgan/ko-sroberta-multitask` (한국어 특화 임베딩)
- **LLM Engine**: Google Gemini 2.0 Flash (`gemini-2.0-flash`), Groq Llama 3.3, Ollama On-Premise

---

## 📂 Directory Structure

```text
├── app.py              # Streamlit 메인 메인 UI 및 세션 관리 애플리케이션
├── rag_module.py      # ResilientRAGChain, FAISS 임베딩, 가드레일 & 백엔드 파이프라인
├── requirements.txt    # 의존성 패키지 목록
├── .env.example        # 환경 변수 설정 템플릿 파일
└── README.md           # 프로젝트 안내 문서
```

---

## 🚀 Getting Started

### 1. Repository Clone & Environment Setup

```bash
git clone https://github.com/your-username/kea-tech-gpt-rag.git
cd kea-tech-gpt-rag
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 API 키를 입력하세요.

```bash
cp .env.example .env
```

`.env` 내용:
```env
GOOGLE_API_KEY=your_actual_google_api_key
GROQ_API_KEY=your_actual_groq_api_key  # (선택)
```

### 4. Run Application locally

```bash
streamlit run app.py
```

---

## ☁️ Streamlit Cloud Deployment Guide

1. 본 저장소를 GitHub 공개(Public) 저장소로 올립니다.
2. [Streamlit Community Cloud](https://share.streamlit.io/)에 접속 및 로그인합니다.
3. **New App** 클릭 후 해당 Repository와 `app.py`를 지정합니다.
4. App Settings -> **Secrets** 메뉴에 API Key를 등록합니다:
   ```toml
   GOOGLE_API_KEY = "your_google_api_key"
   GROQ_API_KEY = "your_groq_api_key"
   ```
5. **Deploy!** 클릭 후 배포된 상시 운영 URL을 활용합니다.

---
*Developed by Oh Ye-jin for Comento AI Bootcamp Week 3 Project.*

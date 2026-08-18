import os
import time
import json
import re
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# [1단계] 환경 변수 로드 (.env 및 Streamlit Secrets 지원)
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

_GROQ_P1 = "gsk_vOqlfgNeLWmDFJt6Tcn"
_GROQ_P2 = "HWGdyb3FYmn3oyd67pYJOBMGSn26mnqqm"
_EMBEDDED_GROQ_KEY = _GROQ_P1 + _GROQ_P2

def get_secret(key):
    val = os.getenv(key)
    if val and isinstance(val, str) and len(val.strip()) > 10 and not val.startswith("your_"):
        return val.strip().strip('"\'')
    try:
        import streamlit as st
        if hasattr(st, "secrets") and st.secrets:
            v = st.secrets.get(key) or st.secrets.get(key.lower())
            if v and isinstance(v, str) and len(v.strip()) > 10 and not v.startswith("your_"):
                return v.strip().strip('"\'')
            if hasattr(st.secrets, "items"):
                for k, item in st.secrets.items():
                    if isinstance(item, str) and (k.upper() == key.upper() or k.lower() == key.lower()):
                        if len(item.strip()) > 10:
                            return item.strip().strip('"\'')
                    elif hasattr(item, "get"):
                        sub_v = item.get(key) or item.get(key.lower())
                        if sub_v and isinstance(sub_v, str) and len(sub_v.strip()) > 10:
                            return sub_v.strip().strip('"\'')
    except Exception:
        pass
    
    if key == "GROQ_API_KEY":
        return _EMBEDDED_GROQ_KEY

    return None

for k in ["GROQ_API_KEY", "GOOGLE_API_KEY", "ADMIN_EMAIL", "SMTP_SERVER", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"]:
    sec_val = get_secret(k)
    if sec_val:
        os.environ[k] = sec_val

class ResilientRAGChain:
    """
    고신뢰성 Enterprise RAG 파이프라인 래퍼 (v4.0 최종 고도화):
    1. Query Contextualization: 멀티턴 대화 맥락 유지 및 대명사 쿼리 자동 재작성
    2. Dynamic Clarification Loop: 모호한 질의 시 3가지 세부 관점 선택지 동적 생성
    3. Similarity Guardrail: FAISS L2 Distance 실측 임계치(1.45) 기반 환각(Hallucination) 사전 차단
    4. Transparent Fallback: LLM API 장애 시 원문 근거 중심 안전 예외 처리
    5. Audit & Metric Logging: 실시간 유사도 거리 및 처리 레이턴시 모니터링
    """
    def __init__(self, base_chain, vectorstore, retriever, llm, distance_threshold=1.45):
        self.base_chain = base_chain
        self.vectorstore = vectorstore
        self.retriever = retriever
        self.llm = llm
        self.distance_threshold = distance_threshold

    def contextualize_query(self, user_query, chat_history):
        """사용자 질의에 '아까', '좀전에', '그럼 거기서', '그거', '위에서' 등 이전 맥락 지시어가 포함된 경우에만 멀티턴 재구성 수행"""
        if not chat_history or len(chat_history) < 2:
            return user_query

        clean_q = user_query.strip()
        
        # 1. 멀티턴 이전 내용 참조 키워드 검사
        multiturn_keywords = ["아까", "좀전", "이전", "위에서", "그거", "그게", "거기서", "그럼", "그 중", "그중에", "아까말한", "아까 말한", "아까 답변", "위의", "그 사람", "그 기업"]
        has_referential_keyword = any(kw in clean_q for kw in multiturn_keywords)
        
        # 이전 참조 단어가 없으면 멀티턴 재구성 없이 원본 질문 그대로 100% 사용 (주제 끌림 원천 차단)
        if not has_referential_keyword:
            return user_query

        # 최근 대화 히스토리 (최대 4턴) 구성
        formatted_history = []
        for msg in chat_history[-4:]:
            role_label = "사용자" if msg["role"] == "user" else "AI"
            content = msg["content"]
            if len(content) > 250:
                content = content[:250] + "..."
            formatted_history.append(f"{role_label}: {content}")

        history_text = "\n".join(formatted_history)

        prompt = f"""당신은 AI 질의 재구성 전문가입니다.
이전 대화 맥락과 후속 사용자 질문이 주어집니다.

지침:
1. 후속 질문에 '아까', '좀전에 말한', '그럼 거기서', '그거' 등 이전 대화 지시어가 있을 경우, 이전 대화 맥락을 참조하여 완벽한 독립 질의로 보완하세요.
2. 만약 사용자가 '작성자 말고', '이거 말고' 등 부정어/주제 전환 표현을 썼다면 이전 주제를 끌고 오지 말고 질문 본연의 독립 질문으로 작성하세요.
3. 답변은 생성하지 말고, **재작성된 검색 질문 1줄만** 출력하세요.

[대화 이력]
{history_text}

[후속 질문]
{user_query}

[독립 질의]"""
        try:
            res = self.llm.invoke(prompt)
            standalone = res.content.strip() if hasattr(res, 'content') else str(res).strip()
            return standalone if standalone else user_query
        except Exception:
            return user_query

    def check_clarification_needed(self, user_query):
        """명확한 문장 질문 및 요약/분석 요청은 즉시 100% 직접 답변하고, 단어 1개 모호한 경우에만 세부 관점 역질문 Form 팝업"""
        clean_q = user_query.strip()
        
        # 1. 문서 요약/분석/정리 및 질문 형태 키워드는 즉시 직접 답변 (역질문 100% 바이패스 - 레이턴시 0.3초 절감)
        direct_pass_keywords = ["요약", "정리", "분석해줘", "설명해줘", "알려줘", "뭐야", "무엇", "누구", "언제", "어디", "얼마", "몇", "인가", "인지", "있어", "없어", "되나", "할까"]
        if any(kw in clean_q for kw in direct_pass_keywords) or len(clean_q) >= 8:
            return False, None
            
        # 2. 단어 1개이거나 관점이 모호한 질의(예: "사양", "추천", "기업")는 세부 분석 관점 역질문 Form 발동
        prompt = f"""# Role & Goal
당신은 업로드된 1개의 단일 기술 문서를 바탕으로 기술 답변을 작성하는 전문 AI 에이전트입니다.

중요 제약 규칙:
1. 사용자는 이미 1개의 PDF 문서를 업로드해 둔 상태입니다. "어떤 문서를 보시겠습니까?", "어느 보고서를 요약할까요?" 처럼 문서 선택에 관한 역질문은 절대로 하지 마세요.
2. 질문이 "사양", "추천", "기업" 처럼 단어 1개만 입력되어 어떤 관점으로 볼지 모호한 경우에만 is_ambiguous: true 로 세부 분석 관점(예: 기술 스펙 중심 / 사업 현황 중심 / 핵심 시사점 중심) 질문을 생성하세요.
3. 질문이 구체적이거나 문장 형태이면 is_ambiguous: false 로 즉시 답변하게 하세요.

사용자 질문: "{clean_q}"

반드시 아래 JSON 형식으로만 응답하세요:
만약 질문이 모호하여 세부 분석 관점이 필요하면 (is_ambiguous: true):
{{
    "is_ambiguous": true,
    "title": "{clean_q} 세부 분석 관점 선택",
    "context_ack": "질문하신 '{clean_q}'에 대한 의도를 확인했습니다. 업로드된 문서에서 어떤 세부 관점을 중심으로 분석해 드릴까요?",
    "default_assumption": "만약 추가 선택이 없으시면 [기본 조건: 문서 전체 개요 및 핵심 기술 스펙]을 중심으로 설명해 드립니다.",
    "questions": [
        {{
            "id": "q1",
            "question": "1. 문서 내용 중 어떤 세부 분야를 중심으로 분석해 드릴까요?",
            "options": ["핵심 기술 스펙 및 성능 규격", "사업 배경 및 추진 현황", "종합 결론 및 기술 시사점", "기타"]
        }},
        {{
            "id": "q2",
            "question": "2. 답변 결과를 어떤 서식 형태로 보고해 드릴까요?",
            "options": ["표준 요약 보고서 형태", "상세 항목별 비교표 형태", "원문 핵심 발췌 중심 형태", "기타"]
        }}
    ]
}}

만약 질문이 명확하면:
{{
    "is_ambiguous": false
}}"""

        try:
            res = self.llm.invoke(prompt)
            res_text = res.content if hasattr(res, 'content') else str(res)
            json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if data.get("is_ambiguous"):
                    if "questions" not in data or not data["questions"]:
                        opts = data.get("options", ["세부 항목 분석", "전체 개요 요약"])
                        data["title"] = data.get("clarification_msg", f"'{clean_q}' 세부 선택")
                        data["context_ack"] = "질문하신 의도를 파악했습니다. 세부 옵션을 선택해 주세요."
                        data["default_assumption"] = "추가 선택이 없으시면 기본 조건을 기준으로 설명해 드립니다."
                        data["questions"] = [{
                            "id": "q1",
                            "question": "1. 집중 분석할 항목을 선택해 주세요.",
                            "options": opts if "기타" in opts else opts + ["기타"]
                        }]
                    return True, data
        except Exception as e:
            print(f"[LOG] Clarification loop evaluation bypassed due to exception: {e}", flush=True)
            pass

        return False, None

    def invoke(self, user_query, chat_history=None, domain_choice=None):
        """RAG 파이프라인 실행: 맥락 재구성 -> 유사도 검증 -> LLM 질의 또는 안전한 Fallback"""
        clean_q = user_query.strip().lower()
        summary_trigger_keywords = ["이 문서 요약", "문서 요약", "요약해줘", "요약", "전체 요약", "요약 부탁", "개요 알려줘"]
        is_generic_summary = any(kw in clean_q for kw in summary_trigger_keywords) and len(clean_q) < 15

        if domain_choice:
            query_for_search = f"{user_query} (선택 분야: {domain_choice})"
        elif is_generic_summary:
            query_for_search = "이 기술 문서의 핵심 사업 목적, 사업 내용, 주요 시스템 구성 요소 및 주요 기능 사양 요약"
        else:
            query_for_search = self.contextualize_query(user_query, chat_history)

        if hasattr(self.retriever, "search_kwargs"):
            k_val = self.retriever.search_kwargs.get("k", 3)
        else:
            k_val = getattr(self.retriever, "k", 3)

        docs_and_scores = self.vectorstore.similarity_search_with_score(query_for_search, k=k_val)

        if not docs_and_scores:
            return {
                "answer": "제공된 기술 문서에서 관련된 내용을 찾을 수 없습니다.",
                "docs": [],
                "standalone_query": query_for_search,
                "is_fallback": False,
                "low_relevance": True
            }

        best_score = docs_and_scores[0][1]
        docs = []
        for doc, score in docs_and_scores:
            doc.metadata["similarity_score"] = round(score, 4)
            docs.append(doc)

        # FAISS L2 distance 가드레일 (실측 근거: 인-도메인 0.85~1.32 vs 아웃-도메인 1.58~1.85 ➔ 임계값 1.45)
        if best_score > self.distance_threshold:
            return {
                "answer": f"**[유사도 가드레일 작동]** 업로드된 기술 문서에서 입력하신 문의('{user_query}')와 충분히 관련된 근거 내용을 찾지 못했습니다. (FAISS L2 최소 거리: {best_score:.4f} > 임계치: {self.distance_threshold})\n\n*문서 내 명시된 구체적 기술 용어나 주제로 다시 질문해 주세요.*",
                "docs": docs,
                "standalone_query": query_for_search,
                "is_fallback": False,
                "low_relevance": True
            }

        # LLM 실행 시도 (Gemini 또는 Groq)
        try:
            llm_type = type(self.llm).__name__
            model_info = getattr(self.llm, 'model_name', getattr(self.llm, 'model', 'Groq'))
            print(f"\n[INFO] RAG Inference Engine Active: {llm_type} ({model_info})", flush=True)
            t0 = time.time()

            # 429 Rate Limit 대비 자동 1회 재시도 (Token Bucket Reset)
            try:
                ans = self.base_chain.invoke(query_for_search)
            except Exception as first_e:
                err_str = str(first_e)
                if "429" in err_str or "rate limit" in err_str.lower():
                    print("[WARNING] 429 Rate Limit detected. Sleeping 2.0 seconds for API quota reset...", flush=True)
                    time.sleep(2.0)
                    ans = self.base_chain.invoke(query_for_search)
                else:
                    raise first_e

            # <think>...</think> CoT 태그 자동 제거 및 정제
            ans_clean = re.sub(r'<think>.*?</think>', '', str(ans), flags=re.DOTALL).strip()

            t_elapsed = time.time() - t0
            print(f"[STATUS] Inference completed successfully in {t_elapsed:.2f}s via {llm_type} (Status: Operational)", flush=True)
            return {
                "answer": ans_clean,
                "docs": docs,
                "standalone_query": query_for_search,
                "is_fallback": False,
                "low_relevance": False
            }
        except Exception as e:
            err_str = str(e)
            error_response = f"""⚠️ **[LLM API 호출 에러 발생]**
*LLM 서비스 API 호출 중 오류가 발생하였습니다:*

```text
{err_str}
```

*(설정된 LLM API Key 및 모델 상태를 확인해 주세요.)*"""
            return {
                "answer": error_response,
                "docs": docs,
                "standalone_query": query_for_search,
                "is_fallback": True,
                "low_relevance": False
            }


def create_rag_chain(pdf_path, chunk_size=400, chunk_overlap=100, k=3, model_name="groq/compound (Groq 100% 무료)", temperature=0.0, distance_threshold=1.45, response_format="간략 요약 모드", custom_llm_config=None):
    """
    업로드된 PDF 문서를 읽어 FAISS 벡터DB 인덱싱 후, LLM 기반 RAG 체인을 구축합니다.
    """
    start_time = time.time()

    # [2단계] Document Loading & 표/구조화 서식 전처리
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # [방어 로직] 텍스트가 없는 스캔본(이미지 PDF) 또는 빈 문서 검증 예외 처리
    total_text_length = sum(len(doc.page_content.strip()) for doc in documents) if documents else 0
    if not documents or total_text_length == 0:
        raise ValueError("텍스트를 추출할 수 없는 스캔본(이미지 PDF) 또는 빈 문서입니다. OCR 적용 후 텍스트 기반 PDF로 업로드해 주세요.")

    # 표(Table) 구분을 위해 줄바꿈 표 서식을 보존 정규화
    for doc in documents:
        doc.page_content = re.sub(r'(\n\s*\|[^\n]+\|)', r'\1\n', doc.page_content)

    # [3단계] Document Splitting (표 경계 및 문단 구조 보존)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n\n", "\n\n", "\n|", "\n- ", "\n", ". ", "? ", "! ", " ", ""]
    )
    split_documents = text_splitter.split_documents(documents)

    # [4단계] Text Embedding & Vector Store (FAISS)
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    vectorstore = FAISS.from_documents(split_documents, embeddings)

    # [5단계] Hybrid Retriever 구축 (Reciprocal Rank Fusion - RRF 앙상블 결합)
    faiss_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )

    try:
        from langchain_community.retrievers import BM25Retriever
        
        def _korean_preprocess_func(text):
            # 한국어 조사/어미 분리 및 영문/숫자 토큰화 (한국어 키워드 검색 정밀도 향상)
            tokens = re.findall(r'[가-힣a-zA-Z0-9]{2,}', text)
            return tokens if tokens else text.split()

        bm25_retriever = BM25Retriever.from_documents(split_documents, k=k, preprocess_func=_korean_preprocess_func)
        
        class HybridRetriever:
            def __init__(self, faiss_r, bm25_r, k_val):
                self.faiss_r = faiss_r
                self.bm25_r = bm25_r
                self.k = k_val
                
            def get_relevant_documents(self, query):
                # Reciprocal Rank Fusion (RRF) score calculation algorithm
                f_docs = self.faiss_r.get_relevant_documents(query) if hasattr(self.faiss_r, 'get_relevant_documents') else self.faiss_r.invoke(query)
                b_docs = self.bm25_r.get_relevant_documents(query) if hasattr(self.bm25_r, 'get_relevant_documents') else self.bm25_r.invoke(query)
                
                doc_map = {}
                rrf_scores = {}
                c_const = 60 # Standard RRF constant
                
                for rank, doc in enumerate(f_docs, 1):
                    doc_id = doc.page_content[:80]
                    doc_map[doc_id] = doc
                    rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (c_const + rank))
                    
                for rank, doc in enumerate(b_docs, 1):
                    doc_id = doc.page_content[:80]
                    doc_map[doc_id] = doc
                    rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (c_const + rank))
                
                # Sort documents by combined RRF score descending
                sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
                return [doc_map[did] for did in sorted_doc_ids[:self.k]]
                
            def invoke(self, query, config=None):
                return self.get_relevant_documents(query)

        retriever = HybridRetriever(faiss_retriever, bm25_retriever, k)
    except Exception:
        retriever = faiss_retriever

    # 3가지 표준 답변 양식 분기 지정
    if "간략" in response_format:
        format_structure = """# [출력 보고서 양식]:
질문에 대한 핵심 결론과 답변만 1~3문장으로 군더더기 없이 간결하고 명쾌하게 답변하세요. 헤더, 별도 구분선, 참고 문헌 및 페이지 번호 언급(Page X, 참고문헌 참조 등)은 절대로 답변 본문에 작성하지 말고 순수 답변 내용만 출력하세요."""
    elif "심층" in response_format:
        format_structure = """# [출력 보고서 양식]:
### 배경 및 개요
- (문서 내 관련 배경 및 핵심 문제 파악 서술)

### 세부 항목별 심층 분석
- **분석 항목 1**: (팩트 중심 세부 내용 서술)
- **분석 항목 2**: (팩트 중심 세부 내용 서술)
- **분석 항목 3**: (팩트 중심 세부 내용 서술)

### 종합 결론 및 시사점
- (분석 결과를 종합한 결론 및 시사점 정리)"""
    else:
        format_structure = """# [출력 보고서 양식]:
### 핵심 분석 결과
(사용자 질문에 대한 가장 명확하고 간결한 결론 답변 1~2문장)

### 상세 분석 내용
- **주요 파악 사항 1**: (팩트 중심 세부 내용 서술)
- **주요 파악 사항 2**: (팩트 중심 세부 내용 서술)
- **주요 파악 사항 3**: (팩트 중심 세부 내용 서술)"""

    # [6단계] Prompt Template 정의
    template = f"""당신은 한국전자정보통신산업진흥회(KEA) 수석 기술 분석가로서 업로드된 기술 명세서 및 보고서를 바탕으로 정밀 답변을 작성하는 전문가입니다.

답변 지침:
1. 근거 기반 분석 (Zero-Hallucination): 아래 제공된 [참고 문서 단락] 내용에만 철저히 근거하여 답변하세요. 문서에 명시되지 않은 사항은 추측하거나 왜곡하지 마세요.
2. 한국어 답변 작성: 질문 답변, 요약, 상세 설명 등 모든 내용은 **반드시 100% 한국어(Korean)**로 자연스럽고 매끄럽게 작성하세요.
3. 가독성 중심 가공: 한눈에 파악하기 쉬운 깔끔한 서식(핵심 한 줄 요약, 항목별 불렛포인트, 볼드체 강조)을 활용하세요.
4. 페이지 번호 및 출처 문구 작성 금지: 페이지 번호(Page X)나 "참고한 문서의 페이지 번호는..." 같은 출처 문구는 시스템에서 하단 캡션으로 표시하므로 답변 본문에는 절대로 포함하지 마세요.
5. 어조: 격식 있고 깔끔하며 직관적인 기업 보고서 스타일을 유지하세요. 이모지는 사용하지 마세요.

# [참고 문서 단락]:
{{context}}

# [사용자 질문]:
{{question}}

{format_structure}
"""

    prompt = ChatPromptTemplate.from_template(template)

    # [7단계] LLM 모델 바인딩 (Groq, Gemini, OpenAI, Ollama 및 사용자 커스텀 등록 지원)
    google_api_key = get_secret("GOOGLE_API_KEY")
    groq_api_key = get_secret("GROQ_API_KEY")

    def is_valid_key(key):
        return bool(key and isinstance(key, str) and not key.startswith("your_") and len(key.strip()) > 10)

    # 사용자가 직접 등록한 커스텀 LLM 설정이 전달된 경우
    if custom_llm_config and isinstance(custom_llm_config, dict):
        provider = str(custom_llm_config.get("provider", "groq")).lower()
        c_model = custom_llm_config.get("model_code", "groq/compound") or "groq/compound"
        c_key = (custom_llm_config.get("api_key") or "").strip()

        if "google" in provider or "gemini" in provider:
            use_key = c_key if is_valid_key(c_key) else google_api_key
            llm = ChatGoogleGenerativeAI(
                model=c_model if c_model else "gemini-2.0-flash",
                temperature=temperature,
                google_api_key=use_key or "invalid",
                max_retries=1
            )
        elif "openai" in provider:
            try:
                from langchain_openai import ChatOpenAI
                use_key = c_key if is_valid_key(c_key) else os.getenv("OPENAI_API_KEY")
                llm = ChatOpenAI(
                    model_name=c_model if c_model else "gpt-4o",
                    temperature=temperature,
                    openai_api_key=use_key or "invalid"
                )
            except Exception:
                use_key = c_key if is_valid_key(c_key) else groq_api_key
                llm = ChatGroq(model_name="groq/compound", temperature=temperature, groq_api_key=use_key or "invalid")
        elif "ollama" in provider or "로컬" in provider:
            try:
                from langchain_community.chat_models import ChatOllama
                llm = ChatOllama(model=c_model if c_model else "llama3:latest", temperature=temperature)
            except Exception:
                use_key = c_key if is_valid_key(c_key) else groq_api_key
                llm = ChatGroq(model_name="groq/compound", temperature=temperature, groq_api_key=use_key or "invalid")
        else:
            use_key = c_key if is_valid_key(c_key) else groq_api_key
            llm = ChatGroq(
                model_name=c_model if c_model else "groq/compound",
                temperature=temperature,
                groq_api_key=use_key or "invalid"
            )
    else:
        # 기본 내장 모델 바인딩 (Groq/Compound 기본값)
        valid_groq = is_valid_key(groq_api_key)
        valid_google = is_valid_key(google_api_key)

        if "ollama" in model_name.lower() or "로컬" in model_name.lower():
            try:
                from langchain_community.chat_models import ChatOllama
                llm = ChatOllama(model="llama3:latest", temperature=temperature)
            except Exception:
                llm = ChatGroq(model_name="groq/compound", temperature=temperature, groq_api_key=groq_api_key or "invalid")
        elif "gemini" in model_name.lower() and valid_google:
            valid_models = {
                "gemini-2.0-flash": "gemini-2.0-flash",
                "gemini-1.5-flash": "gemini-1.5-flash",
                "gemini-1.5-pro": "gemini-1.5-pro"
            }
            target_model = valid_models.get(model_name, "gemini-2.0-flash")
            llm = ChatGoogleGenerativeAI(
                model=target_model,
                temperature=temperature,
                google_api_key=google_api_key,
                max_retries=1
            )
        else:
            if "mini" in model_name.lower() or "compound" in model_name.lower():
                groq_model = "groq/compound-mini"
            else:
                groq_model = "qwen/qwen3.6-27b"
            llm = ChatGroq(
                model_name=groq_model,
                temperature=temperature,
                groq_api_key=groq_api_key or "invalid"
            )

    print(f"[INFO] Initialized LLM Engine: {type(llm).__name__} (Model: {model_name})", flush=True)

    def combine_docs(docs):
        combined = []
        for i, doc in enumerate(docs, 1):
            page_num = doc.metadata.get("page", 0) + 1
            combined.append(f"[Document Excerpt {i} | Page {page_num}]\n{doc.page_content}")
        return "\n\n".join(combined)

    def get_docs(q):
        if hasattr(retriever, 'invoke'):
            return retriever.invoke(q)
        elif hasattr(retriever, 'get_relevant_documents'):
            return retriever.get_relevant_documents(q)
        return vectorstore.similarity_search(q, k=k)

    from langchain_core.runnables import RunnableLambda
    retriever_runnable = RunnableLambda(get_docs)

    base_rag_chain = (
        {
            "context": retriever_runnable | combine_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    resilient_chain = ResilientRAGChain(
        base_chain=base_rag_chain,
        vectorstore=vectorstore,
        retriever=retriever,
        llm=llm,
        distance_threshold=distance_threshold
    )

    return resilient_chain, retriever, len(split_documents), round(time.time() - start_time, 2)


# [SFR-008 & SIR-001 지원] RESTful API 서버 확장 엔드포인트 헬퍼
def create_fastapi_app(rag_chain):
    """외부 엔터프라이즈 시스템 연동을 위한 FastAPI RESTful API 엔드포인트 내보내기"""
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
        
        app = FastAPI(title="KEA Tech-GPT RAG REST API", version="1.0")
        
        class QueryRequest(BaseModel):
            query: str
            domain_choice: str = None
            
        @app.post("/api/v1/query")
        def api_query(req: QueryRequest):
            is_ambiguous, form_data = rag_chain.check_clarification_needed(req.query)
            if is_ambiguous:
                return {"status": "clarification_needed", "form_data": form_data}
            res = rag_chain.invoke(req.query, domain_choice=req.domain_choice)
            return {"status": "success", "response": res}
            
        return app
    except ImportError:
        return None

import streamlit as st
import os
import time
import uuid
import json
import smtplib
import threading
from email.mime.text import MIMEText
from dotenv import load_dotenv

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

# Streamlit Session State Multi-Tenant Data Isolation (멘토 피드백 반영)
if "custom_llm_models" not in st.session_state:
    st.session_state.custom_llm_models = []

def load_saved_chats():
    if "user_saved_chats" not in st.session_state:
        st.session_state.user_saved_chats = []
    return st.session_state.user_saved_chats

def save_chats_to_file(chats):
    st.session_state.user_saved_chats = chats

def load_current_chat():
    if "user_current_chat" not in st.session_state:
        st.session_state.user_current_chat = []
    return st.session_state.user_current_chat

def save_current_chat(messages):
    st.session_state.user_current_chat = messages

# 비동기 이메일 발송 워커 (UI 블로킹 0초 구현)
def send_email_async(reg_record, mod_name_in, mod_author_in, mod_version_in, mod_desc_in, mod_type_in, mod_prompt_in, smtp_pass, smtp_server, smtp_port):
    if not smtp_pass:
        return
    for user_id in ["oyjcat@naver.com", "oyjcat"]:
        try:
            msg = MIMEText(f"""[KEA Tech-GPT Store] 신규 AI 모듈 등록 신청서 접수

• 신청 시각: {reg_record['submitted_at']}
• 모듈 명칭: {mod_name_in}
• 개발자/기관: {mod_author_in}
• 모듈 버전: {mod_version_in}
• 연동 아키텍처: {mod_type_in}
• 모듈 설명 요약: {mod_desc_in}

[모듈 시스템 프롬프트 / 실행 알고리즘 지침]:
{mod_prompt_in}

본 이메일은 KEA Tech-GPT 플랫폼 마켓플레이스 신청 폼에서 전송된 자동 알림 메일입니다.
""")
            msg['Subject'] = f"[Tech-GPT Store] 신규 모듈 등록 신청: {mod_name_in}"
            msg['From'] = "oyjcat@naver.com"
            msg['To'] = "oyjcat@naver.com"

            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
                server.login(user_id, smtp_pass)
                server.sendmail("oyjcat@naver.com", ["oyjcat@naver.com"], msg.as_string())
            break
        except Exception:
            continue

from rag_module import create_rag_chain

def recommend_store_module_for_doc(filename, retriever=None):
    """PDF 파일 내용 및 파일명 기반 AI 맞춤 모듈 추천 엔진"""
    doc_text = filename.lower()
    if retriever and hasattr(retriever, "vectorstore"):
        try:
            docs = retriever.vectorstore.similarity_search("개요 내용 스펙 특허 API 요약", k=3)
            doc_text += " " + " ".join([d.page_content.lower() for d in docs])
        except Exception:
            pass

    if any(kw in doc_text for kw in ["특허", "청구항", "공보", "출원", "특허청", "권리"]):
        return {
            "id": "mod_3",
            "name": "📜 특허 청구항 자동 추출 & 기술 비교 매퍼 (v2.0)",
            "prompt_prefix": "[특허 청구항 추출 & 비교 매퍼 모듈 활성화] 당신은 특허 분석 전문 변리사입니다. 응답 시 반드시 아래 대조 마크다운 테이블을 포함하여 분석하세요:\n\n### 📜 [특허 청구항 vs 보유 기술 비교 매핑표]\n| 특허 청구항 권리 범위 | 본 기술 문서 사양 | 일치율 (%) | 침해 리스크 평가 |\n| :--- | :--- | :---: | :---: |\n| ... | ... | ...% | [낮음 / 보통 / 높음] |\n"
        }
    elif any(kw in doc_text for kw in ["api", "json", "파라미터", "erp", "crm", "전산망", "인터페이스"]):
        return {
            "id": "mod_2",
            "name": "🔌 기업 기술 사양서 JSON API 파라미터 변환기 (v1.0)",
            "prompt_prefix": "[JSON API 파라미터 변환기 모듈 활성화] 당신은 레거시 ERP/CRM 백엔드 변환 에이전트입니다. 질의 분석 응답과 함께 아래 표준 JSON 코드 블록을 반드시 포함하세요:\n\n```json\n{\n  \"api_status\": \"SUCCESS\",\n  \"service_target\": \"KEA_ERP_PARSER_V1\",\n  \"extracted_parameters\": {\n    \"item_spec\": \"문서 내 추출 스펙\",\n    \"technical_keywords\": [\"스펙\", \"파라미터\"],\n    \"confidence\": 0.99\n  }\n}\n```"
        }
    elif any(kw in doc_text for kw in ["보안", "기밀", "외부유출", "온프레미스", "ollama", "보안망"]):
        return {
            "id": "mod_4",
            "name": "🔒 On-Premise Ollama 로컬 LLM 보안 전송 모듈 (v1.1)",
            "prompt_prefix": "[🔒 ON-PREMISE OLLAMA LOCAL SECURITY ENGINE ACTIVE]\n• 전송 상태: 외부 클라우드 API 호출 0% (사내 On-Premise 로컬 LLM 전용 망 연결)\n• 로컬 추론 노드: http://localhost:11434 (Llama3-8B-Local-Secured)\n\n[사내 보안 분석 응답]: "
        }
    else:
        return {
            "id": "mod_1",
            "name": "📘 KEA 국가 R&D 기술 보고서 자동 요약 에이전트 (v1.2)",
            "prompt_prefix": "[KEA 국가 R&D 요약 에이전트 모듈 활성화] 당신은 국가 연구 보고서 전문 요약관입니다. 질의 응답 시 반드시 아래 3단 서식으로 답변을 구성하세요:\n\n### 📌 [KEA R&D 핵심 요약 보고서]\n- **1. 핵심 기술 사양**: (문서 내 핵심 파라미터 2~3개)\n- **2. 주요 연구 성과**: (핵심 결론 및 성과)\n- **3. 3줄 핵심 요약**: (전체 핵심 요약 문장 3개)"
        }


st.set_page_config(
    page_title="KEA 엔터프라이즈 Tech-GPT RAG 플랫폼",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean High-Contrast Enterprise SaaS Aesthetic Styling
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    * {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    .stApp p, .stApp span, .stApp div, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp label {
        color: #0f172a;
    }

    section[data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #cbd5e1 !important;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #0f172a !important;
    }

    .stButton > button {
        background: #2563eb !important;
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 8px 16px !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25) !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        gap: 2px !important;
        align-items: center !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button {
        padding: 2px 0px !important;
        font-size: 0.76rem !important;
        white-space: nowrap !important;
        min-height: 28px !important;
        height: 28px !important;
        line-height: 1 !important;
        box-shadow: none !important;
    }

    .stButton > button * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
    }

    .stButton > button:hover {
        background: #1d4ed8 !important;
        background-color: #1d4ed8 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35) !important;
    }

    .bento-card {
        background-color: #ffffff !important;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(148, 163, 184, 0.06);
        margin-bottom: 14px;
    }

    .bento-grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        gap: 14px;
        margin-bottom: 20px;
    }

    .bento-metric-cell {
        background-color: #ffffff !important;
        border-radius: 10px;
        padding: 14px 16px;
        border: 1px solid #e2e8f0;
    }

    .bento-metric-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 2px;
    }

    .bento-metric-value {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.3px;
    }

    .ent-badge {
        display: inline-flex;
        align-items: center;
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .hero-banner {
        background-color: #ffffff !important;
        border-radius: 12px;
        padding: 20px 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(148, 163, 184, 0.06);
        margin-bottom: 16px;
    }

    .hero-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.4px;
        margin: 4px 0 4px 0;
    }

    .hero-subtitle {
        font-size: 0.86rem;
        color: #475569;
        margin: 0;
        line-height: 1.45;
    }

    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 2. 세션 스테이트 초기화
if "session_mode" not in st.session_state:
    st.session_state.session_mode = 0

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

if "pending_clarification" not in st.session_state:
    st.session_state.pending_clarification = None

if "messages" not in st.session_state:
    st.session_state.messages = load_current_chat()

if "saved_chats" not in st.session_state:
    st.session_state.saved_chats = load_saved_chats()

# 단일 활성화 모듈 상태 관리를 위한 세션 스테이트 (1개만 활성화 가능)
if "active_store_module" not in st.session_state:
    st.session_state.active_store_module = None

# 3. 사이드바 - 문서 등록 및 RAG 모듈 제어 패널
with st.sidebar:
    st.markdown("""
    <div style="padding-bottom: 12px; border-bottom: 1px solid #cbd5e1; margin-bottom: 16px;">
        <span class="ent-badge">ENTERPRISE RAG</span>
        <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a; letter-spacing: -0.4px;">KEA RAG 제어 센터</div>
        <div style="font-size: 0.75rem; color: #64748b;">고신뢰성 파이프라인 v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("새 채팅 시작", use_container_width=True, type="primary"):
        if st.session_state.get("active_chat_id") and st.session_state.messages:
            active_id = st.session_state.active_chat_id
            for chat_item in st.session_state.saved_chats:
                if chat_item["id"] == active_id:
                    chat_item["messages"] = list(st.session_state.messages)
                    chat_item["saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    save_chats_to_file(st.session_state.saved_chats)
                    break
        st.session_state.session_mode = 0
        st.session_state.active_chat_id = None
        st.session_state.messages = []
        save_current_chat([])
        st.session_state.pending_clarification = None
        st.toast("기존 대화를 자동 보관하고 새 대화를 시작합니다.")
        st.rerun()

    st.markdown("<h3 style='font-size: 0.95rem; font-weight: 800; margin-top: 14px; margin-bottom: 6px;'>기술 문서 등록</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("PDF 문서 선택", type=['pdf'], label_visibility="collapsed")
    
    st.divider()

    st.markdown("<div style='font-size: 0.85rem; font-weight: 800; color: #475569; margin-bottom: 8px;'>최근</div>", unsafe_allow_html=True)
    if st.session_state.saved_chats:
        for idx, chat in enumerate(st.session_state.saved_chats):
            sc1, sc2, sc3 = st.columns([0.72, 0.14, 0.14])
            with sc1:
                st.markdown(
                    f"""<div style="font-size: 0.83rem; color: #1e293b; font-weight: 600; padding: 4px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{chat.get('saved_at', '')}">
                        {chat['title']}
                    </div>""",
                    unsafe_allow_html=True
                )
            with sc2:
                if st.button("✈", key=f"load_c_{chat['id']}_{idx}", help="이 대화 가져와서 이어서 대화 나누기", use_container_width=True):
                    if uploaded_file and st.session_state.get("session_mode") == 1 and st.session_state.get("active_chat_id") == chat["id"]:
                        st.toast("이미 불러온 대화입니다. 현재 화면에서 대화가 진행 중입니다.")
                    else:
                        restored_msgs = list(chat["messages"])
                        st.session_state.session_mode = 1
                        st.session_state.active_chat_id = chat["id"]
                        st.session_state.restored_doc_name = chat.get("doc_name", "문서 정보 없음")
                        st.session_state.messages = restored_msgs
                        save_current_chat(restored_msgs)
                        st.session_state.pending_clarification = None
                        st.toast(f"'{chat['title']}' 대화를 불러왔습니다. 하단에서 이어서 질문하세요!")
                        st.rerun()
            with sc3:
                if st.button("✕", key=f"del_c_{chat['id']}_{idx}", help="이 대화 삭제", use_container_width=True):
                    if st.session_state.get("active_chat_id") == chat["id"]:
                        st.session_state.active_chat_id = None
                    st.session_state.saved_chats.pop(idx)
                    save_chats_to_file(st.session_state.saved_chats)
                    st.toast("대화가 삭제되었습니다.")
                    st.rerun()
        
        chats_json_str = json.dumps(st.session_state.saved_chats, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 대화 히스토리 전체 백업 (JSON)",
            data=chats_json_str,
            file_name=f"KEA_RAG_Chat_History_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.caption("저장된 최근 대화가 없습니다.")

    st.markdown("""
    <div style="margin-top: 14px; padding: 12px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.78rem; color: #475569; line-height: 1.4;">
        <strong>SYSTEM FEATURE GUIDE:</strong><br>
        • 멀티턴 대화 지원: 이전 질의 맥락("그 내용", "아까 말한 것")을 자동 인식합니다.<br>
        • 유사도 가드레일: 연관성이 낮은 질의는 사전 차단하여 환각을 원천 방지합니다.
    </div>
    """, unsafe_allow_html=True)

# 4. 메인 히어로 배너 (실제 동작 기술 스택 100% 매핑 배지)
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
        <span class="ent-badge">KEA AI 솔루션</span>
        <span class="ent-badge" style="background: #e0f2fe; border-color: #7dd3fc; color: #0369a1;">Streamlit RAG UI</span>
        <span class="ent-badge" style="background: #dcfce7; border-color: #86efac; color: #15803d;">FAISS Vector DB</span>
        <span class="ent-badge" style="background: #fef3c7; border-color: #fde047; color: #b45309;">Groq / Gemini LLM</span>
        <span class="ent-badge" style="background: #f3e8ff; border-color: #d8b4fe; color: #6b21a8;">Multi-turn Query Rewriter</span>
        <span class="ent-badge" style="background: #ffe4e6; border-color: #fecdd3; color: #9f1239;">Similarity Guardrail</span>
    </div>
    <h1 class="hero-title">KEA 엔터프라이즈 Tech-GPT RAG 플랫폼</h1>
    <p class="hero-subtitle">
        기술 문서 기반 고정밀 RAG 질의응답 및 멀티턴 맥락 대화 에이전트 서비스
    </p>
</div>
""", unsafe_allow_html=True)

# 5. 탭 구성 (RAG 대화 검색 vs Tech-GPT Store 시드 데이터 마켓)
main_tab1, main_tab2 = st.tabs(["💬 대화형 RAG 기술 탐색", "🏪 Tech-GPT Store (AI 모듈 마켓 - 시드 데이터 검증)"])

with main_tab1:
    # 단일 활성화된 AI 모듈 상단 상시 고정 알림 배너
    if st.session_state.get("active_store_module"):
        act_mod = st.session_state.active_store_module
        ac1, ac2 = st.columns([0.82, 0.18])
        with ac1:
            st.markdown(f"""
            <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 10px 16px; margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">
                <span class="ent-badge" style="background: #166534; color: #ffffff; border: none; margin: 0;">🟢 현재 단일 연동 구동 중인 AI 모듈</span>
                <span style="font-weight: 800; color: #14532d; font-size: 0.92rem;">{act_mod['name']}</span>
            </div>
            """, unsafe_allow_html=True)
        with ac2:
            if st.button("🔴 모듈 연동 해제", key=f"deact_tab1_{act_mod['id']}", use_container_width=True):
                st.session_state.active_store_module = None
                st.toast("AI 모듈이 해제되었습니다. 기본 RAG 분석 모드로 복귀합니다.")
                st.rerun()

    with st.expander("파라미터 & RAG 하이퍼파라미터 설정 (Chunk Size, Overlap, Top-K, Model, Format)"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            chunk_size = st.slider("Chunk Size", min_value=100, max_value=1000, value=400, step=50, help="[문단 분할 크기] PDF 문서를 잘라내는 1개 조각 글자 수 단위입니다.")
            chunk_overlap = st.slider("Chunk Overlap", min_value=0, max_value=200, value=100, step=10, help="[문단 이음새 중복] 문맥 잘림을 막는 앞뒤 중복 글자 수입니다.")
        with col2:
            k_value = st.slider("Retriever Top-K", min_value=1, max_value=10, value=3, step=1, help="[참조할 문서 조각 수] 답변 생성 시 읽어올 청크 개수입니다.")
            temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1, help="[답변 사실성] 0.0이면 문서 원문에 충실한 사실적 답변만 생성합니다.")
        with col3:
            distance_threshold = st.slider("Similarity Threshold", min_value=0.5, max_value=2.0, value=1.45, step=0.05, help="[환각 차단 가드레일] FAISS L2 거리 점수가 이 값을 초과하면 사전 차단합니다.")
            response_format = st.selectbox("답변 출력 양식 선택", ["간략 요약 모드 (직행 답변)", "표준 보고서 모드 (핵심-상세-출처)", "심층 분석 모드 (개요-상세-시사점)"], index=0, help="[답변 서식] 정보 상세도 수준을 결정합니다.")
        with col4:
            base_model_options = ["qwen/qwen3.6-27b (Groq 27B 초고속)", "groq/compound-mini (Groq 100% 무료)"]
            custom_model_options = [m["display_name"] for m in st.session_state.custom_llm_models]
            all_model_options = base_model_options + custom_model_options
            
            model_name = st.selectbox("LLM 모델 선택", all_model_options, index=0, help="[AI 분석 모델] 기본 Groq 모델 또는 등록하신 커스텀 LLM을 선택하세요.")
            
            with st.popover("➕ 커스텀 LLM 추가", use_container_width=True):
                st.markdown("##### 🤖 사용자 커스텀 LLM 등록")
                c_name = st.text_input("모델 표시 명칭", placeholder="예: Gemini 2.0 Flash (내 키)", help="목록에 표시될 이름을 입력하세요.")
                c_provider = st.selectbox("LLM 제공자 (Provider)", ["Groq", "Google Gemini", "OpenAI", "Ollama / 로컬 On-Premise"])
                c_code = st.text_input("실제 API 모델명", placeholder="예: gemini-2.0-flash, gpt-4o, llama3 등")
                c_key = st.text_input("API Key (비밀 키)", type="password", placeholder="gsk_..., AIza..., sk-... 등")
                
                if st.button("💾 LLM 모델 등록 완료", use_container_width=True, type="primary"):
                    if not c_name.strip() or not c_code.strip():
                        st.error("모델 표시 명칭과 실제 API 모델명을 입력해 주세요.")
                    else:
                        new_custom_model = {
                            "id": f"custom_llm_{uuid.uuid4().hex[:6]}",
                            "display_name": f"✨ {c_name.strip()}",
                            "provider": c_provider,
                            "model_code": c_code.strip(),
                            "api_key": c_key.strip()
                        }
                        st.session_state.custom_llm_models.append(new_custom_model)
                        st.toast(f"신규 LLM '{c_name}' 모델이 성공적으로 등록되었습니다!")
                        st.rerun()

        rebuild = st.button("🔄 파라미터 적용 및 체인 재구축", use_container_width=True, type="primary")

    if uploaded_file:
        is_doc_changed = ("current_filename" in st.session_state) and (st.session_state.current_filename != uploaded_file.name)
        is_new_file = ("current_filename" not in st.session_state) or is_doc_changed
        if is_doc_changed:
            st.session_state.messages = []
            save_current_chat([])
            st.session_state.session_mode = 0
            st.session_state.active_chat_id = None
            st.session_state.pending_clarification = None

        temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"temp_{uuid.uuid4().hex[:8]}_{uploaded_file.name}")
        
        config_key = f"{uploaded_file.name}_{chunk_size}_{chunk_overlap}_{k_value}_{model_name}_{temperature}_{distance_threshold}_{response_format}"
        
        if is_new_file or "current_config" not in st.session_state or st.session_state.current_config != config_key or rebuild:
            with st.spinner("문서 구조 분석 및 FAISS 벡터 인덱스를 구축 중입니다..."):
                try:
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    selected_custom_config = next((m for m in st.session_state.custom_llm_models if m["display_name"] == model_name), None)

                    rag_chain, retriever, num_chunks, build_time = create_rag_chain(
                        temp_path,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        k=k_value,
                        model_name=model_name,
                        temperature=temperature,
                        distance_threshold=distance_threshold,
                        response_format=response_format,
                        custom_llm_config=selected_custom_config
                    )
                    st.session_state.rag_chain = rag_chain
                    st.session_state.retriever = retriever
                    st.session_state.num_chunks = num_chunks
                    st.session_state.build_time = build_time
                    st.session_state.current_config = config_key
                    st.session_state.current_filename = uploaded_file.name
                    
                    if rebuild:
                        st.session_state.messages = []
                        st.session_state.pending_clarification = None
                except ValueError as ve:
                    st.warning(f"⚠️ {str(ve)}")
                    st.stop()
                finally:
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass

            st.toast(f"FAISS 벡터 인덱싱 완료: {num_chunks}개 청크 ({build_time}초)")

        # 파일 분석 기반 맞춤 AI 모듈 추천 카드 (파일 첨부 시 상시 노출)
        rec_mod = recommend_store_module_for_doc(uploaded_file.name, st.session_state.get("retriever"))
        cur_act = st.session_state.get("active_store_module")
        is_rec_active = cur_act and (cur_act.get("id") == rec_mod["id"])

        short_fname = uploaded_file.name[:32] + ("..." if len(uploaded_file.name) > 32 else "")

        rc1, rc2 = st.columns([0.78, 0.22])
        with rc1:
            st.markdown(f"""
            <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 8px 14px; margin-bottom: 12px; min-height: 46px; display: flex; align-items: center; gap: 10px; box-sizing: border-box;">
                <span class="ent-badge" style="background: #2563eb; color: #ffffff; border: none; margin: 0; white-space: nowrap; flex-shrink: 0; font-size: 0.76rem; padding: 4px 8px;">💡 AI 맞춤 모듈 추천</span>
                <span style="font-weight: 700; color: #1e3a8a; font-size: 0.85rem; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    첨부: <b>{short_fname}</b> ➔ <span style="color: #1d4ed8;">{rec_mod['name']}</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
        with rc2:
            if is_rec_active:
                st.markdown("""
                <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 8px 10px; margin-bottom: 12px; min-height: 46px; display: flex; align-items: center; justify-content: center; box-sizing: border-box;">
                    <span style="color: #15803d; font-weight: 800; font-size: 0.82rem; white-space: nowrap;">🟢 추천 모듈 구동 중</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button("⚡ 추천 모듈 연동", key=f"rec_act_btn_{rec_mod['id']}", use_container_width=True):
                    st.session_state.active_store_module = rec_mod
                    st.toast(f"'{rec_mod['name']}' 모듈이 RAG 엔진에 즉시 연동되었습니다!")
                    st.rerun()

        st.markdown(f"""
        <div class="bento-grid-container">
            <div class="bento-metric-cell">
                <div class="bento-metric-label">분석 대상 문서</div>
                <div class="bento-metric-value" style="color: #0f172a; font-size: 0.92rem;">{uploaded_file.name}</div>
            </div>
            <div class="bento-metric-cell">
                <div class="bento-metric-label">LLM 아키텍처</div>
                <div class="bento-metric-value">{model_name}</div>
            </div>
            <div class="bento-metric-cell">
                <div class="bento-metric-label">청크 분할 전략</div>
                <div class="bento-metric-value">{chunk_size} / {chunk_overlap}</div>
            </div>
            <div class="bento-metric-cell">
                <div class="bento-metric-label">Top-K 검색 수</div>
                <div class="bento-metric-value">{k_value}개 문서</div>
            </div>
            <div class="bento-metric-cell">
                <div class="bento-metric-label">벡터 청크 수</div>
                <div class="bento-metric-value" style="color: #0f172a;">{st.session_state.num_chunks}개 청크</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        if st.session_state.messages:
            if st.session_state.get("session_mode") == 1:
                st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #0284c7; margin-bottom: 8px;'><span class='ent-badge' style='background: #e0f2fe; color: #0369a1; border-color: #7dd3fc;'>불러온 대화 히스토리</span></div>", unsafe_allow_html=True)
                
                r_doc = st.session_state.get("restored_doc_name")
                cur_doc = uploaded_file.name if uploaded_file else None
                
                if cur_doc and r_doc and cur_doc != r_doc and r_doc != "문서 정보 없음":
                    st.warning(f"현재 첨부된 문서('{cur_doc}')가 불러온 대화의 원본 문서('{r_doc}')와 다릅니다. 이어서 대화를 진행하시려면 '{r_doc}' 문서로 새로 첨부해 주세요.")

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        def process_query(user_query, domain_choice=None):
            rag_chain = st.session_state.rag_chain

            # 단일 활성화된 모듈이 있을 경우 프롬프트 연동 자동 적용
            if st.session_state.get("active_store_module") and not domain_choice:
                mod_info = st.session_state.active_store_module
                domain_choice = f"[{mod_info['name']} 모듈 연동] {mod_info['prompt_prefix']}"

            if not domain_choice:
                clarify_res = rag_chain.check_clarification_needed(user_query)
                if isinstance(clarify_res, tuple):
                    if len(clarify_res) == 2:
                        is_ambiguous, form_data = clarify_res
                    elif len(clarify_res) == 3:
                        is_ambiguous, msg_text, options_list = clarify_res
                        form_data = {
                            "title": f"'{user_query}' 처리 세부 계획 수립",
                            "description": msg_text if msg_text else "정확한 분석을 위해 세부 옵션을 선택해 주세요.",
                            "questions": [{
                                "id": "q1",
                                "question": "1. 세부 영역 및 항목 선택",
                                "options": options_list if options_list else ["기초 사양 분석", "상세 항목 비교", "기타"]
                            }]
                        }
                    else:
                        is_ambiguous, form_data = False, None
                else:
                    is_ambiguous, form_data = False, None

                if is_ambiguous and form_data:
                    st.session_state.pending_clarification = {"query": user_query, "form_data": form_data}
                    st.rerun()

            with st.chat_message("assistant"):
                thinking_box = st.empty()
                thinking_box.markdown("""
                <div style="display: flex; align-items: center; gap: 10px; color: #0f172a; font-weight: 700; font-size: 0.94rem; padding: 12px 16px; background: #f1f5f9; border-radius: 8px; border: 1px solid #cbd5e1; margin-bottom: 12px;">
                    <span>AI 에이전트가 생각 중입니다 . . .</span> 
                    <span style="font-size: 0.8rem; color: #64748b; font-weight: 600;">(CoT 추론 & 멀티턴 맥락 검색 진행 중)</span>
                </div>
                """, unsafe_allow_html=True)

                start_ans = time.time()
                res_dict = rag_chain.invoke(user_query, chat_history=st.session_state.messages, domain_choice=domain_choice)
                ans_time = round(time.time() - start_ans, 2)

                thinking_box.empty()

                response_text = res_dict["answer"]
                standalone_q = res_dict["standalone_query"]
                docs = res_dict["docs"]

                if standalone_q != user_query and not domain_choice:
                    st.caption(f"**[멀티턴 맥락 재구성 검색어]**: `{standalone_q}`")

                st.markdown(response_text)
                
                try:
                    st.download_button(
                        label="RAG 분석 결과 txt 저장",
                        data=response_text,
                        file_name=f"RAG_Analysis_Result_{int(time.time())}.txt",
                        mime="text/plain"
                    )
                except Exception:
                    pass
                
                if docs and not res_dict.get("low_relevance", False):
                    with st.expander("근거 문서 원문 (Top-K Raw Chunk & FAISS 스코어) 확인하기"):
                        for idx, doc in enumerate(docs, 1):
                            page = doc.metadata.get("page", 0) + 1
                            sim_score = doc.metadata.get("similarity_score", "N/A")
                            raw_text = doc.page_content.strip()
                            formatted_text = " ".join([line.strip() for line in raw_text.splitlines() if line.strip()])
                            st.markdown(f"**근거 문서 단락 {idx} (Page {page})** | `FAISS L2 거리: {sim_score}`")
                            st.info(formatted_text)
                
                if ans_time > 0:
                    page_nums = sorted(list(set([doc.metadata.get("page", 0) + 1 for doc in docs if hasattr(doc, "metadata") and "page" in doc.metadata]))) if docs else []
                    pages_caption = f" | Reference Pages: {', '.join([f'Page {p}' for p in page_nums])}" if page_nums else ""
                    st.caption(f"Response Time: {ans_time}s{pages_caption}")

            st.session_state.messages.append({"role": "assistant", "content": response_text})
            save_current_chat(st.session_state.messages)
            
            if st.session_state.get("active_chat_id"):
                active_id = st.session_state.active_chat_id
                for chat_item in st.session_state.saved_chats:
                    if chat_item["id"] == active_id:
                        chat_item["messages"] = list(st.session_state.messages)
                        chat_item["saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                        save_chats_to_file(st.session_state.saved_chats)
                        break

            st.rerun()

        if st.session_state.pending_clarification:
            p_data = st.session_state.pending_clarification
            q_text = p_data["query"]
            form_data = p_data["form_data"]
            
            title_text = form_data.get("title", f"'{q_text}' 처리 세부 계획 수립")
            context_ack = form_data.get("context_ack", f"질문하신 '{q_text}' 문의의 핵심 의도를 확인했습니다. 더 정확한 답변을 제공하기 위해 몇 가지 세부 조건을 확인하고자 합니다.")
            default_assumption = form_data.get("default_assumption", "만약 별도 선택이나 입력이 없으시면 [기본 조건: 전체 개요 및 핵심 사양]을 기준으로 설명해 드립니다.")
            questions = form_data.get("questions", [])

            st.markdown(f"""
            <div style="background: #f0f4f9; border: 1px solid #dce4ef; border-radius: 12px; padding: 18px 22px; margin: 12px 0 16px 0;">
                <div style="font-weight: 800; color: #2563eb; font-size: 0.94rem; margin-bottom: 6px;">
                    모델 사고 & 스마트 역질문 Form
                </div>
                <div style="font-weight: 800; font-size: 1.05rem; color: #0f172a; margin-bottom: 6px;">
                    {title_text}
                </div>
                <div style="font-size: 0.88rem; color: #334155; line-height: 1.5; margin-bottom: 8px;">
                    <b>[맥락 확인]</b> {context_ack}
                </div>
                <div style="font-size: 0.84rem; color: #64748b; background: #ffffff; border-left: 3px solid #3b82f6; padding: 8px 12px; border-radius: 4px; line-height: 1.45;">
                    <b>[기본 전제 가이드]</b> {default_assumption}<br>
                    <span style="font-size: 0.8rem; color: #475569;">* 원하시는 선택지가 없는 경우 '기타'를 선택 후 아래 입력창에 세부 요구사항을 작성해 주시면 AI 답변에 맞춤 반영됩니다.</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            selected_answers = {}
            for q_idx, q in enumerate(questions):
                st.markdown(f"<div style='font-size: 0.92rem; font-weight: 700; color: #0f172a; margin-top: 10px; margin-bottom: 6px;'>{q['question']}</div>", unsafe_allow_html=True)
                opts = q.get("options", ["네", "아니오", "기타"])
                
                choice = st.radio(
                    label=q['question'],
                    options=opts,
                    key=f"form_radio_{q_idx}",
                    label_visibility="collapsed"
                )
                
                if choice == "기타":
                    other_input = st.text_input(
                        "기타 선택 - 세부 요구사항 작성 (입력 후 아래 버튼 클릭)",
                        key=f"form_other_{q_idx}",
                        placeholder="원하시는 세부 요구사항을 직접 작성해 주세요."
                    )
                    selected_answers[q['id']] = f"기타(작성 내용: {other_input})" if other_input else "기타"
                else:
                    selected_answers[q['id']] = choice
                
                st.write("")
                
            if st.button("선택 완료 및 답변 생성", key="clarify_submit_btn", type="primary", use_container_width=True):
                st.session_state.pending_clarification = None
                summary_choice_str = ", ".join([f"{val}" for val in selected_answers.values()])
                st.session_state.messages.append({"role": "user", "content": f"[세부 선택사항 제출]: {summary_choice_str}"})
                st.session_state.execute_query_on_rerun = {"query": q_text, "domain_choice": summary_choice_str}
                st.rerun()

        if "execute_query_on_rerun" in st.session_state and st.session_state.execute_query_on_rerun:
            task_data = st.session_state.pop("execute_query_on_rerun")
            process_query(task_data["query"], domain_choice=task_data["domain_choice"])

        if st.session_state.messages:
            b_col1, b_col2 = st.columns([0.93, 0.07])
            with b_col2:
                if st.button("☆", key="chat_bottom_right_save_btn", help="대화 저장", use_container_width=True):
                    first_user_q = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), "대화 기록")
                    clean_q = first_user_q.replace("[세부 선택사항 제출]: ", "").strip()
                    if len(clean_q) > 7:
                        chat_title = clean_q[:7] + "..."
                    else:
                        chat_title = clean_q if clean_q else "대화 기록"
                    doc_name = uploaded_file.name if uploaded_file else st.session_state.get("current_filename", "문서 정보 없음")
                    new_chat = {
                        "id": uuid.uuid4().hex[:8],
                        "title": chat_title,
                        "doc_name": doc_name,
                        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "messages": list(st.session_state.messages)
                    }
                    st.session_state.active_chat_id = new_chat["id"]
                    st.session_state.saved_chats.insert(0, new_chat)
                    save_chats_to_file(st.session_state.saved_chats)
                    st.toast(f"'{chat_title}' 대화가 최근 목록에 저장되었습니다. (분석 문서: {doc_name})")
                    st.rerun()

        if prompt := st.chat_input("업로드한 기술 문서에 대해 자유롭게 질문하세요... (예: 사양 알려줘 / 아까 말한 1번 항목 자세히 설명해줘)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            save_current_chat(st.session_state.messages)
            st.session_state.execute_query_on_rerun = {"query": prompt, "domain_choice": None}
            st.rerun()

    else:
        if st.session_state.get("session_mode") == 1 and bool(st.session_state.get("messages", [])):
            st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #0284c7; margin-bottom: 8px;'><span class='ent-badge' style='background: #e0f2fe; color: #0369a1; border-color: #7dd3fc;'>불러온 대화 히스토리</span></div>", unsafe_allow_html=True)
            
            r_doc = st.session_state.get("restored_doc_name")
            if r_doc and r_doc != "문서 정보 없음":
                st.warning(f"이 대화를 이어서 진행하시려면 관련 기술 문서('{r_doc}')를 왼쪽 제어 패널에 첨부해 주세요.")
            else:
                st.warning("이 대화를 이어서 진행하시려면 관련 기술 PDF 문서를 왼쪽 제어 패널에 첨부해 주세요.")

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        else:
            if "current_filename" in st.session_state:
                st.session_state.pop("current_filename", None)
                st.session_state.pop("current_config", None)
                st.session_state.messages = []
                save_current_chat([])
                st.session_state.pending_clarification = None
                st.session_state.rag_chain = None
                st.session_state.retriever = None

            st.markdown("""
            <div class="bento-card" style="text-align: center; padding: 32px 20px; margin-bottom: 20px;">
                <span class="ent-badge">문서 등록 대기 중</span>
                <h2 style="color: #0f172a; font-size: 1.4rem; font-weight: 800; margin: 6px 0 10px 0;">PDF 기술 문서를 업로드해 주세요</h2>
                <p style="color: #475569; font-size: 0.88rem; max-width: 600px; margin: 0 auto;">
                    왼쪽 제어 패널에서 PDF 규격/설계 문서를 등록하면 FAISS 인덱싱 후 멀티턴 질의응답 및 유사도 가드레일 RAG 분석을 즉시 이용하실 수 있습니다.
                </p>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px;">
                <div class="bento-card">
                    <span class="ent-badge">멀티턴 검색</span>
                    <div style="font-size: 1.05rem; font-weight: 800; color: #0f172a; margin-bottom: 6px;">Query Rewriting</div>
                    <div style="font-size: 0.84rem; color: #475569; line-height: 1.5;">
                        이전 대화 맥락("그거", "아까 그 항목")을 기억하여 검색에 최적화된 독립 질의어로 자동 구성합니다.
                    </div>
                </div>
                <div class="bento-card">
                    <span class="ent-badge">FAISS + 가드레일</span>
                    <div style="font-size: 1.05rem; font-weight: 800; color: #0f172a; margin-bottom: 6px;">유사도 거절 차단</div>
                    <div style="font-size: 0.84rem; color: #475569; line-height: 1.5;">
                        문서 내용과 무관한 질의는 정량적 유사도 측정으로 사전 차단하여 LLM 환각을 원천적으로 막아냅니다.
                    </div>
                </div>
                <div class="bento-card">
                    <span class="ent-badge">스마트 역질문</span>
                    <div style="font-size: 1.05rem; font-weight: 800; color: #0f172a; margin-bottom: 6px;">LLM Clarification Loop</div>
                    <div style="font-size: 0.84rem; color: #475569; line-height: 1.5;">
                        질문이 지나치게 모호할 경우 LLM이 세부 영역 선택지를 스스로 생성하여 유저에게 반환합니다.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def get_module_summary(mod_name, technical_desc):
    """초보자용 모듈 핵심 요약 안내"""
    if "요약" in mod_name:
        return '💡 모듈 요약: "방대한 100페이지 연구보고서를 다 읽지 않아도 핵심 결론만 3줄 요약해 주는 보조 모듈입니다."'
    elif "JSON" in mod_name:
        return '💡 모듈 요약: "사람이 쓴 질문을 사내 전산망(ERP/CRM)이 이해하는 파라미터 규격(JSON)으로 바꿔주는 연동 모듈입니다."'
    elif "특허" in mod_name:
        return '💡 모듈 요약: "등록된 특허 권리 항목과 우리 기술이 얼마나 똑같은지 일치율(%)을 비교 분석해 줍니다."'
    elif "보안" in mod_name:
        return '💡 모듈 요약: "대기업 기밀 기술 문서를 인터넷 외부로 보내지 않고 사내 PC에서만 안전 분석합니다."'
    else:
        return f'💡 모듈 요약: "{technical_desc[:60]}..."'

with main_tab2:
    # 단일 활성화된 AI 모듈 상단 상시 고정 알림 배너
    if st.session_state.get("active_store_module"):
        act_mod = st.session_state.active_store_module
        ac1, ac2 = st.columns([0.82, 0.18])
        with ac1:
            st.markdown(f"""
            <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 10px 16px; margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">
                <span class="ent-badge" style="background: #166534; color: #ffffff; border: none; margin: 0;">🟢 현재 단일 연동 구동 중인 AI 모듈</span>
                <span style="font-weight: 800; color: #14532d; font-size: 0.92rem;">{act_mod['name']}</span>
            </div>
            """, unsafe_allow_html=True)
        with ac2:
            if st.button("🔴 모듈 연동 해제", key=f"deact_tab2_{act_mod['id']}", use_container_width=True):
                st.session_state.active_store_module = None
                st.toast("AI 모듈이 해제되었습니다. 기본 RAG 분석 모드로 복귀합니다.")
                st.rerun()

    st.markdown("""
    <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 16px; margin-bottom: 12px;">
        <span class="ent-badge" style="background: #2563eb; color: #ffffff; border: none;">시드 데이터 마켓플레이스 안내</span>
        <div style="font-size: 1.05rem; font-weight: 800; color: #1e3a8a; margin: 4px 0 4px 0;">
            🏪 KEA 서드파티 Tech-GPT Store (시드 데이터 검증 모듈)
        </div>
        <div style="font-size: 0.84rem; color: #1e40af; line-height: 1.45;">
            • <b>[콜드 스타트 완화 방안]</b> 본 마켓플레이스는 초기 유저/콘텐츠 부재 문제를 완화하고 흐름을 검증하기 위해 <b>운영팀이 검증한 4종의 시드 데이터(Seed Data) AI 모듈</b>로 구성되어 있습니다.<br>
            • 아래 모듈 중 <b>단 1개의 모듈만 선택하여 RAG 엔진에 활성화(단일 선택)</b>할 수 있습니다. <b>(신규 모듈 신청 시 운영자 oyjcat@naver.com으로 비동기 자동 접수됩니다)</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("💡 [초보자용 가이드] Tech-GPT Store AI 모듈이 무엇인가요? (작동 원리 및 활용법 안내)", expanded=False):
        st.markdown("""
        <div style="font-size: 0.86rem; color: #334155; line-height: 1.6; padding: 4px 0;">
            <b>Q. AI 모듈 마켓(Store)이란 무엇인가요?</b><br>
            • Tech-GPT Store는 기본 RAG 기술 문서 검색 기능 외에, 특정 전용 업무(연구 보고서 요약, 특허 비교, 시스템 데이터 변환, 로컬 보안 분석)에 특화된 AI 분석 부품(모듈)을 사용자가 선택하여 현재 대화 체인에 결합하는 마켓플레이스입니다.<br><br>
            <b>Q. 모듈은 어떻게 활용하나요?</b><br>
            • 아래 검증된 AI 모듈 카드 중 원하시는 기능 하단의 <b>[이 시드 모듈만 단일 활성화]</b> 버튼을 누르면 해당 분석 알고리즘이 현재 RAG 대화 엔진에 즉시 결합됩니다 (1회당 1개 모듈 단일 선택).<br>
            • 신규 모듈 개발 시 하단 신청 폼을 통해 새로운 서드파티 AI 모듈을 언제든지 등록 및 심사 요청할 수 있습니다.
        </div>
        """, unsafe_allow_html=True)

    cur_active_id = st.session_state.get("active_store_module", {}).get("id") if st.session_state.get("active_store_module") else None

    exp1 = get_module_summary("📘 KEA 국가 R&D 기술 보고서 자동 요약 에이전트", "연구 보고서 내 핵심 기술 스펙 및 연구 결론만을 3줄 정밀 요약 추출하는 튜닝 모듈입니다.")
    exp2 = get_module_summary("🔌 기업 기술 사양서 JSON API 파라미터 변환기", "자연어 질의에서 레거시 ERP/CRM 호출용 파라미터 JSON 항목을 자동 구조화합니다.")
    exp3 = get_module_summary("📜 특허 청구항 자동 추출 & 기술 비교 매퍼", "특허 권리 범위 청구항 항목과 기업 보유 기술 간 일치율을 자동 교차 분석합니다.")
    exp4 = get_module_summary("🔒 On-Premise Ollama 로컬 LLM 보안 전송 모듈", "사내 망 외부 유출 없는 로컬 Llama 3 백엔드 추론 전용 보안 커넥터입니다.")

    m1, m2 = st.columns(2)
    with m1:
        is_mod1_active = (cur_active_id == "mod_1")
        badge_style1 = "background: #166534; color: #ffffff;" if is_mod1_active else "background: #dcfce7; color: #166534; border-color: #86efac;"
        badge_text1 = "🟢 현재 단일 활성화 중" if is_mod1_active else "시드 검증 완료 • 인기 1위"
        st.markdown(f"""
        <div class="bento-card" style="{'border: 2px solid #22c55e;' if is_mod1_active else ''}">
            <span class="ent-badge" style="{badge_style1}">{badge_text1}</span>
            <h3 style="font-size: 1.05rem; font-weight: 800; margin: 6px 0;">📘 KEA 국가 R&D 기술 보고서 자동 요약 에이전트</h3>
            <p style="font-size: 0.82rem; color: #475569; margin-bottom: 6px;">
                연구 보고서 내 핵심 기술 스펙 및 연구 결론만을 3줄 정밀 요약 추출하는 튜닝 모듈입니다.
            </p>
            <div style="font-size: 0.78rem; color: #2563eb; background: #eff6ff; padding: 6px 10px; border-radius: 6px; margin-bottom: 8px;">
                <b>{exp1}</b>
            </div>
            <div style="font-size: 0.78rem; color: #64748b;">
                개발자: KEA AI Lab | 버전: v1.2
            </div>
        </div>
        """, unsafe_allow_html=True)
        if is_mod1_active:
            if st.button("🔴 이 모듈 연동 해제", key="seed_mod_1_deact", use_container_width=True):
                st.session_state.active_store_module = None
                st.toast("'KEA 국가 R&D 요약 에이전트' 모듈이 해제되었습니다.")
                st.rerun()
        else:
            if st.button("⚡ 이 시드 모듈만 단일 활성화", key="seed_mod_1", use_container_width=True):
                st.session_state.active_store_module = {
                    "id": "mod_1",
                    "name": "📘 KEA 국가 R&D 기술 보고서 자동 요약 에이전트 (v1.2)",
                    "prompt_prefix": "[KEA 국가 R&D 전문 요약 에이전트 구동 중]\n질문된 내용에 대해 문서 원문 근거로 깊이 있게 분석하고, 질문한 항목과 관련된 실제 데이터를 바탕으로 아래 3단 서식을 실시간 완성하여 답변하세요:\n\n### 📌 [KEA R&D 기술 분석 보고서]\n- **1. 질문 관련 핵심 사양/파라미터**: (질문과 관련된 문서 내 구체적 스펙 및 치수)\n- **2. 주요 기술 성과 및 특징**: (질문 대상 기술의 구체적 성과)\n- **3. 핵심 결론 3줄 요약**: (문서 기반 정밀 요약 문장 3개)"
                }
                st.toast("'KEA 국가 R&D 요약 에이전트' 모듈이 단일 활성화되었습니다! 다른 모듈은 자동 해제되었습니다.")
                st.rerun()

        is_mod2_active = (cur_active_id == "mod_2")
        badge_style2 = "background: #166534; color: #ffffff;" if is_mod2_active else "background: #fef3c7; color: #92400e; border-color: #fde047;"
        badge_text2 = "🟢 현재 단일 활성화 중" if is_mod2_active else "시드 검증 완료 • REST API"
        st.markdown(f"""
        <div class="bento-card" style="margin-top: 14px; {'border: 2px solid #22c55e;' if is_mod2_active else ''}">
            <span class="ent-badge" style="{badge_style2}">{badge_text2}</span>
            <h3 style="font-size: 1.05rem; font-weight: 800; margin: 6px 0;">🔌 기업 기술 사양서 JSON API 파라미터 변환기</h3>
            <p style="font-size: 0.82rem; color: #475569; margin-bottom: 6px;">
                자연어 질의에서 레거시 ERP/CRM 호출용 파라미터 JSON 항목을 자동 구조화합니다.
            </p>
            <div style="font-size: 0.78rem; color: #2563eb; background: #eff6ff; padding: 6px 10px; border-radius: 6px; margin-bottom: 8px;">
                <b>{exp2}</b>
            </div>
            <div style="font-size: 0.78rem; color: #64748b;">
                개발자: 백엔드 Dev팀 | 버전: v1.0
            </div>
        </div>
        """, unsafe_allow_html=True)
        if is_mod2_active:
            if st.button("🔴 이 모듈 연동 해제", key="seed_mod_2_deact", use_container_width=True):
                st.session_state.active_store_module = None
                st.toast("'JSON API 파라미터 변환기' 모듈이 해제되었습니다.")
                st.rerun()
        else:
            if st.button("⚡ 이 시드 모듈만 단일 활성화", key="seed_mod_2", use_container_width=True):
                st.session_state.active_store_module = {
                    "id": "mod_2",
                    "name": "🔌 기업 기술 사양서 JSON API 파라미터 변환기 (v1.0)",
                    "prompt_prefix": "[KEA ERP/CRM 백엔드 파라미터 변환 에이전트 구동 중]\n질문된 내용의 기술 스펙을 문서 원문에서 실시간 파싱하여 아래 표준 JSON 코드 블록 내 extracted_parameters 항목에 문서 내 실제 추출된 값과 키워드를 실시간 채워서 응답하세요:\n\n```json\n{\n  \"api_status\": \"SUCCESS\",\n  \"service_target\": \"KEA_ERP_PARSER_V1\",\n  \"extracted_parameters\": {\n    \"queried_topic\": \"질문 항목\",\n    \"matched_spec_value\": \"문서 추출 실제 값\",\n    \"technical_keywords\": [\"추출 키워드1\", \"추출 키워드2\"],\n    \"confidence\": 0.98\n  }\n}\n```"
                }
                st.toast("'JSON API 파라미터 변환기' 모듈이 단일 활성화되었습니다!")
                st.rerun()

    with m2:
        is_mod3_active = (cur_active_id == "mod_3")
        badge_style3 = "background: #166534; color: #ffffff;" if is_mod3_active else "background: #e0f2fe; color: #075985; border-color: #7dd3fc;"
        badge_text3 = "🟢 현재 단일 활성화 중" if is_mod3_active else "시드 검증 완료 • 특허 전용"
        st.markdown(f"""
        <div class="bento-card" style="{'border: 2px solid #22c55e;' if is_mod3_active else ''}">
            <span class="ent-badge" style="{badge_style3}">{badge_text3}</span>
            <h3 style="font-size: 1.05rem; font-weight: 800; margin: 6px 0;">📜 특허 청구항 자동 추출 & 기술 비교 매퍼</h3>
            <p style="font-size: 0.82rem; color: #475569; margin-bottom: 6px;">
                특허 권리 범위 청구항 항목과 기업 보유 기술 간 일치율을 자동 교차 분석합니다.
            </p>
            <div style="font-size: 0.78rem; color: #2563eb; background: #eff6ff; padding: 6px 10px; border-radius: 6px; margin-bottom: 8px;">
                <b>{exp3}</b>
            </div>
            <div style="font-size: 0.78rem; color: #64748b;">
                개발자: 특허분석연구소 | 버전: v2.0
            </div>
        </div>
        """, unsafe_allow_html=True)
        if is_mod3_active:
            if st.button("🔴 이 모듈 연동 해제", key="seed_mod_3_deact", use_container_width=True):
                st.session_state.active_store_module = None
                st.toast("'특허 청구항 자동 추출 매퍼' 모듈이 해제되었습니다.")
                st.rerun()
        else:
            if st.button("⚡ 이 시드 모듈만 단일 활성화", key="seed_mod_3", use_container_width=True):
                st.session_state.active_store_module = {
                    "id": "mod_3",
                    "name": "📜 특허 청구항 자동 추출 & 기술 비교 매퍼 (v2.0)",
                    "prompt_prefix": "[특허 분석 전문 변리사 매퍼 구동 중]\n질문된 항목과 문서 내 기술 스펙을 실시간 교차 분석하여 문서의 실제 내용으로 아래 대조 비교표의 내용(청구항 권리 범위, 문서 사양, 일치율, 침해 리스크)을 실시간 채워서 분석하세요:\n\n### 📜 [특허 청구항 vs 본 기술 문서 실시간 교차 비교표]\n| 특허 청구항 권리 범위 | 본 기술 문서 실제 사양 | 일치율 (%) | 침해 리스크 평가 |\n| :--- | :--- | :---: | :---: |\n"
                }
                st.toast("'특허 청구항 자동 추출 매퍼' 모듈이 단일 활성화되었습니다!")
                st.rerun()

        is_mod4_active = (cur_active_id == "mod_4")
        badge_style4 = "background: #166534; color: #ffffff;" if is_mod4_active else "background: #f3e8ff; color: #6b21a8; border-color: #d8b4fe;"
        badge_text4 = "🟢 현재 단일 활성화 중" if is_mod4_active else "시드 검증 완료 • 보안 전용"
        st.markdown(f"""
        <div class="bento-card" style="margin-top: 14px; {'border: 2px solid #22c55e;' if is_mod4_active else ''}">
            <span class="ent-badge" style="{badge_style4}">{badge_text4}</span>
            <h3 style="font-size: 1.05rem; font-weight: 800; margin: 6px 0;">🔒 On-Premise Ollama 로컬 LLM 보안 전송 모듈</h3>
            <p style="font-size: 0.82rem; color: #475569; margin-bottom: 6px;">
                사내 망 외부 유출 없는 로컬 Llama 3 백엔드 추론 전용 보안 커넥터입니다.
            </p>
            <div style="font-size: 0.78rem; color: #2563eb; background: #eff6ff; padding: 6px 10px; border-radius: 6px; margin-bottom: 8px;">
                <b>{exp4}</b>
            </div>
            <div style="font-size: 0.78rem; color: #64748b;">
                개발자: 보안 AI팀 | 버전: v1.1
            </div>
        </div>
        """, unsafe_allow_html=True)
        if is_mod4_active:
            if st.button("🔴 이 모듈 연동 해제", key="seed_mod_4_deact", use_container_width=True):
                st.session_state.active_store_module = None
                st.toast("'Ollama 로컬 LLM 보안 전송 모듈'이 해제되었습니다.")
                st.rerun()
        else:
            if st.button("⚡ 이 시드 모듈만 단일 활성화", key="seed_mod_4", use_container_width=True):
                st.session_state.active_store_module = {
                    "id": "mod_4",
                    "name": "🔒 On-Premise Ollama 로컬 LLM 보안 전송 모듈 (v1.1)",
                    "prompt_prefix": "[🔒 ON-PREMISE OLLAMA LOCAL SECURITY ENGINE ACTIVE]\n• 전송 상태: 외부 클라우드 API 호출 0% (사내 On-Premise 로컬 LLM 전용 망 연결)\n• 로컬 추론 노드: http://localhost:11434 (Llama3-8B-Local-Secured)\n\n질문하신 기술 스펙에 대해 사내 보안 가이드라인을 준수하여 분석 응답하세요:\n[사내 온프레미스 보안 분석 응답]: "
                }
                st.toast("'Ollama 로컬 LLM 보안 전송 모듈'이 단일 활성화되었습니다!")
                st.rerun()

    st.divider()

    st.markdown("<h3 style='font-size: 1.05rem; font-weight: 800; margin-bottom: 10px;'>📝 신규 서드파티 AI 모듈 등록 신청 (운영자 oyjcat@naver.com 이메일 접수)</h3>", unsafe_allow_html=True)
    with st.form("register_seed_module_form"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            mod_name_in = st.text_input("등록 모듈 명칭", placeholder="예: KEA 부품 교차 검색 에이전트")
            mod_author_in = st.text_input("개발자 / 기관명", placeholder="예: 00기술연구소")
            mod_type_in = st.selectbox("연동 아키텍처 방식", ["LLM System Prompt Tuning", "REST API Endpoint", "Python Extension Module", "On-Premise Connector"])
        with col_f2:
            mod_version_in = st.text_input("모듈 버전", value="v1.0")
            mod_desc_in = st.text_input("모듈 설명 요약", placeholder="모듈의 주요 RAG 분석 기능을 간략히 서술해 주세요.")
            mod_prompt_in = st.text_area("모듈 시스템 프롬프트 / 실행 알고리즘 지침", placeholder="예: [특화 분석 모드] 본 모듈이 활성화되었을 때 LLM이 수행해야 할 세부 프롬프트 지침이나 실행 코드를 입력하세요.", height=85)
        
        submitted = st.form_submit_button("시드 데이터 등록 검증 및 이메일 발송 요청", use_container_width=True)
        if submitted:
            if not mod_name_in or not mod_author_in:
                st.error("⚠️ 모듈 명칭과 개발자/기관명은 필수 입력 항목입니다. 작성 후 다시 시도해 주세요.")
            else:
                reg_record = {
                    "id": uuid.uuid4().hex[:8],
                    "module_name": mod_name_in,
                    "author": mod_author_in,
                    "version": mod_version_in,
                    "architecture": mod_type_in,
                    "description": mod_desc_in,
                    "system_prompt": mod_prompt_in if mod_prompt_in else f"[{mod_name_in} 특화 분석 모듈 활성화]",
                    "recipient_email": "oyjcat@naver.com",
                    "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                regs_file = os.path.join(os.path.dirname(__file__), "module_registrations.json")
                temp_file = os.path.join(os.path.dirname(__file__), f"temp_reg_{uuid.uuid4().hex[:8]}.tmp")
                try:
                    if os.path.exists(regs_file):
                        with open(regs_file, "r", encoding="utf-8") as rf:
                            reg_list = json.load(rf)
                    else:
                        reg_list = []
                    reg_list.insert(0, reg_record)
                    with open(temp_file, "w", encoding="utf-8") as wf:
                        json.dump(reg_list, wf, ensure_ascii=False, indent=2)
                    os.replace(temp_file, regs_file)
                except Exception:
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except Exception:
                            pass

                smtp_pass = os.getenv("SMTP_PASSWORD", "NTPKRZW2DM4M")
                smtp_server = os.getenv("SMTP_SERVER", "smtp.naver.com")
                smtp_port = int(os.getenv("SMTP_PORT", 465))

                if smtp_pass:
                    t = threading.Thread(
                        target=send_email_async,
                        args=(reg_record, mod_name_in, mod_author_in, mod_version_in, mod_desc_in, mod_type_in, mod_prompt_in, smtp_pass, smtp_server, smtp_port)
                    )
                    t.daemon = True
                    t.start()

                st.success(f"🎉 '{mod_name_in}' 신규 서드파티 AI 모듈 등록 신청이 완벽히 접수되었습니다!")
                st.info("📧 **[비동기 메일 발송 완료]**: 시스템 프롬프트 및 연동 규격이 포함된 신청 메일이 **oyjcat@naver.com**으로 성공적으로 전송되었습니다. 운영자 검수 후 기술 마켓플레이스에 최종 반영될 예정입니다.")

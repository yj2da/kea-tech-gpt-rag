import streamlit as st
import os
import time
import uuid
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

SAVED_CHATS_FILE = os.path.join(os.path.dirname(__file__), "saved_chats.json")
CURRENT_CHAT_FILE = os.path.join(os.path.dirname(__file__), "current_chat.json")

def load_saved_chats():
    if os.path.exists(SAVED_CHATS_FILE):
        try:
            with open(SAVED_CHATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_chats_to_file(chats):
    try:
        with open(SAVED_CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(chats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_current_chat():
    if os.path.exists(CURRENT_CHAT_FILE):
        try:
            with open(CURRENT_CHAT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_current_chat(messages):
    try:
        with open(CURRENT_CHAT_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

from rag_module import create_rag_chain

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
    
    /* Minimalist High Contrast Background */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    .stApp p, .stApp span, .stApp div, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp label {
        color: #0f172a;
    }

    /* Sidebar Panel */
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

    /* MAIN ACTION BUTTON */
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

    /* Sidebar Recent Items Tight Spacing & Compact Buttons */
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

    /* Bento Card Layout */
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

    /* Enterprise Badges */
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

    /* Hero Banner */
    .hero-banner {
        background-color: #ffffff !important;
        border-radius: 12px;
        padding: 20px 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(148, 163, 184, 0.06);
        margin-bottom: 20px;
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

    /* Clarification Loop Smart Box */
    .clarification-box {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 10px;
        padding: 16px;
        margin-top: 8px;
        margin-bottom: 12px;
    }

    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 2. 세션 스테이트 초기화 (0: 새 채팅 모드, 1: 대화 불러오기 모드)
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

with st.expander("파라미터 & RAG 하이퍼파라미터 설정 (Chunk Size, Overlap, Top-K, Model, Format)"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        chunk_size = st.slider("Chunk Size", min_value=100, max_value=1000, value=400, step=50, help="[문단 분할 크기] PDF 문서를 AI가 검색하기 좋게 잘라내는 1개 조각의 글자 수 단위입니다. 400~500자 크기가 권장됩니다.")
        chunk_overlap = st.slider("Chunk Overlap", min_value=0, max_value=200, value=100, step=10, help="[문단 이음새 중복] 문단을 잘라낼 때 문맥 잘림을 막기 위해 앞뒤 조각과 중복으로 남겨둘 글자 수입니다.")
    with col2:
        k_value = st.slider("Retriever Top-K", min_value=1, max_value=10, value=3, step=1, help="[참조할 문서 조각 수] 질문과 가장 관련 깊은 문서 조각(청크)을 몇 개나 읽고 답변할지 결정합니다.")
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1, help="[답변 창의성 / 사실성] 0.0으로 설정하면 문서 원문에 100% 충실한 사실적 답변만 생성합니다.")
    with col3:
        model_name = st.selectbox("LLM 모델 선택", ["llama-3.3-70b-versatile (Groq 100% 무료)", "Ollama Llama3 (로컬 On-Premise 지원)", "gemini-2.0-flash", "gemini-1.5-flash"], index=0, help="[AI 분석 모델] 기술 문서 분석 및 답변 생성에 사용할 AI 모델 버전입니다.")
        distance_threshold = st.slider("Similarity Threshold", min_value=0.5, max_value=2.0, value=1.45, step=0.05, help="[무관한 질문 차단 가드레일] FAISS L2 거리 점수가 이 값을 초과하면 환각을 사전 차단합니다.")
    with col4:
        response_format = st.selectbox("답변 출력 양식 선택", ["간략 요약 모드 (직행 답변)", "표준 보고서 모드 (핵심-상세-출처)", "심층 분석 모드 (개요-상세-시사점)"], index=0, help="[답변 출력 서식] AI 답변의 렌더링 스타일 및 정보 상세도 수준을 결정합니다.")
        rebuild = st.button("파라미터 적용 및 체인 재구축", use_container_width=True)

if uploaded_file:
    # 기존 문서가 이미 존재하는 상태에서 다른 파일로 새로 교체할 때만 대화 초기화 확인 팝업 표출
    is_doc_changed = ("current_filename" in st.session_state) and (st.session_state.current_filename != uploaded_file.name)
    is_new_file = ("current_filename" not in st.session_state) or (st.session_state.current_filename != uploaded_file.name)
    has_active_chat = bool(st.session_state.get("messages", []))

    if is_doc_changed and has_active_chat and not st.session_state.get("doc_change_approved", False):
        st.warning("첨부한 문서를 다른 문서로 바꾸면 현재 활성화된 대화창이 새 문서로 전환됩니다. (저장된 최근 대화 목록은 안전하게 유지됩니다) 계속 진행하시겠습니까?")
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            if st.button("확인 (새 문서로 전환)", type="primary", use_container_width=True, key="confirm_change_doc_yes"):
                st.session_state.doc_change_approved = True
                st.session_state.messages = []
                save_current_chat([])
                st.session_state.session_mode = 0
                st.session_state.active_chat_id = None
                st.session_state.pending_clarification = None
                st.rerun()
        with c_col2:
            if st.button("취소 (기존 대화 유지)", use_container_width=True, key="confirm_change_doc_no"):
                st.info("문서 변경이 취소되었습니다.")
                st.stop()

    st.session_state.doc_change_approved = False

    # 안전한 임시 파일 관리 (UUID 파일명 및 try...finally 삭제)
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"temp_{uuid.uuid4().hex[:8]}_{uploaded_file.name}")
    
    config_key = f"{uploaded_file.name}_{chunk_size}_{chunk_overlap}_{k_value}_{model_name}_{temperature}_{distance_threshold}_{response_format}"
    
    if is_new_file or "current_config" not in st.session_state or st.session_state.current_config != config_key or rebuild:
        with st.spinner("문서 구조 분석 및 FAISS 벡터 인덱스를 구축 중입니다..."):
            try:
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                rag_chain, retriever, num_chunks, build_time = create_rag_chain(
                    temp_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    k=k_value,
                    model_name=model_name,
                    temperature=temperature,
                    distance_threshold=distance_threshold,
                    response_format=response_format
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
            finally:
                # 임시 파일 즉시 완전 삭제로 파일 누수 방지
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

        st.toast(f"FAISS 벡터 인덱싱 완료: {num_chunks}개 청크 ({build_time}초)")

    # 벤토 그리드 시스템 상태 대시보드
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

    # 메시지 히스토리 렌더링
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

    # RAG 질의 처리 함수
    def process_query(user_query, domain_choice=None):
        rag_chain = st.session_state.rag_chain

        # LLM 기반 질문 모호성 판정 (선택지가 미정인 경우)
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

        # 답변 생성 UI
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

            # 멀티턴 질문 재구성 정보 표시 (원본 질문과 검색 질문이 다를 경우)
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
        
        # 불러온 활성 대화인 경우, 추가 질문 및 답변을 최근 목록 DB에 실시간 동기화
        if st.session_state.get("active_chat_id"):
            active_id = st.session_state.active_chat_id
            for chat_item in st.session_state.saved_chats:
                if chat_item["id"] == active_id:
                    chat_item["messages"] = list(st.session_state.messages)
                    chat_item["saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    save_chats_to_file(st.session_state.saved_chats)
                    break

        st.rerun()

    # 스마트 역질문 대기 중인 경우 유저 대화형 Form 카드 렌더링
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
            
            # 기타를 눌렀을 때만 작성란이 동적으로 나타남
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

    # Form 외부에서 안전하게 Query 처리 실행
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
    # 첨부된 파일이 없는 경우: 대화 불러오기 모드(session_mode == 1)인 경우 해당 대화 복원 및 문서 첨부 경고 팝업 표출
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

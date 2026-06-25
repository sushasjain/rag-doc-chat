import streamlit as st
import os
import json
import warnings
warnings.filterwarnings("ignore")

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocChat",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

CHAT_FILE = "chat_history.json"

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background-color: #0d1117;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
}

/* Hide Streamlit chrome */
header[data-testid="stHeader"]    { display: none !important; }
footer                             { display: none !important; }
#MainMenu                          { display: none !important; }

/* Lock sidebar permanently open — hide every variant of the collapse/expand arrow */
[data-testid="stSidebarCollapseButton"]          { display: none !important; }
[data-testid="collapsedControl"]                  { display: none !important; }
button[data-testid="stBaseButton-headerNoPadding"]{ display: none !important; }
button[kind="header"]                             { display: none !important; }

/* ── Main content area ── */
.main .block-container {
    padding-top: 2rem !important;
    padding-bottom: 7rem !important;
    max-width: 780px !important;
    margin: 0 auto !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #21262d !important;
}

[data-testid="stSidebarContent"] {
    padding: 1.5rem 1.25rem 2rem 1.25rem !important;
}

/* Sidebar header */
.sidebar-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding-bottom: 1.25rem;
}

.sidebar-logo {
    font-size: 1.4rem;
    line-height: 1;
}

.sidebar-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: #e6edf3;
    letter-spacing: -0.02em;
}

.sidebar-divider {
    height: 1px;
    background: #21262d;
    margin: 1rem 0;
}

.sidebar-section-label {
    font-size: 0.62rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.09em !important;
    color: #6e7681 !important;
    margin: 0 0 0.65rem 0 !important;
    text-transform: uppercase !important;
}

/* PDF status badge */
.pdf-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(124, 58, 237, 0.08);
    border: 1px solid rgba(124, 58, 237, 0.25);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    margin-top: 0.6rem;
    font-size: 0.78rem;
    color: #c9d1d9;
}

.pdf-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.pdf-ready {
    color: #7c3aed;
    font-weight: 700;
    flex-shrink: 0;
}

/* Model status panel */
.model-panel {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    margin-top: 0.1rem;
}

.model-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: #8b949e;
}

.status-dot {
    width: 6px;
    height: 6px;
    background: #3fb950;
    border-radius: 50%;
    flex-shrink: 0;
}

/* ── Sidebar buttons ── */
.stButton > button {
    background: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 1rem !important;
    width: 100% !important;
    text-align: left !important;
    transition: background 0.12s ease, border-color 0.12s ease !important;
    cursor: pointer !important;
}

.stButton > button:hover {
    background: #30363d !important;
    border-color: #6e7681 !important;
    color: #e6edf3 !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border-radius: 8px;
}

[data-testid="stFileUploadDropzone"] {
    background: #21262d !important;
    border: 1px dashed #30363d !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: #7c3aed !important;
}

[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploadDropzone"] span {
    font-size: 0.78rem !important;
    color: #8b949e !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin: 0.4rem 0;
    border: 1px solid transparent;
}

/* User bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: rgba(37, 99, 235, 0.07);
    border-color: rgba(37, 99, 235, 0.18);
}

/* Assistant bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: rgba(22, 27, 34, 0.7);
    border-color: #21262d;
}

/* Avatar circles */
[data-testid="chatAvatarIcon-user"] svg {
    fill: #60a5fa !important;
}

[data-testid="chatAvatarIcon-assistant"] svg {
    fill: #a78bfa !important;
}

/* Message text */
[data-testid="stChatMessageContent"] p {
    color: #e6edf3 !important;
    font-size: 0.9rem !important;
    line-height: 1.65 !important;
    margin: 0 !important;
}

[data-testid="stChatMessageContent"] pre,
[data-testid="stChatMessageContent"] code {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    font-size: 0.82rem !important;
    color: #e6edf3 !important;
}

/* ── Chat input ── */
[data-testid="stChatInputContainer"] {
    background: #0d1117 !important;
    border-top: 1px solid #21262d !important;
    padding: 0.85rem 1.5rem 1rem 1.5rem !important;
}

[data-testid="stChatInput"] {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    color: #e6edf3 !important;
    font-size: 0.9rem !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12) !important;
}

/* ── Sources expander ── */
[data-testid="stExpander"] {
    background: rgba(13, 17, 23, 0.6) !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    margin-top: 0.5rem !important;
}

[data-testid="stExpander"] details summary {
    color: #8b949e !important;
    font-size: 0.78rem !important;
    padding: 0.4rem 0.25rem !important;
}

[data-testid="stExpander"] details summary:hover {
    color: #c9d1d9 !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] p {
    color: #8b949e !important;
    font-size: 0.8rem !important;
    line-height: 1.5 !important;
}

/* ── Spinner ── */
.stSpinner > div > div {
    border-top-color: #7c3aed !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    background: rgba(22, 27, 34, 0.8) !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
}

/* ── Welcome screen ── */
.welcome-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 5rem 2rem 3rem;
    max-width: 460px;
    margin: 0 auto;
}

.welcome-glyph {
    font-size: 2.75rem;
    margin-bottom: 1rem;
    line-height: 1;
}

.welcome-title {
    font-size: 1.45rem;
    font-weight: 600;
    color: #e6edf3;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.02em;
}

.welcome-sub {
    color: #8b949e;
    font-size: 0.875rem;
    line-height: 1.55;
    margin: 0 0 2rem 0;
}

.steps-row {
    display: flex;
    gap: 1.25rem;
    justify-content: center;
    flex-wrap: wrap;
}

.step-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
}

.step-num {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: rgba(124, 58, 237, 0.12);
    border: 1px solid rgba(124, 58, 237, 0.3);
    color: #a78bfa;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.8rem;
}

.step-label {
    color: #6e7681;
    font-size: 0.75rem;
    white-space: nowrap;
}

/* ── Thin scrollbar ── */
::-webkit-scrollbar       { width: 4px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #6e7681; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE INIT ───────────────────────────────────────────────────────
if "messages" not in st.session_state:
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = []

if "qa" not in st.session_state:
    st.session_state.qa = None

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def save_chat():
    with open(CHAT_FILE, "w") as f:
        json.dump(st.session_state.messages, f)

def process_pdf(file_path: str):
    """Unchanged RAG pipeline — loads, chunks, embeds, and wires up RetrievalQA."""
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(docs)

    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embedding,
        persist_directory="db",
    )

    retriever = vectordb.as_retriever()
    llm = Ollama(model="mistral")

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:

    # Branding
    st.markdown("""
    <div class="sidebar-header">
        <span class="sidebar-logo">📚</span>
        <span class="sidebar-title">DocChat</span>
    </div>
    """, unsafe_allow_html=True)

    # ── PDF Upload ──
    st.markdown('<p class="sidebar-section-label">Document</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type="pdf",
        label_visibility="collapsed",
    )

    if uploaded_file:
        # Only re-process if a different (or new) PDF is uploaded
        if st.session_state.pdf_name != uploaded_file.name:
            with st.spinner("Processing PDF…"):
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.read())
                st.session_state.qa = process_pdf("temp.pdf")
                st.session_state.pdf_name = uploaded_file.name

        st.markdown(f"""
        <div class="pdf-badge">
            <span>📄</span>
            <span class="pdf-name">{uploaded_file.name}</span>
            <span class="pdf-ready">✓</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ── Chat Controls ──
    st.markdown('<p class="sidebar-section-label">Chat</p>', unsafe_allow_html=True)

    if st.button("✦  New Chat", key="new_chat", use_container_width=True):
        st.session_state.messages = []
        save_chat()
        st.rerun()

    if st.button("🗑  Clear History", key="clear_chat", use_container_width=True):
        st.session_state.messages = []
        save_chat()
        st.rerun()

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ── Model Info ──
    st.markdown('<p class="sidebar-section-label">Model</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="model-panel">
        <div class="model-row"><span class="status-dot"></span><span>mistral (Ollama)</span></div>
        <div class="model-row"><span class="status-dot"></span><span>all-MiniLM-L6-v2</span></div>
        <div class="model-row"><span class="status-dot"></span><span>ChromaDB</span></div>
    </div>
    """, unsafe_allow_html=True)

# ─── MAIN CHAT AREA ──────────────────────────────────────────────────────────

# Welcome / empty state
if not st.session_state.messages:
    if st.session_state.qa is None:
        st.markdown("""
        <div class="welcome-wrap">
            <div class="welcome-glyph">📚</div>
            <h2 class="welcome-title">Chat with your document</h2>
            <p class="welcome-sub">Upload a PDF in the sidebar, then ask anything about it.</p>
            <div class="steps-row">
                <div class="step-card">
                    <div class="step-num">1</div>
                    <span class="step-label">Upload PDF</span>
                </div>
                <div class="step-card">
                    <div class="step-num">2</div>
                    <span class="step-label">Ask a question</span>
                </div>
                <div class="step-card">
                    <div class="step-num">3</div>
                    <span class="step-label">Get answers</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="welcome-wrap">
            <div class="welcome-glyph">💬</div>
            <h2 class="welcome-title">Ready</h2>
            <p class="welcome-sub">
                <strong style="color:#a78bfa;">{st.session_state.pdf_name}</strong>
                is loaded. Ask me anything about it.
            </p>
        </div>
        """, unsafe_allow_html=True)

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            sources = msg["sources"]
            with st.expander(f"📄 Sources — {len(sources)} page(s)"):
                for page in sources:
                    st.markdown(f"- Page {page}")

# ─── CHAT INPUT ──────────────────────────────────────────────────────────────
query = st.chat_input("Ask something about your PDF…")

if query:
    # Append + save user message
    st.session_state.messages.append({"role": "user", "content": query})
    save_chat()

    with st.chat_message("user"):
        st.markdown(query)

    # Guard: no PDF uploaded yet
    if st.session_state.qa is None:
        with st.chat_message("assistant"):
            st.warning("Please upload a PDF in the sidebar first.")
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Please upload a PDF first.",
            "sources": [],
        })
        save_chat()

    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                response = st.session_state.qa.invoke({"query": query})
                answer = response["result"]
                sources = sorted(set(
                    str(doc.metadata.get("page", "?"))
                    for doc in response["source_documents"]
                ))

            st.markdown(answer)

            if sources:
                with st.expander(f"📄 Sources — {len(sources)} page(s)"):
                    for page in sources:
                        st.markdown(f"- Page {page}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })
        save_chat()

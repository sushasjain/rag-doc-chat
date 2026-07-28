import streamlit as st
import streamlit.components.v1 as components
import os
import json
import hashlib
import html as html_lib
import markdown as mdlib
import warnings
warnings.filterwarnings("ignore")

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocChat",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

CHAT_FILE = "chat_history.json"

# ─── FORCE SIDEBAR OPEN via parent-frame JS ───────────────────────────────────
# components.html runs in an iframe on localhost — same origin as the app,
# so window.parent.document gives us access to the Streamlit page DOM.
components.html("""
<script>
(function() {
  var attempts = 0;
  function fix() {
    try {
      var doc = window.parent.document;

      // Force sidebar visible
      var sb = doc.querySelector('section[data-testid="stSidebar"]');
      if (sb) {
        sb.style.cssText += ';transform:translateX(0)!important;' +
          'min-width:260px!important;width:260px!important;' +
          'visibility:visible!important;display:flex!important;';
      }

      // Push main content to the right of the sidebar
      var main = doc.querySelector('[data-testid="stMain"]');
      if (main) main.style.marginLeft = '260px';

    } catch(e) {}
    attempts++;
    if (attempts < 15) setTimeout(fix, 300);
  }
  fix();
})();
</script>
""", height=0)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
*, *::before, *::after { box-sizing: border-box; }

/* ── Force dark theme variables ── */
:root {
  color-scheme: dark;
  --bg:        #1a1a1a;
  --surface:   #242424;
  --border:    #2c2c2c;
  --text:      #e2e2e2;
  --muted:     #666;
  --accent:    #d97757;
  --accent-bg: rgba(217,119,87,.08);
  --code-bg:   #141414;
}

html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section[data-testid="stMain"],
.main {
  background-color: #1a1a1a !important;
  color: #e2e2e2 !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── Hide Streamlit chrome ── */
header[data-testid="stHeader"] { display: none !important; }
footer                          { display: none !important; }
#MainMenu                       { display: none !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background-color: #171717 !important;
  border-right: 1px solid #252525 !important;
  min-width: 260px !important;
  width: 260px !important;
  transform: translateX(0) !important;
  visibility: visible !important;
}

[data-testid="stSidebarContent"] {
  padding: 1rem 0.875rem 1.5rem !important;
}

/* Sidebar collapse button — keep visible but match dark theme */
[data-testid="stSidebarCollapseButton"] button,
button[data-testid="stBaseButton-headerNoPadding"],
[data-testid="collapsedControl"] button {
  background: transparent !important;
  border: none !important;
  color: #444 !important;
}
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="collapsedControl"] button:hover {
  color: #888 !important;
  background: #242424 !important;
}

/* ── Main content ── */
.main .block-container {
  padding-top: 1.25rem !important;
  padding-bottom: 7rem !important;
  max-width: 740px !important;
  margin: 0 auto !important;
}

/* ── Sidebar HTML components ── */
.sb-brand {
  display: flex; align-items: center; gap: .6rem;
  padding: .5rem .25rem 1rem;
}
.sb-icon {
  width: 30px; height: 30px; background: #d97757;
  border-radius: 7px; display: flex; align-items: center;
  justify-content: center; font-size: .9rem; color: white;
  font-weight: 700; flex-shrink: 0;
}
.sb-name { font-size: 1rem; font-weight: 600; color: #ececec; letter-spacing: -.01em; }
.sb-div  { height: 1px; background: #252525; margin: .5rem 0; }
.sb-label {
  font-size: .65rem !important; font-weight: 600 !important;
  color: #444 !important; margin: .75rem 0 .4rem .1rem !important;
  letter-spacing: .08em !important; text-transform: uppercase !important;
}
.pdf-active {
  display: flex; align-items: center; gap: .45rem;
  background: rgba(217,119,87,.07); border: 1px solid rgba(217,119,87,.18);
  border-radius: 8px; padding: .45rem .7rem; margin-top: .5rem;
  font-size: .75rem; color: #aaa;
}
.pdf-fname { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.pdf-ok    { color:#d97757; font-weight:700; flex-shrink:0; }
.model-info { display:flex; flex-direction:column; gap:.35rem; }
.model-line { display:flex; align-items:center; gap:.45rem; font-size:.71rem; color:#444; }
.m-dot      { width:5px; height:5px; background:#4caf50; border-radius:50%; flex-shrink:0; }

/* ── Sidebar buttons ── */
.stButton > button {
  background: transparent !important; color: #aaa !important;
  border: 1px solid #2a2a2a !important; border-radius: 8px !important;
  font-size: .82rem !important; font-weight: 400 !important;
  padding: .5rem .875rem !important; width: 100% !important;
  text-align: left !important; cursor: pointer !important;
  transition: background .1s, border-color .1s, color .1s !important;
}
.stButton > button:hover {
  background: #242424 !important; border-color: #3a3a3a !important; color: #ececec !important;
}

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {
  background: #222 !important; border: 1px dashed #2c2c2c !important;
  border-radius: 8px !important;
}
[data-testid="stFileUploadDropzone"]:hover { border-color: #d97757 !important; }
[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploadDropzone"] span { font-size: .74rem !important; color: #4a4a4a !important; }

/* ── Custom message bubbles ── */
.cu-msg {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 6px 4px;
  margin: 2px 0;
}

/* USER — right aligned */
.cu-user {
  flex-direction: row-reverse;
  align-items: flex-end;
  margin: 8px 0;
}
.cu-bubble {
  background: #242424;
  border: 1px solid #2c2c2c;
  border-radius: 18px 18px 4px 18px;
  padding: 10px 16px;
  max-width: 72%;
  font-size: .9rem;
  color: #e2e2e2;
  line-height: 1.65;
  word-wrap: break-word;
}

/* ASSISTANT — left, no bubble */
.cu-assistant {
  padding: 14px 4px;
}
.cu-body { flex: 1; min-width: 0; padding-top: 2px; }
.cu-content {
  font-size: .9rem;
  color: #e2e2e2;
  line-height: 1.72;
}
.cu-content p         { margin: 0 0 .7em; }
.cu-content p:last-child { margin-bottom: 0; }
.cu-content ul, .cu-content ol { padding-left: 1.3rem; margin: .4em 0 .7em; }
.cu-content li        { margin-bottom: .25em; }
.cu-content h1, .cu-content h2, .cu-content h3 {
  color: #ececec; font-weight: 600; margin: .8em 0 .3em; line-height: 1.3;
}
.cu-content h1 { font-size: 1.1rem; }
.cu-content h2 { font-size: 1rem; }
.cu-content h3 { font-size: .93rem; }
.cu-content code {
  font-family: 'Courier New', monospace; font-size: .82em;
  background: #1e1e1e; padding: .1em .35em; border-radius: 3px; color: #d4d4d4;
}
.cu-content pre {
  background: #141414; border: 1px solid #2c2c2c; border-radius: 6px;
  padding: .875rem 1rem; overflow-x: auto; margin: .6em 0;
}
.cu-content pre code { background: none; padding: 0; font-size: .82rem; }
.cu-content table { border-collapse: collapse; width: 100%; margin: .6em 0; font-size: .85rem; }
.cu-content th, .cu-content td {
  border: 1px solid #2c2c2c; padding: .4rem .7rem; text-align: left;
}
.cu-content th { background: #242424; color: #ececec; font-weight: 600; }
.cu-content blockquote {
  border-left: 3px solid #d97757; margin: .6em 0; padding: .3em .8em;
  color: #888; font-style: italic;
}
.cu-content strong { color: #ececec; }

/* Sources details */
.cu-sources {
  margin-top: .6rem;
  font-size: .76rem;
  color: #555;
}
.cu-sources summary {
  cursor: pointer;
  list-style: none;
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  padding: .25rem 0;
  user-select: none;
}
.cu-sources summary:hover { color: #888; }
.cu-sources[open] summary { color: #888; }
.cu-pages { display:flex; flex-direction:column; gap:.5rem; margin-top:.5rem; }
.cu-src-item {
  display: flex; align-items: baseline; gap: .6rem;
  background: #1e1e1e; border: 1px solid #252525;
  border-radius: 6px; padding: .4rem .7rem;
}
.cu-page  {
  font-size: .69rem; font-weight: 600; color: #d97757;
  white-space: nowrap; flex-shrink: 0;
}
.cu-excerpt {
  font-size: .72rem; color: #444; line-height: 1.4;
  overflow: hidden; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}

/* Avatars */
.cu-av {
  width: 28px; height: 28px; border-radius: 50%;
  flex-shrink: 0; display: flex; align-items: center; justify-content: center;
}
.cu-av-u  { background: #2e2e2e; color: #777; }
.cu-av-ai {
  background: #d97757; border-radius: 6px;
  color: white; font-weight: 700; font-size: .88rem; letter-spacing: -.5px;
}

/* Warning inside assistant block */
.cu-warn {
  background: rgba(217,119,87,.07); border: 1px solid rgba(217,119,87,.2);
  border-radius: 8px; padding: .6rem .875rem; font-size: .84rem; color: #aaa;
  margin-top: .25rem;
}

/* ── Chat input ── */
[data-testid="stChatInputContainer"] {
  background: #1a1a1a !important;
  border-top: 1px solid #252525 !important;
  padding: .875rem 2rem 1.25rem !important;
}
[data-testid="stChatInput"] {
  background: #242424 !important; border: 1px solid #2c2c2c !important;
  border-radius: 14px !important; color: #ececec !important; font-size: .9rem !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: #d97757 !important;
  box-shadow: 0 0 0 2px rgba(217,119,87,.12) !important;
}

/* ── Spinner ── */
.stSpinner > div > div { border-top-color: #d97757 !important; }

/* ── Welcome ── */
.cu-welcome {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; padding: 5rem 2rem 3rem; max-width: 440px; margin: 0 auto;
}
.cu-welcome-icon {
  width: 52px; height: 52px; background: #d97757; border-radius: 13px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.4rem; color: white; font-weight: 700; margin: 0 auto 1.25rem;
}
.cu-welcome h2 {
  font-size: 1.4rem; font-weight: 600; color: #ececec;
  margin: 0 0 .5rem; letter-spacing: -.02em;
}
.cu-welcome p { color: #4a4a4a; font-size: .875rem; line-height: 1.6; margin: 0 0 2rem; }
.cu-steps { display:flex; gap:1.5rem; justify-content:center; flex-wrap:wrap; }
.cu-step  { display:flex; flex-direction:column; align-items:center; gap:.35rem; }
.cu-step-n {
  width:32px; height:32px; border-radius:50%; border:1px solid #2c2c2c;
  color:#555; display:flex; align-items:center; justify-content:center; font-size:.8rem;
}
.cu-step-l { color:#444; font-size:.72rem; }

/* ── Scrollbar ── */
::-webkit-scrollbar       { width: 4px; }
::-webkit-scrollbar-track { background: #1a1a1a; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #3a3a3a; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = []

if "qa"       not in st.session_state: st.session_state.qa       = None
if "pdf_name" not in st.session_state: st.session_state.pdf_name = None
if "pdf_hash" not in st.session_state: st.session_state.pdf_hash = None

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def save_chat():
    with open(CHAT_FILE, "w") as f:
        json.dump(st.session_state.messages, f)

@st.cache_resource(show_spinner=False)
def _load_embedding_model():
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    encode_kwargs={"normalize_embeddings": True},
)

@st.cache_resource(show_spinner=False)
def _load_llm():
    from langchain_community.llms import Ollama
    return Ollama(model="mistral")

_PROMPT_TEMPLATE = """You are DocChat, a precise document assistant. Answer the user's question using ONLY the context provided below.

Rules:
- Use only information present in the context. Do not add outside knowledge.
- If the answer is not in the context, respond exactly: "I couldn't find that information in this document."
- Format your answer clearly: use bullet points for lists, **bold** for key terms, and short paragraphs.
- Be direct. Do not repeat yourself. Do not pad your response.
- Do not invent names, numbers, dates, or facts.

Context:
{context}

Question: {question}

Answer:"""

def process_pdf(file_path: str):
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_community.vectorstores import Chroma
    from langchain.chains import RetrievalQA
    from langchain_community.retrievers import BM25Retriever
    from langchain.retrievers import EnsembleRetriever
    from langchain.prompts import PromptTemplate

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=_PROMPT_TEMPLATE,
    )

    # Load PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # Chunk PDF
    from chunker import split_documents_by_structure
    docs = split_documents_by_structure(docs)

    # Create Vector DB
    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=_load_embedding_model(),
    )

    # Vector Retriever
    vector_retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )

    # BM25 Retriever
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 5

    # Hybrid Retriever
    retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5],
    )

    # QA Chain
    qa = RetrievalQA.from_chain_type(
        llm=_load_llm(),
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )

    return qa

# ─── MESSAGE RENDERERS ───────────────────────────────────────────────────────
def render_user(content: str):
    safe = html_lib.escape(content)
    st.markdown(f"""
    <div class="cu-msg cu-user">
      <div class="cu-bubble">{safe}</div>
      <div class="cu-av cu-av-u">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_assistant(content: str, sources: list = None):
    body = mdlib.markdown(content, extensions=["fenced_code", "tables"])
    src  = ""
    if sources:
        items = ""
        for s in sources:
            if isinstance(s, dict):
                page    = html_lib.escape(str(s.get("page", "?")))
                excerpt = html_lib.escape(s.get("excerpt", ""))
                items  += (f'<div class="cu-src-item">'
                           f'<span class="cu-page">pg {page}</span>'
                           f'<span class="cu-excerpt">{excerpt}</span>'
                           f'</div>')
            else:
                items += (f'<div class="cu-src-item">'
                          f'<span class="cu-page">pg {html_lib.escape(str(s))}</span>'
                          f'</div>')
        src = (f'<details class="cu-sources">'
               f'<summary>📄 {len(sources)} source section(s)</summary>'
               f'<div class="cu-pages">{items}</div></details>')
    st.markdown(f"""
    <div class="cu-msg cu-assistant">
      <div class="cu-av cu-av-ai">✦</div>
      <div class="cu-body">
        <div class="cu-content">{body}</div>
        {src}
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_assistant_warn():
    st.markdown("""
    <div class="cu-msg cu-assistant">
      <div class="cu-av cu-av-ai">✦</div>
      <div class="cu-body">
        <div class="cu-warn">Please upload a PDF from the sidebar first.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-icon">✦</div>
      <span class="sb-name">DocChat</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("✏  New conversation", key="new_chat", use_container_width=True):
        st.session_state.messages = []
        save_chat()
        st.rerun()

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sb-label">Document</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if uploaded_file:
        file_bytes = uploaded_file.read()
        file_hash  = hashlib.md5(file_bytes).hexdigest()
        if st.session_state.pdf_hash != file_hash:
            with st.spinner("Processing…"):
                with open("temp.pdf", "wb") as f:
                    f.write(file_bytes)
                st.session_state.qa       = process_pdf("temp.pdf")
                st.session_state.pdf_name = uploaded_file.name
                st.session_state.pdf_hash = file_hash
        st.markdown(f"""
        <div class="pdf-active">
          <span>📄</span>
          <span class="pdf-fname">{uploaded_file.name}</span>
          <span class="pdf-ok">✓</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)

    if st.button("🗑  Clear history", key="clear_chat", use_container_width=True):
        st.session_state.messages = []
        save_chat()
        st.rerun()

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sb-label">Running locally</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="model-info">
      <div class="model-line"><span class="m-dot"></span><span>mistral · Ollama</span></div>
      <div class="model-line"><span class="m-dot"></span><span>all-MiniLM-L6-v2</span></div>
      <div class="model-line"><span class="m-dot"></span><span>ChromaDB</span></div>
    </div>
    """, unsafe_allow_html=True)

# ─── MAIN AREA ────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    if st.session_state.qa is None:
        st.markdown("""
        <div class="cu-welcome">
          <div class="cu-welcome-icon">✦</div>
          <h2>How can I help you?</h2>
          <p>Upload a PDF from the sidebar, then ask me anything about it.</p>
          <div class="cu-steps">
            <div class="cu-step"><div class="cu-step-n">1</div><span class="cu-step-l">Upload PDF</span></div>
            <div class="cu-step"><div class="cu-step-n">2</div><span class="cu-step-l">Ask a question</span></div>
            <div class="cu-step"><div class="cu-step-n">3</div><span class="cu-step-l">Get answers</span></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="cu-welcome">
          <div class="cu-welcome-icon">✦</div>
          <h2>Ready to chat</h2>
          <p><span style="color:#d97757">{st.session_state.pdf_name}</span> is loaded.<br>Ask me anything about it.</p>
        </div>
        """, unsafe_allow_html=True)

# Render chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        render_user(msg["content"])
    else:
        if msg["content"] == "Please upload a PDF first.":
            render_assistant_warn()
        else:
            render_assistant(msg["content"], msg.get("sources", []))

# ─── INPUT ───────────────────────────────────────────────────────────────────
# ─── INPUT ───────────────────────────────────────────────────────────────────
query = st.chat_input("Message DocChat…")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    save_chat()
    render_user(query)

    if st.session_state.qa is None:
        render_assistant_warn()
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Please upload a PDF first.",
            "sources": [],
        })
        save_chat()

    else:
        answer = ""
        sources = []

        try:
            with st.status("Searching document…", expanded=False) as status:
                qa = st.session_state.qa

                source_docs = qa.retriever.get_relevant_documents(query)

                status.update(label="Generating answer...")

                result = qa.combine_documents_chain.invoke({
                    "input_documents": source_docs,
                    "question": query,
                })

                answer = result.get("output_text", "").strip()

                # Build deduplicated source list
                seen = set()
                for doc in source_docs:
                    page = str(doc.metadata.get("page", "?"))
                    if page not in seen:
                        seen.add(page)
                        sources.append({
                            "page": page,
                            "excerpt": doc.page_content[:150].strip().replace("\n", " "),
                        })

                sources.sort(key=lambda x: x["page"])

                status.update(label="Done", state="complete")

        except Exception:
            answer = (
                "Something went wrong while generating the answer. "
                "Please make sure Ollama is running (`ollama serve`) and try again."
            )
            sources = []

        render_assistant(answer, sources)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })

        save_chat()

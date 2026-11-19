"""Streamlit frontend for the NVIDIA Agentic RAG reference implementation."""

from pathlib import Path
import os
import sys
import uuid

import streamlit as st
from dotenv import load_dotenv
from langgraph.errors import GraphRecursionError

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))
load_dotenv(PROJECT_ROOT / ".env")

from chatui.prompts import prompts_nemotron  # noqa: E402
from chatui.utils import compile, database  # noqa: E402
from chatui.utils.graph import TavilyAPIError  # noqa: E402

DEFAULT_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"


@st.cache_resource
def get_agent():
    return compile.compile_graph().compile()


def agent_inputs(question: str) -> dict:
    """Build the state expected by the original LangGraph workflow."""
    return {
        "question": question,
        "generator_model_id": DEFAULT_MODEL,
        "router_model_id": DEFAULT_MODEL,
        "retrieval_model_id": DEFAULT_MODEL,
        "hallucination_model_id": DEFAULT_MODEL,
        "answer_model_id": DEFAULT_MODEL,
        "prompt_generator": prompts_nemotron.generator_prompt,
        "prompt_router": prompts_nemotron.router_prompt,
        "prompt_retrieval": prompts_nemotron.retrieval_prompt,
        "prompt_hallucination": prompts_nemotron.hallucination_prompt,
        "prompt_answer": prompts_nemotron.answer_prompt,
        "router_use_nim": False,
        "retrieval_use_nim": False,
        "generator_use_nim": False,
        "hallucination_use_nim": False,
        "answer_use_nim": False,
        "collection_name": st.session_state.collection_name,
        "nim_generator_ip": "",
        "nim_router_ip": "",
        "nim_retrieval_ip": "",
        "nim_hallucination_ip": "",
        "nim_answer_ip": "",
        "nim_generator_port": "",
        "nim_router_port": "",
        "nim_retrieval_port": "",
        "nim_hallucination_port": "",
        "nim_answer_port": "",
        "nim_generator_id": "",
        "nim_router_id": "",
        "nim_retrieval_id": "",
        "nim_hallucination_id": "",
        "nim_answer_id": "",
    }


def save_uploaded_files(uploaded_files) -> list[str]:
    upload_dir = PROJECT_ROOT / "data" / "uploads" / st.session_state.collection_name
    upload_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for upload in uploaded_files:
        path = upload_dir / Path(upload.name).name
        path.write_bytes(upload.getbuffer())
        paths.append(str(path))
    return paths


st.set_page_config(page_title="Agentic RAG", page_icon="✦", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background: #f7f8fc; }
        [data-testid="stSidebar"] { background: #101827; }
        [data-testid="stSidebar"] * { color: #e8eefc; }
        [data-testid="stSidebar"] .stTextArea textarea {
            background: #172235; color: #ffffff; border-color: #34445f;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
            background: #172235; border-color: #526a92;
        }
        .hero { padding: 1.9rem 0 1.25rem; }
        .hero h1 { color: #111d33; font-size: 2.65rem; letter-spacing: -0.06em; margin: 0; }
        .hero p { color: #65718a; font-size: 1.04rem; margin: 0.45rem 0 0; }
        .status-card { background: #ffffff; border: 1px solid #e3e8f3; border-radius: 16px; padding: 0.9rem 1.1rem; }
        .status-label { color: #7a879f; font-size: 0.72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
        .status-value { color: #15213a; font-size: .94rem; font-weight: 600; margin-top: .25rem; }
        .dot { color: #1c9b6e; font-weight: 800; }
        .stButton > button { border-radius: 9px; font-weight: 600; }
        [data-testid="stSidebar"] .stButton > button {
            background: #2157d5 !important;
            border: 1px solid #2157d5 !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stButton > button * { color: #ffffff !important; }
        [data-testid="stSidebar"] .stButton > button:hover:not(:disabled) {
            background: #1746b8 !important;
            border-color: #1746b8 !important;
        }
        [data-testid="stSidebar"] .stButton > button:disabled {
            background: #1b2639 !important;
            border-color: #2b3b56 !important;
            color: #8290a8 !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] .stButton > button:disabled * { color: #8290a8 !important; }
        [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
            background: #233553 !important;
            border-color: #526a92 !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploader"] button * { color: #ffffff !important; }
        [data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
            background: #172235 !important; border: 1px solid #34445f !important;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploaderFile"] * { color: #e8eefc !important; }
        .source-ready { background: #172235; border: 1px solid #34445f; border-radius: 10px; color: #d8e4fb; font-size: .85rem; padding: .7rem .8rem; margin: .45rem 0 .8rem; }
        [data-testid="stChatMessage"] { background: #ffffff; border: 1px solid #e3e8f3; border-radius: 14px; padding: .55rem .85rem; color: #17233a !important; }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] *,
        [data-testid="stChatMessage"] [data-testid="stSpinner"],
        [data-testid="stChatMessage"] [data-testid="stSpinner"] * {
            color: #17233a !important;
            -webkit-text-fill-color: #17233a !important;
            opacity: 1 !important;
        }
        [data-testid="stChatInput"] { background: #ffffff !important; border: 1px solid #cfd8e8 !important; border-radius: 14px; box-shadow: none !important; }
        [data-testid="stChatInput"] > div { background: transparent !important; border: 0 !important; box-shadow: none !important; }
        [data-testid="stChatInput"] div[data-baseweb="textarea"] { background: #ffffff !important; border: 0 !important; box-shadow: none !important; }
        [data-testid="stChatInput"]:focus-within { border-color: #2157d5 !important; box-shadow: 0 0 0 3px rgba(33, 87, 213, .12) !important; }
        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] input {
            color: #14213a !important;
            -webkit-text-fill-color: #14213a !important;
            background: #ffffff !important;
        }
        [data-testid="stChatInput"] textarea::placeholder,
        [data-testid="stChatInput"] input::placeholder {
            color: #687792 !important;
            opacity: 1;
            -webkit-text-fill-color: #687792 !important;
        }
        [data-testid="stChatInput"] button { color: #2157d5 !important; }
        .sidebar-title { font-size: 1.25rem; font-weight: 750; margin-bottom: .2rem; }
        .sidebar-copy { color: #aebbd1; font-size: .87rem; margin-bottom: 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "collection_name" not in st.session_state:
    st.session_state.collection_name = f"rag-{uuid.uuid4().hex}"
if "context_ready" not in st.session_state:
    st.session_state.context_ready = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed_sources" not in st.session_state:
    st.session_state.indexed_sources = []
if "processed_uploads" not in st.session_state:
    st.session_state.processed_uploads = set()

has_nvidia_key = bool(os.getenv("NVIDIA_API_KEY"))
has_tavily_key = bool(os.getenv("TAVILY_API_KEY"))

st.markdown(
    """
    <div class="hero">
        <h1>Research with grounded answers.</h1>
        <p>Add your own sources, or let the agent search the web when no context is available.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

status_col, model_col, context_col = st.columns(3)
with status_col:
    st.markdown(
        f'<div class="status-card"><div class="status-label">Services</div><div class="status-value"><span class="dot">●</span> {"Ready" if has_nvidia_key and has_tavily_key else "Keys required"}</div></div>',
        unsafe_allow_html=True,
    )
with model_col:
    st.markdown(
        f'<div class="status-card"><div class="status-label">Model</div><div class="status-value">{DEFAULT_MODEL}</div></div>',
        unsafe_allow_html=True,
    )
with context_col:
    context_status = (
        '<span class="dot">●</span> Context ready'
        if st.session_state.context_ready
        else "Web search fallback"
    )
    st.markdown(
        f'<div class="status-card"><div class="status-label">Knowledge base</div><div class="status-value">{context_status}</div></div>',
        unsafe_allow_html=True,
    )

if not (has_nvidia_key and has_tavily_key):
    st.warning("Add NVIDIA_API_KEY and TAVILY_API_KEY to .env before using the app.")

with st.sidebar:
    st.markdown('<div class="sidebar-title">Knowledge base</div><div class="sidebar-copy">Use a URL or upload files to make answers specific to your sources.</div>', unsafe_allow_html=True)
    st.caption("WEB PAGES")
    urls = st.text_area("Web page URLs (one per line)")
    if st.button("Add URLs to context", use_container_width=True, disabled=not has_nvidia_key):
        with st.spinner("Downloading, splitting, and embedding pages..."):
            result = database.upload(urls.splitlines(), st.session_state.collection_name)
        if result:
            st.session_state.context_ready = True
            st.session_state.indexed_sources.extend(urls.splitlines())
            st.success("Context created.")
        else:
            st.error("No usable pages were added.")

    st.caption("DOCUMENTS")
    files = st.file_uploader(
        "Upload documents", type=["pdf", "txt", "md", "csv"], accept_multiple_files=True
    )
    if files:
        new_files = [
            upload
            for upload in files
            if (upload.name, upload.size) not in st.session_state.processed_uploads
        ]
        file_names = ", ".join(upload.name for upload in files)
        st.markdown(
            f'<div class="source-ready">Selected: {file_names}</div>',
            unsafe_allow_html=True,
        )
        if new_files and has_nvidia_key:
            with st.spinner("Indexing selected files..."):
                result = database.upload_files(
                    save_uploaded_files(new_files), st.session_state.collection_name
                )
            if result:
                st.session_state.context_ready = True
                st.session_state.indexed_sources.extend(upload.name for upload in new_files)
                st.session_state.processed_uploads.update(
                    (upload.name, upload.size) for upload in new_files
                )
                st.success("Files are ready to use in answers.")
                st.rerun()
            else:
                st.error("The selected files could not be indexed.")

    if st.button("Clear context", type="secondary", use_container_width=True):
        database._clear(collection_name=st.session_state.collection_name)
        st.session_state.context_ready = False
        st.session_state.indexed_sources = []
        st.session_state.processed_uploads = set()
        st.success("Context cleared.")

    if st.session_state.indexed_sources:
        st.caption("INDEXED SOURCES")
        for source in st.session_state.indexed_sources[-5:]:
            st.markdown(f"• {source}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input(
    "Ask a question about your documents or the web",
    disabled=not (has_nvidia_key and has_tavily_key),
)
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Routing, retrieving, and checking the answer..."):
                final_state = {}
                for update in get_agent().stream(agent_inputs(question), {"recursion_limit": 10}):
                    for state in update.values():
                        final_state.update(state)
                answer = final_state.get("generation", "The agent did not return an answer.")
            st.markdown(answer)
        except GraphRecursionError:
            answer = "The agent reached its retry limit. Try a more specific question."
            st.error(answer)
        except TavilyAPIError:
            answer = "Web search failed. Check that TAVILY_API_KEY is set correctly."
            st.error(answer)
        except Exception as error:
            answer = f"The request could not be completed: {error}"
            st.error(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

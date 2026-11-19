# Agentic RAG

> A source-grounded question-answering application for uploaded documents and indexed webpages, with web search used only when no local context exists.

**Author:** Anshika Garg  
**Email:** Anshika.120611@stu.upes.ac.in  
**Institution:** School of Computer Science, UPES, Dehradun

## Overview

Agentic RAG is a Retrieval-Augmented Generation application for dependable question answering over user-provided sources. It accepts PDFs, TXT files, Markdown files, CSV files, and webpage URLs; converts source content into searchable vector representations; retrieves relevant passages; and creates an answer grounded in those passages.

Rather than relying on a single prompt, the application uses an agentic workflow. It checks retrieved passages for relevance, checks whether the generated answer is grounded in the evidence, evaluates whether the response addresses the question, and follows a safe not-found path when selected sources do not contain the answer.

## Key Features

- Upload and index **PDF, TXT, Markdown, and CSV** files.
- Add and index **webpage URLs** as local knowledge-base sources.
- Create a session-specific **ChromaDB** vector collection.
- Retrieve semantically relevant chunks using NVIDIA embeddings.
- Generate responses with the NVIDIA Nemotron model.
- Grade retrieved chunks for relevance before generation.
- Check generated answers for grounding and usefulness.
- Use **Tavily web search only when no documents or URLs are indexed**.
- Return a safe not-found response instead of blending unrelated web information into an active document context.
- Provide a Streamlit interface for source management and chat.

## System Workflow

```text
Files / URLs
     |
Load, split, and embed source content
     |
ChromaDB session collection
     |
User question
     |
Is indexed context available?
   |                       |
 Yes                      No
   |                       |
Retrieve local chunks     Tavily web search
   |                       |
Relevance grading --------+
     |
Generate answer with NVIDIA Nemotron
     |
Grounding check and answer-quality check
     |
Final answer or safe not-found response
```

## Technology Stack

| Area | Technology |
|---|---|
| Frontend | Streamlit |
| Agent orchestration | LangGraph |
| LLM and embeddings | NVIDIA API / NVIDIA Nemotron |
| Vector database | ChromaDB via `langchain-chroma` |
| Document processing | LangChain community loaders and PyPDF |
| Web search | Tavily Search API |
| Environment management | Python virtual environment and `python-dotenv` |

## Prerequisites

- Python 3.10 or later (Python 3.12 is supported)
- An NVIDIA API key from [NVIDIA Build](https://build.nvidia.com/)
- A Tavily API key from [Tavily](https://tavily.com/) for web-search fallback
- Internet access for hosted model inference and web search

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Harshit-Verma03/Agentic-RAG.git
cd Agentic-RAG
```

### 2. Create and activate a virtual environment

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Create `.env` from the provided template:

```bash
cp .env.example .env
```

Open `.env` and add your keys:

```env
NVIDIA_API_KEY=your_nvidia_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Never commit `.env` or share these keys.

## Run the Application

With the virtual environment active, run:

```bash
streamlit run app.py
```

Streamlit will display a local address, usually:

```text
http://localhost:8501
```

Open this address in a browser. Keep the terminal open while the application is running. To stop the app, press `Ctrl + C` in the terminal.

## How to Use

### Ask questions about documents

1. Start the app with `streamlit run app.py`.
2. In the sidebar, select one or more supported files.
3. Click **Index selected files**.
4. Wait until the knowledge-base status displays **Context ready**.
5. Ask a question related to the indexed material.

### Add webpages as context

1. Paste one webpage URL per line in **Web page URLs**.
2. Click **Add URLs to context**.
3. Wait for indexing to finish.
4. Ask a question about the indexed webpages.

URLs entered in the interface are downloaded, chunked, embedded, and stored in the local ChromaDB context. They are not treated as a live Tavily search.

### Use live web search

Clear the active context, then ask a general question. When no indexed context exists, the router uses Tavily to search the web before generating an answer.

## Important Source Policy

| Context state | Behaviour |
|---|---|
| No indexed files or URLs | Uses Tavily web search. |
| Files or URLs indexed | Searches only the local ChromaDB collection. |
| Indexed context has no answer | Returns a safe not-found message instead of unrelated web content. |

This policy protects source provenance. To get a web answer after working with documents, click **Clear context** first.

## Project Structure

```text
Agentic-RAG/
├── app.py                         # Streamlit user interface
├── .env.example                   # Environment-variable template
├── requirements.txt               # Python dependencies
├── code/
│   └── chatui/
│       ├── prompts/
│       │   └── prompts_nemotron.py  # Agent prompts
│       └── utils/
│           ├── compile.py           # LangGraph workflow compilation
│           ├── graph.py             # Workflow nodes and transitions
│           └── database.py          # Loading, chunking, embeddings, ChromaDB
├── data/                          # Runtime uploads and vector-store data
└── output/                        # Generated project documents and reports
```

## Configuration

Optional settings in `.env`:

```env
NVIDIA_MODEL_ID=nvidia/nemotron-3.5-lightning-30b-a3b
RAG_DATA_DIR=./data
TAVILY_K=3
RECURSION_LIMIT=10
```

- `NVIDIA_MODEL_ID`: model used for generation and grading.
- `RAG_DATA_DIR`: directory for runtime source and vector data.
- `TAVILY_K`: maximum number of Tavily search results.
- `RECURSION_LIMIT`: maximum LangGraph workflow iterations for one request.

## Supported Input Types

| Type | Processing method |
|---|---|
| PDF | PyPDFLoader |
| TXT / Markdown | TextLoader |
| CSV | CSVLoader |
| Webpage URL | WebBaseLoader |

Text is split recursively into chunks before embedding. The default configuration uses 250-token chunks with zero overlap.

## Validation Performed

The project has been checked for these functional paths:

- Python syntax compilation for the main application, graph, database, and prompt modules.
- Streamlit application startup.
- NVIDIA hosted chat and embedding connectivity.
- ChromaDB indexing and semantic retrieval.
- Tavily web-search fallback with no context.
- Document-grounded answer generation and grading.
- Safe not-found behaviour for unsupported questions within an active context.
- Parsing of plain `yes`/`no` and JSON-like grading outputs.

## Known Limitations

- The interface does not yet show page-level citations or retrieved chunk excerpts.
- Scanned PDFs without extractable text require OCR, which is not currently included.
- An active context blocks Tavily fallback even if the context is unrelated; clear it to use web search.
- LLM graders are a helpful control layer, not formal guarantees of factual correctness.
- The project is an inference-time application and does not include a benchmark dataset, training pipeline, or numerical accuracy claims.
- Production deployment would require authentication, access control, encryption, retention controls, audit logs, and file-security checks.

## Troubleshooting

### `streamlit: command not found`

Activate the virtual environment and reinstall dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### API key warning or model request failure

Verify that `.env` is in the project root and contains a valid `NVIDIA_API_KEY`. Restart Streamlit after changing `.env`.

### Web search does not run

- Confirm `TAVILY_API_KEY` exists in `.env`.
- Click **Clear context** first. Tavily is intentionally used only when no source context is indexed.

### A document answer cannot find information

Confirm that the file or URL was indexed successfully, then ask a more specific question. The information may not be present in the selected sources.

### Telemetry warning in the terminal

Some third-party libraries may print telemetry warnings. If the application continues to retrieve chunks, generate answers, and complete grading checks, these warnings do not prevent normal use.

## License and Acknowledgements

This project is based on an NVIDIA Agentic RAG reference implementation and retains the repository’s [Apache 2.0 License](LICENSE.txt). It uses open-source libraries and hosted services subject to their respective licenses and terms.

---

Built and documented by **Anshika Garg**.

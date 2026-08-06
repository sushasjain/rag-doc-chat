# DocChat
### AI-Powered Intelligent Document Assistant using Retrieval-Augmented Generation (RAG)

DocChat is an intelligent document assistant that allows users to upload PDF documents and ask questions in natural language. Instead of relying on general knowledge, the application retrieves the most relevant sections from the uploaded document and generates accurate, context-aware answers using Retrieval-Augmented Generation (RAG).

Designed with a clean and responsive interface, DocChat combines semantic search, keyword retrieval, vector databases, and Large Language Models to provide fast, reliable, and document-grounded responses.

---

## Features

-  Upload and analyze PDF documents
-  Ask questions in natural language
-  Retrieval-Augmented Generation (RAG)
-  Hybrid Retrieval
  - Semantic Search
  - BM25 Keyword Search
-  AI-generated responses using LLMs
-  Answers grounded strictly in document context
-  Fast document indexing
-  Persistent ChromaDB vector storage
-  Modern responsive Streamlit interface

---

##  Architecture

```
                  User
                    │
                    ▼
             Upload PDF Document
                    │
                    ▼
          PDF Processing (PyMuPDF)
                    │
                    ▼
             Document Chunking
                    │
                    ▼
        Sentence Transformer Embeddings
                    │
                    ▼
              Chroma Vector Store
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
 Semantic Retriever        BM25 Retriever
        │                       │
        └───────────┬───────────┘
                    ▼
          Context Fusion & Ranking
                    │
                    ▼
              Prompt Construction
                    │
                    ▼
          Large Language Model (LLM)
                    │
                    ▼
            Context-Based Response
```

---

##  Tech Stack

### Frontend
- Streamlit

### Backend
- Python

### AI / Machine Learning
- LangChain
- Sentence Transformers
- ChromaDB
- BM25 Retriever
- OpenRouter
- Google Gemini

### Document Processing
- PyMuPDF

### Vector Database
- ChromaDB

---

##  Project Structure

```
LexiMind/
│
├── app.py                 # Streamlit application
├── ingest.py              # PDF ingestion pipeline
├── chunker.py             # Text chunking
├── query.py               # Retrieval & response generation
├── db/                    # Chroma database
├── .streamlit/
├── requirements.txt
└── README.md
```

---

##  Installation

Clone the repository

```bash
git clone https://github.com/yourusername/rag-doc-chat.git

cd rag-doc-chat
```

Create a virtual environment

```bash
python -m venv venv
```

Activate

Linux / macOS

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

##  Environment Variables

Create a `.env` file.

```
OPENROUTER_API_KEY=YOUR_API_KEY
```

or

```
GOOGLE_API_KEY=YOUR_API_KEY
```

---

## ▶ Running the Application

```bash
streamlit run app.py
```

---

##  Workflow

1. Upload a PDF document.
2. Extract text using PyMuPDF.
3. Split the document into semantic chunks.
4. Generate embeddings using Sentence Transformers.
5. Store embeddings in ChromaDB.
6. Retrieve relevant chunks using Hybrid Search (Semantic + BM25).
7. Construct a context-aware prompt.
8. Generate grounded responses using an LLM.

---

##  Future Enhancements

- Multi-document support
- Highlight answer sources
- Chat history persistence
- OCR support for scanned PDFs
- Authentication
- Docker deployment
- Cloud database support

---


##  License

This project is intended for educational and portfolio purposes.

---

##  Author

**Susha Jain**

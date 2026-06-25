DocChat – Local RAG PDF Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that allows users to upload PDF documents and ask natural language questions. The application retrieves relevant document chunks using vector search and generates answers using a local Mistral model running through Ollama.

---

Features

-Upload PDF documents
-Chat with your PDFs
-Semantic search using ChromaDB
-Local LLM using Ollama (Mistral)
-Sentence embeddings with all-MiniLM-L6-v2
-Source page references
-Modern Streamlit interface
-Persistent chat history

---

Tech Stack

- Python
- Streamlit
- LangChain
- Ollama
- Mistral
- ChromaDB
- Sentence Transformers
- PyPDFLoader

---

## Project Structure

```
.
├── app.py
├── ingest.py
├── query.py
├── requirements.txt
├── data/
└── .streamlit/
```

---

## Installation

Clone the repository

```bash
git clone https://github.com/sushasjain/rag-doc-chat.git
cd rag-doc-chat
```

Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run Ollama

```bash
ollama serve
```

Pull the model

```bash
ollama pull mistral
```

Start the application

```bash
streamlit run app.py
```

---

## Screenshots

*(Add screenshots here after deployment.)*

---

## Future Improvements

- Multiple PDF support
- Conversation memory
- Authentication
- Cloud deployment
- Better citation formatting

---

## License

MIT License

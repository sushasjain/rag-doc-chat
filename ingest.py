from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

loader = PyPDFLoader("data/sample.pdf")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

docs = text_splitter.split_documents(documents)

for i, doc in enumerate(docs):
    doc.metadata["chunk_id"] = i

embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectordb = Chroma.from_documents(
    documents=docs,
    embedding=embedding,
    persist_directory="db"
)

print("✅ Done")
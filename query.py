from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA

embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectordb = Chroma(
    persist_directory="db",
    embedding_function=embedding
)

retriever = vectordb.as_retriever()

llm = Ollama(model="mistral")

qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever
)

query = input("Ask: ")
print(qa.run(query))
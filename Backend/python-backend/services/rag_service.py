# backend/python-backend/services/rag_service.py

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document 
import pytesseract
from PIL import Image

from google.api_core import exceptions as google_exceptions

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(env_path)

# Keys 
gemini_api_key = os.getenv("RAG_GEMINI_API")
groq_api_key = os.getenv("RAG_GROQ_API")

if gemini_api_key:
    os.environ["GOOGLE_API_KEY"] = gemini_api_key
else:
    print("⚠️ WARNING: RAG_GEMINI_API not found in the .env file!")

primary_llm = None
fallback_llm = None
embeddings = None

try:
    # 1. Primary Model (Gemini)
    if gemini_api_key:
        primary_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash") 
    
    # 2. Fallback Model (Groq)
    if groq_api_key:
        fallback_llm = ChatGroq(model="llama3-8b-8192", api_key=groq_api_key)
        
    # 3. Embeddings (Using HuggingFace so document uploads never hit an API quota!)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
except Exception as e:
    print(f"⚠️ AI Initialization Error: {e}")


def load_document(file_path: str):
    """Dynamically loads different file types."""
    ext = file_path.split('.')[-1].lower()
    
    if ext == 'pdf':
        loader = PyPDFLoader(file_path)
        return loader.load()
    elif ext in ['docx', 'doc']:
        loader = Docx2txtLoader(file_path)
        return loader.load()
    elif ext in ['xlsx', 'xls', 'csv']:
        loader = UnstructuredExcelLoader(file_path) 
        return loader.load()
    elif ext in ['png', 'jpg', 'jpeg']:
        text = pytesseract.image_to_string(Image.open(file_path))
        return [Document(page_content=text, metadata={"source": file_path})]
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def create_rag_index(file_path: str):
    """Loads document, chunks it, and creates a lightweight FAISS index."""
    if not embeddings:
        raise RuntimeError("Embeddings model not initialized. Check your backend console.")
        
    docs = load_document(file_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    vector_store = FAISS.from_documents(splits, embeddings)
    return vector_store


def ask_question(vector_store, question: str):
    if not primary_llm and not fallback_llm:
        return "Error: No AI Models are initialized."
        
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    system_prompt = (
        "You are an assistant for document analysis. Use the following pieces of retrieved "
        "context to answer the question. If you don't know the answer, say that you don't know.\n\n"
        "{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    def run_chain(llm_to_use):
        question_answer_chain = create_stuff_documents_chain(llm_to_use, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        response = rag_chain.invoke({"input": question})
        return response["answer"]

    # --- Routing Logic with explicit Fallback ---
    if primary_llm:
        try:
            return run_chain(primary_llm)
        except (google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable) as e:
            print(f"⚠️ Gemini Quota/Service Error: {e}. Switching to Groq...")
            if fallback_llm:
                return run_chain(fallback_llm)
            return "Gemini is busy and no fallback is available."
            
        except Exception as e:
            error_msg = str(e).lower()
            if any(x in error_msg for x in ["429", "quota", "limit", "exhausted"]):
                print("⚠️ Rate limit detected via string match. Switching to Groq...")
                if fallback_llm:
                    return run_chain(fallback_llm)
            
            return f"An error occurred: {str(e)}"
            
    elif fallback_llm:
        return run_chain(fallback_llm)
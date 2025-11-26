import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


def load_pdf_chunks(pdf_path):
    """Load and chunk a single PDF file."""
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=40
    )

    chunks = splitter.split_documents(pages)
    return chunks


def load_all_pdfs_from_directory(data_dir):
    """Load and chunk all PDF files from a directory."""
    data_path = Path(data_dir)
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
        return []
    
    all_chunks = []
    pdf_files = list(data_path.glob("*.pdf"))
    
    for pdf_path in pdf_files:
        try:
            chunks = load_pdf_chunks(str(pdf_path))
            all_chunks.extend(chunks)
            print(f"Loaded {len(chunks)} chunks from {pdf_path.name}")
        except Exception as e:
            print(f"Error loading {pdf_path.name}: {e}")
    
    return all_chunks


def get_embedding_model():
    """Get or initialize the embedding model."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def build_vector_store(chunks, model):
    """Build a FAISS vector store from document chunks."""
    if not chunks:
        # Return empty index if no chunks
        if model is None:
            model = get_embedding_model()
        dim = model.get_sentence_embedding_dimension()
        index = faiss.IndexFlatL2(dim)
        return index, []
    
    texts = [c.page_content for c in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    return index, texts


def ingest(data_dir, embedding_model=None):
    """
    Ingest all PDFs from the data directory and build vector store.
    Returns (index, texts, chunk_count)
    """
    if embedding_model is None:
        embedding_model = get_embedding_model()
    
    chunks = load_all_pdfs_from_directory(data_dir)
    index, texts = build_vector_store(chunks, embedding_model)
    
    return index, texts, len(chunks)


def retrieve_context(query, model, index, texts, k=4):
    """Retrieve relevant context from vector store for a query."""
    if len(texts) == 0:
        return "No documents available. Please upload PDF files first."
    
    q_emb = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(q_emb, k)

    matched = [texts[i] for i in indices[0] if i < len(texts)]

    return "\n".join(matched)

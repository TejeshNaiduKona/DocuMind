import os
import glob
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration
RAW_DOCS_DIR = "raw_documents"
CHROMA_DB_DIR = "vectorstore"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def main():
    print(f"Loading documents from {RAW_DOCS_DIR}...")
    
    text_loader_kwargs = {'autodetect_encoding': True}
    loaders = [
        DirectoryLoader(RAW_DOCS_DIR, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs),
        DirectoryLoader(RAW_DOCS_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader),
        DirectoryLoader(RAW_DOCS_DIR, glob="**/*.docx", loader_cls=Docx2txtLoader)
    ]
    
    docs = []
    for loader in loaders:
        try:
            loaded_docs = loader.load()
            if loaded_docs:
                print(f"Loaded {len(loaded_docs)} documents using {loader.loader_cls.__name__}")
                docs.extend(loaded_docs)
        except Exception as e:
            print(f"Error loading with {loader.loader_cls.__name__}: {e}")

    if not docs:
        print("No documents found. Please add some .txt, .pdf, or .docx files to the raw_documents directory.")
        return

    print(f"Total documents loaded: {len(docs)}")

    print(f"Splitting documents with chunk size {CHUNK_SIZE} and overlap {CHUNK_OVERLAP}...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
    )
    splits = text_splitter.split_documents(docs)
    print(f"Generated {len(splits)} chunks.")

    print(f"Initializing embedding model '{EMBEDDING_MODEL}'...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print(f"Storing embeddings in ChromaDB at {CHROMA_DB_DIR}...")
    # Initialize Chroma, which will embed and store the chunks
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    print("Ingestion complete. Vector store persisted locally.")

if __name__ == "__main__":
    main()

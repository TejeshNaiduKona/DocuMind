# Model Card: DocuMind Enterprise RAG System

## Model Details
- **Architecture**: Retrieval-Augmented Generation (RAG)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Local HuggingFace model)
- **Reranker Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2` (Local HuggingFace model)
- **Generation Model**: `llama-3.1-8b-instant` (Provided remotely via Groq)
- **Vector Database**: ChromaDB (SQLite-backed local instance)

## Intended Use
This system is intended as an internal Enterprise assistant. Its primary function is to answer employee, legal, and operational inquiries by surfacing facts *strictly* from the documents provided. 

## Document Parsing Capabilities
- **Supported Formats**: `.pdf`, `.docx`, `.txt`
- **Chunking Profile**: 512 characters with a 64 character overlap, prioritizing paragraph retention to prevent loss of semantic context.

## Ethical Considerations & Limitations
- **Hallucination Mitigation**: The generation model is strictly prompted to answer "I don't know" if the provided context does not hold the answer. All responses are emitted alongside their explicit sources.
- **Data Privacy**: Documents ingested remain on-device/in-network within the ChromaDB instance. However, generated requests and contexts are passed to the Groq API. For strictly confidential environments, replacing Groq with a locally hosted Llama/Mistral node is required.
- **Top-K Limit**: The system pulls the 5 most statistically similar chunks and uses a CrossEncoder to rerank, passing the top 3 items to the LLM. Extremely dispersed information (e.g. "summarize all 50 documents") will result in partial or missing answers. 

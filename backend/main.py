import os
import subprocess
import json
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from sentence_transformers import CrossEncoder

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request

load_dotenv()

app = FastAPI(title="DocuMind Enterprise RAG API")

# Setup Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

CHROMA_DB_DIR = "vectorstore"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL = "llama-3.1-8b-instant"

embeddings = None
vectorstore = None
base_retriever = None
cross_encoder = None
llm = None

@app.on_event("startup")
def startup_event():
    global embeddings, vectorstore, base_retriever, cross_encoder, llm
    
    print("Loading vector store & embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    if os.path.exists(CHROMA_DB_DIR):
        vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
        base_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    print("Initializing CrossEncoder ReRanker...")
    cross_encoder = CrossEncoder(RERANKER_MODEL)

    print("Initializing LLM via Groq...")
    if not os.environ.get("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY not found in environment!")
    else:
        llm = ChatGroq(model_name=LLM_MODEL, temperature=0, streaming=True)

class QueryRequest(BaseModel):
    question: str

prompt_template = PromptTemplate.from_template("""You are a factual assistant for DocuMind. Answer ONLY using the context below.
If the answer isn't in the context, say "I don't know."
Context: {context}
Question: {question}""")

@app.post("/query")
@limiter.limit("5/minute")
async def query_documents(request: Request, req: QueryRequest):
    if not base_retriever or not llm:
        raise HTTPException(status_code=500, detail="Backend not fully initialized (Vectorstore or LLM missing).")
        
    initial_docs = base_retriever.invoke(req.question)
    
    if not initial_docs:
        # Stream "I don't know." with empty sources
        async def empty_response():
            yield json.dumps({"type": "sources", "data": []}) + "\n"
            yield json.dumps({"type": "token", "content": "I don't know."}) + "\n"
        return StreamingResponse(empty_response(), media_type="application/x-ndjson")
        
    pairs = [[req.question, doc.page_content] for doc in initial_docs]
    scores = cross_encoder.predict(pairs)
    for doc, score in zip(initial_docs, scores):
        doc.metadata['relevance_score'] = float(score)
        
    initial_docs.sort(key=lambda d: d.metadata['relevance_score'], reverse=True)
    top_docs = initial_docs[:3]
    
    context_text = "\n\n".join([doc.page_content for doc in top_docs])
    chain = prompt_template | llm
    
    async def generate_response():
        sources = [{"source": d.metadata.get("source", "Unknown"), "score": d.metadata.get("relevance_score"), "content": d.page_content} for d in top_docs]
        # Emit sources first
        yield json.dumps({"type": "sources", "data": sources}) + "\n"
        
        # Emit tokens
        async for chunk in chain.astream({"context": context_text, "question": req.question}):
            if chunk.content:
                yield json.dumps({"type": "token", "content": chunk.content}) + "\n"

    return StreamingResponse(generate_response(), media_type="application/x-ndjson")

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    os.makedirs("raw_documents", exist_ok=True)
    file_path = os.path.join("raw_documents", file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    # Run the ingestion script
    process = subprocess.run(["python", "scripts/ingest.py"], capture_output=True, text=True)
    
    # Reload vectorstore inline
    startup_event()
    
    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {process.stderr}")
        
    return {"message": f"Successfully ingested {file.filename}", "logs": process.stdout}

@app.get("/sources")
async def get_sources():
    docs = []
    if os.path.exists("raw_documents"):
        docs = os.listdir("raw_documents")
    return {"documents": docs}

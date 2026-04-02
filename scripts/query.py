import os
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from sentence_transformers import CrossEncoder

# Setup Configuration
CHROMA_DB_DIR = "vectorstore"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL = "llama-3.1-8b-instant"  # Use a currently active Groq model

def main():
    load_dotenv()
    
    # 1. Initialize embeddings and reload the vector store
    print("Loading vector store & embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    
    # 2. Setup the base retriever to get top k=5 chunks
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # 3. Setup ReRanker for relevance ordering
    print("Initializing CrossEncoder ReRanker...")
    cross_encoder = CrossEncoder(RERANKER_MODEL)

    # 4. Craft strict RAG prompt
    template = """You are a factual assistant. Answer ONLY using the context below.
If the answer isn't in the context, say "I don't know."
Context: {context}
Question: {question}"""
    prompt = PromptTemplate.from_template(template)

    # 5. Initialize the Groq LLM
    print("Initializing LLM via Groq...")
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found in environment!")
        return
        
    llm = ChatGroq(model_name=LLM_MODEL, temperature=0)

    # The query workflow
    query = "What is the company policy for remote work?"
    print(f"\nQUERY: {query}\n")

    print("Retrieving and re-ranking documents...")
    initial_docs = base_retriever.invoke(query)
    
    # Apply CrossEncoder manually
    pairs = [[query, doc.page_content] for doc in initial_docs]
    scores = cross_encoder.predict(pairs)
    
    # Attach scores and sort
    for doc, score in zip(initial_docs, scores):
        doc.metadata['relevance_score'] = score
    
    # Sort docs by score descending and take top 3
    initial_docs.sort(key=lambda d: d.metadata['relevance_score'], reverse=True)
    top_docs = initial_docs[:3]
    
    # Format the context text from the retrieved docs
    context_text = "\n\n".join([doc.page_content for doc in top_docs])
    
    print("Generating response...")
    # Format prompt and call LLM
    chain = prompt | llm
    response = chain.invoke({"context": context_text, "question": query})

    print("\n--- FINAL ANSWER ---")
    print(response.content)
    print("\n--- SOURCES ---")
    for idx, doc in enumerate(top_docs):
        print(f"\n[Source {idx+1}] Score: {doc.metadata.get('relevance_score'):.4f}")
        print(doc.page_content[:150] + "...")

if __name__ == "__main__":
    main()

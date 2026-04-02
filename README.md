# 🧠 DocuMind: Enterprise RAG Chatbot

DocuMind is a production-ready, highly accurate Enterprise Retrieval-Augmented Generation (RAG) system. It allows organizations to ingest `.pdf`, `.docx`, and `.txt` documents and interact with them securely using a ChatGPT-style interface, completely circumventing LLM hallucinations by enforcing strict source-grounding.

## 🌟 Key Features

- **Multi-Format Document Ingestion**: Seamlessly upload APIs and TXTs locally or through the UI drag-and-drop.
- **High-Accuracy RAG Pipeline**: Combines dense retrieval via ChromaDB (`all-MiniLM-L6-v2`) with precision reranking via a CrossEncoder (`ms-marco-MiniLM-L-6-v2`) to pull only the 3 most strictly relevant context chunks.
- **Citation-Backed UI**: The Streamlit interface displays the exact ReRanker context chunks drawn from the documents, allowing users to verify LLM claims instantly.
- **Conversation Memory**: Maintains multi-turn context awareness seamlessly using LangChain's conversational buffer memory.
- **Enterprise-Ready Middleware**: API endpoints are secured with `slowapi` rate limiting.
- **Instant Deployment**: Fully dockerized with multi-container `docker-compose` routing, alongside a unified `Dockerfile` for HuggingFace Space hosting. 

---

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI, Uvicorn
- **Frontend UI**: Streamlit
- **RAG Orchestrator**: LangChain
- **Embeddings & ReRanker**: HuggingFace `sentence-transformers`
- **Vector Database**: ChromaDB (Local SQLite Persistence)
- **Generation LLM**: LLaMA-3.1-8B (via Groq API)

---

## 🚀 Getting Started Locally

### 1. Requirements
Ensure you have Docker installed. Clone this repository and execute:

```bash
git clone https://your-repo-link/DocuMind.git
cd DocuMind
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory and add your Groq inference key:
```env
GROQ_API_KEY=gsk_YOUR_GROQ_API_KEY_HERE
```

### 3. Spin up the Containers
Boot the unified backend, vector store, and frontend seamlessly using Docker Compose:
```bash
docker-compose up --build -d
```
Access the application by navigating to **`http://localhost:8501`** in your browser.

---

## 🌐 Deploying to Hugging Face Spaces

This project contains a unified `Dockerfile` and `run.sh` script precisely tuned to bypass HF networking permissions and boot the application perfectly.

1. Create a New Space on Hugging Face using the **Docker** SDK (Blank Template).
2. Clone your Space, copy the contents of this repository into it, and `git push`.
3. Go to the **Settings > Variables and secrets** tab of the Space.
4. Create a new Secret named `GROQ_API_KEY` and provide your token.
5. Hugging Face will automatically execute the build and render the Streamlit app!

---

## 🔒 Security & Model Boundaries
Please review [MODEL_CARD.md](MODEL_CARD.md) for detailed descriptions on token chunking logic, LLM fallback behaviors limiting false generation, and privacy constraints.

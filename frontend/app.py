import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="DocuMind - Enterprise RAG", page_icon="🧠", layout="wide")

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.title("🧠 DocuMind")
st.markdown("Enterprise Document Intelligence Chatbot")

# --- Sidebar ---
with st.sidebar:
    st.header("🏢 Document Knowledge Base")
    st.markdown("Upload PDFs, DOCX, or TXT documents to add them to the system.")
    
    uploaded_file = st.file_uploader("Upload a new document", type=["txt", "pdf", "docx"])
    if uploaded_file and st.button("Ingest Document"):
        with st.spinner("Ingesting document (creating chunks & embeddings)..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            try:
                res = requests.post(f"{API_URL}/ingest", files=files)
                if res.status_code == 200:
                    st.success(f"{uploaded_file.name} ingested successfully!")
                else:
                    st.error(f"Failed to ingest: {res.text}")
            except Exception as e:
                st.error(f"Backend is not running: {e}")
                
    st.divider()
    st.subheader("Indexed Documents")
    try:
        res = requests.get(f"{API_URL}/sources")
        if res.status_code == 200:
            for doc in res.json().get("documents", []):
                st.markdown(f"- 📄 `{doc}`")
    except:
        st.warning("Could not connect to FastAPI server.")

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("Show Sources"):
                for idx, src in enumerate(msg["sources"]):
                    st.caption(f"**Source {idx+1} [Relevance: {src['score']:.2f}]**: {src['source']}")
                    st.markdown(f"> {src['content']}")

if user_input := st.chat_input("Ask a question about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        sources = []
        
        try:
            with requests.post(f"{API_URL}/query", json={"question": user_input}, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        data = json.loads(decoded_line)
                        if data["type"] == "sources":
                            sources = data["data"]
                        elif data["type"] == "token":
                            full_response += data["content"]
                            placeholder.markdown(full_response + "▌")
                            
            placeholder.markdown(full_response)
            if sources:
                with st.expander("Show Sources"):
                    for idx, src in enumerate(sources):
                        st.caption(f"**Source {idx+1} [Relevance: {src['score']:.2f}]**: {src['source']}")
                        st.markdown(f"> {src['content']}")
                        
        except Exception as e:
            st.error(f"Error querying backend: {e}")
            full_response = "Sorry, the backend encountered an error."

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response,
        "sources": sources
    })

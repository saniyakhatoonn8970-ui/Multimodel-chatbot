import os
import uuid
import base64
import requests
import streamlit as st
from typing import Optional, List, Dict, Any

# Configure page settings
st.set_page_config(
    page_title="MindBridge AI - Multimodal Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex + uuid.uuid4().hex  # 64-char high-entropy token

if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

if "conversations" not in st.session_state:
    st.session_state.conversations = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "documents" not in st.session_state:
    st.session_state.documents = []

if "backend_healthy" not in st.session_state:
    st.session_state.backend_healthy = False

if "system_providers" not in st.session_state:
    st.session_state.system_providers = {}

# ---------------------------------------------------------
# API Helper Functions
# ---------------------------------------------------------
def get_headers() -> Dict[str, str]:
    return {
        "X-Session-ID": st.session_state.session_id
    }

def check_backend_health() -> bool:
    try:
        res = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if res.status_code == 200:
            data = res.json()
            st.session_state.backend_healthy = True
            st.session_state.system_providers = data.get("providers", {})
            return True
        st.session_state.backend_healthy = False
        return False
    except Exception:
        st.session_state.backend_healthy = False
        return False

def fetch_conversations():
    try:
        res = requests.get(f"{BACKEND_URL}/api/conversations", headers=get_headers(), timeout=5)
        if res.status_code == 200:
            st.session_state.conversations = res.json().get("conversations", [])
    except Exception as e:
        st.sidebar.error(f"Failed to fetch conversations: {e}")

def create_new_conversation(title: Optional[str] = None):
    try:
        res = requests.post(
            f"{BACKEND_URL}/api/conversations",
            headers=get_headers(),
            json={"title": title or "New Conversation"},
            timeout=5
        )
        if res.status_code == 201:
            data = res.json()
            st.session_state.current_conversation_id = data["id"]
            st.session_state.messages = []
            fetch_conversations()
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error creating conversation: {e}")

def fetch_conversation_messages(conversation_id: str):
    try:
        res = requests.get(
            f"{BACKEND_URL}/api/conversations/{conversation_id}",
            headers=get_headers(),
            timeout=5
        )
        if res.status_code == 200:
            data = res.json()
            st.session_state.messages = data.get("messages", [])
    except Exception as e:
        st.error(f"Error loading messages: {e}")

def delete_current_conversation():
    if not st.session_state.current_conversation_id:
        return
    try:
        res = requests.delete(
            f"{BACKEND_URL}/api/conversations/{st.session_state.current_conversation_id}",
            headers=get_headers(),
            timeout=5
        )
        if res.status_code == 204:
            st.session_state.current_conversation_id = None
            st.session_state.messages = []
            fetch_conversations()
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error deleting conversation: {e}")

def fetch_documents():
    try:
        res = requests.get(f"{BACKEND_URL}/api/documents", headers=get_headers(), timeout=5)
        if res.status_code == 200:
            st.session_state.documents = res.json().get("documents", [])
    except Exception as e:
        st.sidebar.error(f"Failed to fetch documents: {e}")

def delete_document(doc_id: str):
    try:
        res = requests.delete(f"{BACKEND_URL}/api/documents/{doc_id}", headers=get_headers(), timeout=5)
        if res.status_code == 204:
            fetch_documents()
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error deleting document: {e}")

def submit_feedback(message_id: str, feedback_type: str):
    try:
        res = requests.post(
            f"{BACKEND_URL}/api/feedback",
            headers=get_headers(),
            json={"message_id": message_id, "feedback_type": feedback_type},
            timeout=5
        )
        if res.status_code == 201:
            st.toast("Thank you for your feedback!", icon="✅")
    except Exception as e:
        st.error(f"Failed to submit feedback: {e}")

# ---------------------------------------------------------
# Sidebar UI: Management & Controls
# ---------------------------------------------------------
with st.sidebar:
    st.title("🧠 MindBridge AI")
    st.caption("Secure Multimodal Assistant with RAG")

    # Backend Connection Status
    healthy = check_backend_health()
    if healthy:
        st.success("● Backend API Connected", icon="🟢")
    else:
        st.error(f"● Cannot reach Backend ({BACKEND_URL})", icon="🔴")
        st.info("Start the FastAPI server: `uvicorn backend.app.main:app --reload`")

    st.divider()

    # Anonymous Session Info
    with st.expander("🔐 Anonymous Session"):
        st.text(f"Session Token:\n{st.session_state.session_id[:12]}...{st.session_state.session_id[-8:]}")
        st.caption("Data is segregated by this high-entropy token without requiring user registration.")
        if st.button("Generate New Session", use_container_width=True):
            st.session_state.session_id = uuid.uuid4().hex + uuid.uuid4().hex
            st.session_state.current_conversation_id = None
            st.session_state.messages = []
            st.session_state.documents = []
            st.rerun()

    # Conversation Selector & New Chat Button
    st.subheader("💬 Conversations")
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        create_new_conversation()

    fetch_conversations()
    conv_options = {c["id"]: c["title"] for c in st.session_state.conversations}

    if conv_options:
        # Default to first conversation if none selected
        if st.session_state.current_conversation_id not in conv_options:
            st.session_state.current_conversation_id = list(conv_options.keys())[0]

        selected_id = st.selectbox(
            "Select Conversation",
            options=list(conv_options.keys()),
            format_func=lambda x: conv_options.get(x, "Conversation"),
            index=list(conv_options.keys()).index(st.session_state.current_conversation_id)
            if st.session_state.current_conversation_id in conv_options else 0
        )

        if selected_id != st.session_state.current_conversation_id:
            st.session_state.current_conversation_id = selected_id
            fetch_conversation_messages(selected_id)
            st.rerun()

        if st.button("🗑️ Delete Current Chat", use_container_width=True):
            delete_current_conversation()
    else:
        st.info("No conversations yet. Click 'New Conversation' to start.")

    st.divider()

    # Document Knowledge Base Management (RAG)
    st.subheader("📚 Knowledge Base (RAG)")
    uploaded_doc = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], key="rag_uploader")
    if uploaded_doc is not None:
        if st.button("📥 Index Document", use_container_width=True):
            with st.spinner(f"Ingesting and chunking {uploaded_doc.name}..."):
                try:
                    files = {"file": (uploaded_doc.name, uploaded_doc.getvalue(), uploaded_doc.type)}
                    res = requests.post(f"{BACKEND_URL}/api/documents", headers=get_headers(), files=files, timeout=30)
                    if res.status_code == 201:
                        st.success(f"Successfully indexed '{uploaded_doc.name}'!")
                        fetch_documents()
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {res.json().get('error', res.text)}")
                except Exception as e:
                    st.error(f"Error indexing document: {e}")

    fetch_documents()
    if st.session_state.documents:
        st.caption(f"**{len(st.session_state.documents)}** Indexed Document(s):")
        for doc in st.session_state.documents:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📄 **{doc['filename']}** ({doc.get('chunks_count', 0)} chunks)")
            with col2:
                if st.button("✕", key=f"del_{doc['id']}", help="Delete document"):
                    delete_document(doc["id"])
    else:
        st.caption("No documents indexed yet. Upload documents above to enable grounded RAG retrieval.")

    st.divider()

    # Chat Settings & Toggles
    st.subheader("⚙️ Assistant Settings")
    use_rag = st.toggle("Enable RAG Retrieval", value=True, help="Search indexed documents to ground answers.")
    rag_only = st.toggle("Document-Only Answers", value=False, help="Answer strictly from documents without general knowledge.")
    enable_audio = st.toggle("Enable Audio Response (TTS)", value=False, help="Generate spoken audio response.")

# ---------------------------------------------------------
# Main Chat Area
# ---------------------------------------------------------

# Top Header & AI Disclaimer Banner
st.subheader("MindBridge AI - Multimodal Conversational Assistant")
st.info(
    "⚠️ **AI & Privacy Notice**: MindBridge AI is an artificial intelligence assistant providing supportive conversation "
    "and document-grounded retrieval. It is **not** a licensed therapist, physician, or emergency service. In a crisis, "
    "call/text **988** (US/CA) or your local emergency number. Conversations are tied to your anonymous session token.",
    icon="ℹ️"
)

# Ensure a conversation exists
if not st.session_state.current_conversation_id:
    if st.session_state.conversations:
        st.session_state.current_conversation_id = st.session_state.conversations[0]["id"]
        fetch_conversation_messages(st.session_state.current_conversation_id)
    else:
        create_new_conversation("Welcome Chat")

# Load messages for active conversation
if st.session_state.current_conversation_id and not st.session_state.messages:
    fetch_conversation_messages(st.session_state.current_conversation_id)

# Render Chat History
for msg in st.session_state.messages:
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    metadata = msg.get("message_metadata") or {}

    with st.chat_message(role):
        st.markdown(content)

        # Show citations if present in metadata
        citations = metadata.get("citations")
        if citations:
            with st.expander(f"📑 Sources Cited ({len(citations)} references)"):
                for idx, c in enumerate(citations, 1):
                    page_info = f", Page {c.get('page_number')}" if c.get("page_number") else ""
                    st.markdown(f"**[{idx}] {c.get('filename')}{page_info}** (Relevance: `{c.get('score', 0):.2f}`)")
                    st.caption(f"> \"{c.get('snippet', '')}\"")

        # Feedback buttons for assistant responses
        if role == "assistant" and msg.get("id"):
            col_f1, col_f2, _ = st.columns([1, 1, 10])
            with col_f1:
                if st.button("👍", key=f"fb_pos_{msg['id']}", help="Helpful"):
                    submit_feedback(msg["id"], "helpful")
            with col_f2:
                if st.button("👎", key=f"fb_neg_{msg['id']}", help="Not helpful"):
                    submit_feedback(msg["id"], "unhelpful")

# ---------------------------------------------------------
# Multimodal Input Drawer (Image & Audio)
# ---------------------------------------------------------
with st.expander("📷 / 🎙️ Attach Image or Transcribe Audio", expanded=False):
    tab_img, tab_audio = st.tabs(["Image Understanding", "Speech-to-Text"])
    
    selected_image = None
    with tab_img:
        img_upload = st.file_uploader("Upload an Image (JPEG, PNG, WebP)", type=["jpg", "jpeg", "png", "webp"], key="img_uploader")
        if img_upload:
            selected_image = img_upload
            st.image(img_upload, caption="Preview of uploaded image", width=300)

    transcribed_text_slot = None
    with tab_audio:
        audio_upload = st.file_uploader("Upload Audio (WAV, MP3, WebM)", type=["wav", "mp3", "webm"], key="audio_uploader")
        if audio_upload:
            if st.button("🎙️ Transcribe Audio"):
                with st.spinner("Transcribing speech..."):
                    try:
                        files = {"file": (audio_upload.name, audio_upload.getvalue(), audio_upload.type)}
                        res = requests.post(f"{BACKEND_URL}/api/audio/transcribe", headers=get_headers(), files=files, timeout=30)
                        if res.status_code == 200:
                            transcription_data = res.json()
                            transcribed_text_slot = transcription_data.get("text", "")
                            st.success(f"**Transcription:** {transcribed_text_slot}")
                            st.session_state.transcribed_cache = transcribed_text_slot
                        else:
                            st.error(f"Transcription failed: {res.text}")
                    except Exception as e:
                        st.error(f"Error during audio transcription: {e}")

# ---------------------------------------------------------
# Chat Input & Message Processing
# ---------------------------------------------------------
default_input = st.session_state.pop("transcribed_cache", "")
user_input = st.chat_input("Type your message here...", key="chat_input_field")
if not user_input and default_input:
    user_input = default_input

if user_input:
    # 1. Display User Message Immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Process via Backend API
    with st.chat_message("assistant"):
        with st.spinner("MindBridge is thinking..."):
            try:
                if selected_image:
                    # Multimodal multipart request
                    files = {
                        "image_file": (selected_image.name, selected_image.getvalue(), selected_image.type)
                    }
                    data = {
                        "conversation_id": st.session_state.current_conversation_id,
                        "message": user_input,
                        "use_rag": str(use_rag).lower(),
                        "rag_only": str(rag_only).lower(),
                        "enable_audio_response": str(enable_audio).lower()
                    }
                    res = requests.post(
                        f"{BACKEND_URL}/api/chat/multimodal",
                        headers=get_headers(),
                        data=data,
                        files=files,
                        timeout=45
                    )
                else:
                    # Standard JSON chat request
                    payload = {
                        "conversation_id": st.session_state.current_conversation_id,
                        "message": user_input,
                        "use_rag": use_rag,
                        "rag_only": rag_only,
                        "enable_audio_response": enable_audio
                    }
                    res = requests.post(
                        f"{BACKEND_URL}/api/chat",
                        headers=get_headers(),
                        json=payload,
                        timeout=45
                    )

                if res.status_code == 200:
                    data = res.json()
                    asst_msg = data.get("assistant_message", {})
                    content = asst_msg.get("content", "")
                    citations = data.get("citations", [])
                    audio_b64 = data.get("audio_base64")
                    is_crisis = data.get("crisis_triggered", False)

                    if is_crisis:
                        st.error("🚨 **Supportive Safety Intervention Activated**")

                    st.markdown(content)

                    # Show citations if any
                    if citations:
                        with st.expander(f"📑 Sources Cited ({len(citations)} references)"):
                            for idx, c in enumerate(citations, 1):
                                page_info = f", Page {c.get('page_number')}" if c.get("page_number") else ""
                                st.markdown(f"**[{idx}] {c.get('filename')}{page_info}** (Relevance: `{c.get('score', 0):.2f}`)")
                                st.caption(f"> \"{c.get('snippet', '')}\"")

                    # Play audio response if available
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        st.audio(audio_bytes, format="audio/wav")

                    # Refresh messages from server to keep state perfectly synchronized
                    fetch_conversation_messages(st.session_state.current_conversation_id)
                    st.rerun()

                else:
                    err_msg = res.json().get("error", res.text)
                    st.error(f"Error: {err_msg}")

            except Exception as e:
                st.error(f"Failed to communicate with MindBridge backend: {e}")

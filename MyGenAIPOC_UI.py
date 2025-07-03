import streamlit as st
from MyGenAIPOC_RAG import build_qa_chain
from MyGenAIPOC import process_customer
import os 
import requests
from dotenv import load_dotenv

# Load .env file for local development.
# This should be at the top of your script.
load_dotenv()

st.title("Customer Insights GenAI Assistant")

if 'qa_chain' not in st.session_state:
    st.session_state.qa_chain = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'customer_id' not in st.session_state:
    st.session_state.customer_id = ''
if 'pdf_file' not in st.session_state:
    st.session_state.pdf_file = None
if 'json_file' not in st.session_state:
    st.session_state.json_file = None
if 'follow_up_counter' not in st.session_state:
    st.session_state.follow_up_counter = 0
if 'customer_lookup_counter' not in st.session_state:
    st.session_state.customer_lookup_counter = 0

st.sidebar.header("Customer Lookup")
customer_id = st.sidebar.text_input(
    "Enter Customer ID or Aadhar:",
    value=st.session_state.get('customer_id', ''),
    key=f"customer_id_{st.session_state.customer_lookup_counter}"
)
lookup = st.sidebar.button("Search")

if lookup and customer_id:
    pdf_file, json_file = process_customer(customer_id)
    st.session_state.customer_id = customer_id
    st.session_state.pdf_file = pdf_file
    st.session_state.json_file = json_file
    if json_file:
        # Each call to build_qa_chain now creates a new, isolated pipeline
        st.session_state.qa_chain = build_qa_chain(
            pdf_file=pdf_file,
            json_file=json_file,
            embedding_deployment="text-embedding-ada-002",
            embedding_model="text-embedding-ada-002",
            embedding_endpoint=os.environ.get('OPENAI_ENDPOINT'),
            llm_deployment="gpt-4o",
            llm_endpoint=os.environ.get('OPENAI_ENDPOINT')
        )
        st.session_state.chat_history = []
        st.success("Customer found. You can now ask questions.")
    else:
        st.session_state.qa_chain = None
        st.session_state.chat_history = []
        st.error("Customer not found. Please check the Customer ID or Aadhar and try again.")

if st.session_state.qa_chain:
    st.subheader(f"Customer ID: {st.session_state.customer_id}")
    if len(st.session_state.chat_history) == 0:
        # First, send a 'system' message to set the context
        system_prompt_url = "https://mygenaipoc.blob.core.windows.net/mygenaipoc/SystemPrompt.txt"
        response = requests.get(system_prompt_url)
        if response.status_code == 200:
            system_message = response.text.strip()
        else:
            system_message = (
                "You are a generative AI assistant at a bank. "
                "Give insights to the user based on the customer information. "
                "Never mention any bank's name in your answers. "
                "If you don't have enough information, say 'I don't know'."
            )
        st.session_state.chat_history.append(("system", system_message))

        # Then, send a 'user' message to request a snapshot
        # Fetch the first prompt from the provided URL
        first_prompt_url = "https://mygenaipoc.blob.core.windows.net/mygenaipoc/FirstPrompt.txt"
        response = requests.get(first_prompt_url)
        if response.status_code == 200:
            user_message = response.text.strip()
        else:
            user_message = (
                "First check the Customer Status. "
                "If Status is 'Exited', say 'Customer is no longer with us' and give no further response. "
                "If Status is 'Blacklisted', say 'Customer is Blacklisted' and give no further response. "
                "If neither, then:\n"
                "1. Give the Customer Name.\n"
                "2. If the Customer Type is 'Burgundy', say 'This is a Priority Banking Customer.'\n"
                "3. Give a snapshot of the customer in 5 bullet points."
            )
        st.session_state.chat_history.append(("user", user_message))

        # Get the response from the qa_chain
        result = st.session_state.qa_chain(user_message)
        st.session_state.chat_history.append(("assistant", result['result']))

    st.markdown("### Customer Insights")
    for idx, (sender, msg) in enumerate(st.session_state.chat_history):
        if idx == 0 and sender == "assistant":
            st.markdown(f"**Assistant:** {msg}")
        elif sender == "user" and idx != 1:  # Skip displaying the first user message
            st.markdown(f"**You:** {msg}")
        elif sender == "assistant":
            st.markdown(f"**Assistant:** {msg}")

    col1, col2, col3 = st.columns([9, 2, 3], vertical_alignment="center")
    with col1:
        follow_up_key = f"follow_up_{st.session_state.follow_up_counter}"
        follow_up = st.text_input("Ask a follow-up question:", key=follow_up_key)
    with col2:
        send = st.button("Send")
    with col3:
         no_more = st.button("No More Questions", key="no-more-questions")

    # MODIFIED: The logic for the "No more questions" button is now simplified.
    if no_more:
        # Clear the entire session state, which removes the old qa_chain object.
        st.session_state.clear()
        # Rerun the app to present a fresh interface to the user.
        st.rerun()

    elif send and follow_up.strip() and st.session_state.qa_chain:
        st.session_state.chat_history.append(("user", follow_up))
        result = st.session_state.qa_chain(follow_up)
        st.session_state.chat_history.append(("assistant", result['result']))
        st.session_state.follow_up_counter += 1
        st.rerun()
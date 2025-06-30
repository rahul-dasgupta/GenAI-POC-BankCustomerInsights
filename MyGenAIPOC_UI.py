import streamlit as st
import io
# MODIFIED: Removed 'clear_rag_objects' from the import
from MyGenAIPOC_RAG import build_qa_chain
from MyGenAIPOC import process_customer

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
            embedding_endpoint="https://dasgu-mchng52g-eastus2.openai.azure.com/",
            llm_deployment="gpt-4o",
            llm_endpoint="https://dasgu-mchng52g-eastus2.openai.azure.com/"
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
        initial_query = ("""I am a relationship manager in Axis Bank and this attached document has details about one of my customers. \
           First check if the Customer Status is Exited or Blacklisted. \
           If Exited then say Customer is no longer with us and give no further response. \
           If Blacklisted then say Customer is Blacklisted and give no further response.\
           If neither then don't mention anything, just give the Customer Name and if it is Burgundy, and move on to answer the questions below\
           1. Are there any upcoming dates in 2023 for his deposits, credit cards, investments, insurance, etc.?\
           2. What are the top 2 up-selling or cross-selling opportunities for this customer based on his current portfolio?""")
        result = st.session_state.qa_chain(initial_query)
        st.session_state.chat_history.append(("assistant", result['result']))

    st.markdown("### Key Customer Insights")
    for idx, (sender, msg) in enumerate(st.session_state.chat_history):
        if idx == 0 and sender == "assistant":
            st.markdown(f"**Assistant:** {msg}")
        elif sender == "user":
            st.markdown(f"**You:** {msg}")
        elif sender == "assistant":
            st.markdown(f"**Assistant:** {msg}")

    col1, col2, col3 = st.columns([6,2,3])
    with col1:
        follow_up_key = f"follow_up_{st.session_state.follow_up_counter}"
        follow_up = st.text_input("Ask a follow-up question:", key=follow_up_key)
    with col2:
        send = st.button("Send")
    with col3:
         no_more = st.button("No more questions", key="no-more-questions")

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
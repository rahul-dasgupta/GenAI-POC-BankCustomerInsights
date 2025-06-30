import os
# ADDED: Import the uuid module to generate unique names
import uuid
import os

os.environ["OPENAI_API_TYPE"] = os.environ.get('OPENAI_API_TYPE')
os.environ["OPENAI_API_KEY"] = os.environ.get('OPENAI_API_KEY')
os.environ["OPENAI_API_VERSION"] = os.environ.get('OPENAI_API_VERSION')

import camelot
import pandas as pd
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import AzureChatOpenAI
import io
import tempfile


def build_qa_chain(pdf_file, json_file, embedding_deployment, embedding_model, embedding_endpoint, llm_deployment, llm_endpoint):
    table_docs = []
    text_docs = []
    if pdf_file is not None:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_pdf:
            tmp_pdf.write(pdf_file.read())
            tmp_pdf.flush()
            tables = camelot.read_pdf(tmp_pdf.name, pages="all", flavor="lattice")
        for t in tables:
            df = t.df
            table_docs.append(Document(page_content=df.to_csv(index=False), metadata={"source": "table"}))

        pdf_file.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_pdf2:
            tmp_pdf2.write(pdf_file.read())
            tmp_pdf2.flush()
            text_loader = PyPDFLoader(tmp_pdf2.name)
            text_docs = text_loader.load()

    json_file.seek(0)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=True, mode="w+") as tmp_json:
        tmp_json.write(json_file.read())
        tmp_json.flush()
        json_loader = JSONLoader(
            file_path=tmp_json.name,
            jq_schema=". | {text: tostring, metadata: {id: .CustomerID}}",
            text_content=False
        )
        json_docs = json_loader.load()

    all_docs = json_docs + table_docs + text_docs

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200
    )
    split_docs = splitter.split_documents(all_docs)

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=embedding_deployment,
        model=embedding_model,
        azure_endpoint=embedding_endpoint
    )
    
    # ADDED: Create a unique name for the collection for this specific session
    collection_name = str(uuid.uuid4())

    # MODIFIED: Pass the unique collection_name to Chroma to ensure isolation
    vectorstore = Chroma.from_documents(
        documents=split_docs, 
        embedding=embeddings, 
        persist_directory=None,
        collection_name=collection_name
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    llm = AzureChatOpenAI(
        temperature=0,
        azure_deployment=llm_deployment,
        azure_endpoint=llm_endpoint
    )
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
    )
    return qa_chain
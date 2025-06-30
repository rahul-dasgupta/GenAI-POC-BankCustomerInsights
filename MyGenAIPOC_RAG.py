import os

os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_KEY"] = "Cn2IWRpS5EpqWfPW5X3Y5HKXXotOjzTxWhSN9CqtCsBjazajvb2YJQQJ99BFACHYHv6XJ3w3AAAAACOGifdX"
#os.environ["OPENAI_API_BASE"] = "https://dasgu-mchng52g-eastus2.openai.azure.com/"
os.environ["OPENAI_API_VERSION"] = "2024-12-01-preview"  

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
    # Only process PDF if provided
    if pdf_file is not None:
        # 1. Extract tables → one Document per row
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_pdf:
            tmp_pdf.write(pdf_file.read())
            tmp_pdf.flush()
            tables = camelot.read_pdf(tmp_pdf.name, pages="all", flavor="lattice")
        for t in tables:
            df = t.df
            table_docs.append(Document(page_content=df.to_csv(index=False), metadata={"source": "table"}))
        #print(f"Loaded {len(table_docs)} Table Docs")

        # 2. Extract full-page text (ignores images)
        pdf_file.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_pdf2:
            tmp_pdf2.write(pdf_file.read())
            tmp_pdf2.flush()
            text_loader = PyPDFLoader(tmp_pdf2.name)
            text_docs = text_loader.load()
        #print(f"Loaded {len(text_docs)} text page documents")


    # 3. Load JSON from in-memory file using a temp file for JSONLoader
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
    #print(f"Loaded {len(json_docs)} JSON documents")

    # 4. Combine all documents
    all_docs = json_docs + table_docs + text_docs

    # 5. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200
    )
    split_docs = splitter.split_documents(all_docs)
    #print(f"Split into {len(split_docs)} chunks.")

    # 6. Embed & index
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=embedding_deployment,
        model=embedding_model,
        azure_endpoint=embedding_endpoint
    )
    # Always use in-memory Chroma (no persist_directory)
    vectorstore = Chroma.from_documents(split_docs, embeddings, persist_directory=None)

    # 7. Build RetrievalQA chain
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
        return_source_documents=True
    )
    return qa_chain




import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import HuggingFaceHub
import os
import pickle
from langchain.llms import CTransformers
from htmltemplate import css, bot_template, user_template
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    # embeddings = OpenAIEmbeddings()
    # embeddings = embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2",
                                   model_kwargs={'device': "cpu"})

    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    
    return vectorstore

def get_conversation_chain(vectorstore):
    # llm = ChatOpenAI()
    llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":2048})
    # llm = HuggingFaceHub(repo_id="tiiuae/falcon-7b", model_kwargs={"temperature":0.5, "max_length":512})
    # llm = CTransformers(model='TheBloke/Falcon-7B-Instruct-GGML', model_file='falcon-7b-instruct.ggccv1.q4_1.bin',config={'max_new_tokens':2000,'temperature':0.01})
    # llm = CTransformers(model="marella/gpt-2-ggml",model_type="gpt2",
                    # config={'max_new_tokens':128,'temperature':0.01})



    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    # st.write(response)
    st.session_state.chat_history = response['chat_history']
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
    
 
def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with your data :envelope:")
    st.write(css, unsafe_allow_html=True)
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    st.header("Chat with your data :envelope:")
    user_question=st.text_input("Ask anything to your PDF:")
    if user_question:
        handle_userinput(user_question)
    # st.write(user_template.replace("{{MSG}}", "hello bot"), unsafe_allow_html=True)
    # st.write(user_template.replace("{{MSG}}", "hello human"), unsafe_allow_html=True)
    with st.sidebar:
        st.subheader("Documents")
        pdf_docs=st.file_uploader(
            "Upload your PDF file and press _START_",accept_multiple_files=True)
        if st.button("START"):
            with st.spinner("Processing Data..."):
                # get text
                raw_text=get_pdf_text(pdf_docs)
                # get text chunks
                text_chunks=get_text_chunks(raw_text)
                # st.write(text_chunks)
                # create vector store
                vectorstore=get_vectorstore(text_chunks)
                 # create conversation chain
                st.session_state.conversation = get_conversation_chain(vectorstore)




if __name__ == '__main__':
    main()
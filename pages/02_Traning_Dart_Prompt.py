from dotenv import load_dotenv

from langchain_core.messages.chat import ChatMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_teddynote import logging

from libs.loaders.dart_document_loader import DartDocumentLoader, get_recent_report_no

import streamlit as st

load_dotenv()
if "langsmith_on" not in st.session_state:
    logging.langsmith("[Test] Dart Prompt")
    st.session_state["langsmith_on"] = True

st.title("🎯 Test Dart Prompt")

# 처음 1번만 실행하기 위한 코드
if "messages" not in st.session_state:
    # 대화기록을 저장하기 위한 용도로 생성한다.
    st.session_state["messages"] = []


def print_history():
    for msg in st.session_state["messages"]:
        st.chat_message(msg.role).write(msg.content)


def add_history(role, content):
    st.session_state["messages"].append(ChatMessage(role=role, content=content))


def create_prompt():
    chat_template = ChatPromptTemplate.from_messages(
        [
            # role, message
            ("system", system_prompt),
            ("human", "반가워요!"),
            ("ai", "안녕하세요! 무엇을 도와드릴까요?"),
            ("human", "{question}"),
        ]
    )
    return chat_template


# 체인을 생성합니다.
def create_chain(retriever, model):
    pass


@st.cache_data(show_spinner="loading...")
def load_dart_report():
    report_no = get_recent_report_no(stock_code)
    docs = DartDocumentLoader(report_no).load()
    return docs


def generate_retriever():
    docs = load_dart_report()
    return docs


with st.sidebar:
    stock_code = st.text_input("Stock Code")

    if stock_code:
        test = load_dart_report()

if test:
    st.write(test)

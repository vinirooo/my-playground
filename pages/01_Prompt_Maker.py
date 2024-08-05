import streamlit as st
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_teddynote import logging
from langchain_teddynote.prompts import load_prompt

load_dotenv()
logging.langsmith("[Project] Prompt Maker")


def make_prompt(task, question):
    # Your code for generating the prompt goes here
    prompt = load_prompt("prompts/prompt-maker.yaml", encoding="utf-8")
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    chain = prompt | llm | StrOutputParser()

    with st.chat_message("ai"):
        response = chain.stream({"task": task, "question": question})
        st.write_stream(response)


st.title("Prompt Maker")

task = st.text_input("Enter a TASK")
question = st.text_area("Enter a prompt")
button = st.button("Generate Prompt")

if button:
    if not task:
        st.warning("Please enter a TASK before generating the prompt.")
    elif not question:
        st.warning("Please enter a prompt before generating the prompt.")
    else:
        make_prompt(task, question)

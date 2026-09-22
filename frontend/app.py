import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Campus Helper", page_icon="🎓")
st.title("🎓 Campus Helper")
st.caption("검색된 문서를 근거로 답변하는 RAG 챗봇 예제")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("참고 문서"):
                for source in message["sources"]:
                    st.markdown(f"- [{source['title']}]({source['url']})")
                    st.caption(source["excerpt"])

if question := st.chat_input("학사 정보를 질문해보세요"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={"question": question},
                timeout=45,
            )
            response.raise_for_status()
            result = response.json()
            st.markdown(result["answer"])
            if result["sources"]:
                with st.expander("참고 문서"):
                    for source in result["sources"]:
                        st.markdown(f"- [{source['title']}]({source['url']})")
                        st.caption(source["excerpt"])
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                }
            )
        except requests.RequestException:
            message = "API에 연결하지 못했습니다. FastAPI 서버 상태를 확인해주세요."
            st.error(message)
            st.session_state.messages.append({"role": "assistant", "content": message})

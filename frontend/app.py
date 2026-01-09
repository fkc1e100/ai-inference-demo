import streamlit as st
import requests
import json
import time

# Configuration
# In Kubernetes, we can talk to the other service by name
# If running locally, you might need localhost:8000
API_URL = "http://ai-inference:8000/api/generate"

st.set_page_config(page_title="AI Assistant", page_icon="🤖")

st.title("🤖 Enterprise AI Assistant")
st.caption("Powered by Gemma 3 (4B) on Google Kubernetes Engine")

tab1, tab2 = st.tabs(["Chat", "Performance"])

with tab1:
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is your question?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Call the Model
            try:
                with st.spinner("Thinking..."):
                    payload = {
                        "model": "gemma3:4b",
                        "prompt": prompt,
                        "stream": False 
                    }
                    # Note: For production real-time feel, we would enable streaming
                    response = requests.post(API_URL, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        answer = data.get("response", "No response.")
                        
                        # Simulate typing effect
                        for chunk in answer.split():
                            full_response += chunk + " "
                            time.sleep(0.05)
                            message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                        
            except Exception as e:
                st.error(f"Connection Error: {e}")

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

with tab2:
    st.header("System Performance Real-time")
    st.markdown("Verified load test results for Gemma 3 (4B) on 10x NVIDIA L4 GPUs.")
    
    try:
        import streamlit.components.v1 as components
        with open("/app/results.html", "r") as f:
            html_content = f.read()
            components.html(html_content, height=1000, scrolling=True)
    except FileNotFoundError:
        st.warning("Performance data not found. Please run the load test.")
    except Exception as e:
        st.error(f"Error loading graphs: {e}")

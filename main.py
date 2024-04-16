import streamlit as st
import requests
import yaml
from dotenv import load_dotenv
import random
from msal_streamlit_authentication import msal_authentication
import json
import time
import boto3
from io import StringIO
from PyPDF2 import PdfReader

st.set_page_config(
    layout='wide')


hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

with st.sidebar:
    awsk = st.text_input("AWS API Key", key="AWS Key", type="password")
    aws_key = st.text_input("AWS Secret", key="AWS Secret", type="password")



uploaded_file = st.file_uploader("Choose a file")

# load env
load_dotenv()

skillsearch = False
projectsearch = False


session = boto3.Session(
    aws_access_key_id=awsk,
    aws_secret_access_key=aws_key
)


bedrock = session.client(service_name='bedrock-runtime')

# Read config yaml file
with open('./streamlit_app/config.yaml', 'r') as file:
    config = yaml.safe_load(file)
title = config['streamlit']['title']
subtitle = config['streamlit']['subtitle']
avatar = {
    'user': None,
    'assistant': config['streamlit']['avatar']
}

# Set logo
st.image(config['streamlit']['logo'], width=300)

# Set page title
st.title(title)
st.markdown(f":blue[{subtitle}]")

# Initialize Streamlit session state
if "messages" not in st.session_state:
    st.session_state['messages'] = [{"role": "assistant", "content": "Hello! How can I help?"}]
if 'genid' not in st.session_state:
    st.session_state['genid'] = random.randint(0,10000)
if 'messagenum' not in st.session_state: 
    st.session_state['messagenum'] = 0
if "response" not in st.session_state:
    st.session_state.response = ""

for msg in st.session_state.messages:
    if "assistant" in msg['role']:
        st.chat_message(msg["role"]).write(msg['content'])
    elif "user" in msg['role']:
        st.chat_message(msg["role"]).write(msg['content'])

def stream_data(output):
    for word in output.split():
        yield word + " "
        time.sleep(0.05)

current_line_number = 1

if aws_key:
    if uploaded_file is None:
        if prompt := st.chat_input("Enter your question"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            # prompt_data = "\nInstructions: " + instructions + "\n\nHuman: " + prompt + "\n\nAssistant: "
            modelId = "anthropic.claude-3-sonnet-20240229-v1:0" 
            # prompt_data = "\n\nHuman: " + prompt + "\n\nAssistant: "
            # body = json.dumps({"prompt": prompt_data, "max_tokens_to_sample": 300, "temperature": 0.1, "top_p": 0.9})
            body = json.dumps({
                    "max_tokens": 256,
                    "messages": [{"role": "user", "content": prompt}],
                    "anthropic_version": "bedrock-2023-05-31"
                    })
            accept = '*/*'
            contentType = 'application/json'
            response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
            response_body = json.loads(response.get('body').read())
            output = response_body.get('content')[0]['text']
            # print(requests.post(URL,data=BODY, params=PARAMS))
            st.session_state.messages.append({"role": "assistant", "content": output})
            # st.chat_message("assistant").write_stream(stream_data(response['content']))
            st.chat_message("assistant").write(output)
    else:
        if prompt := st.chat_input("Enter your question"):
            reader = PdfReader(uploaded_file)
            pagetext = []
            for page in reader.pages:
                pagetext.append(page.extract_text())
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            # prompt_data = "\nInstructions: " + instructions + "\n\nHuman: " + prompt + "\n\nAssistant: "
            modelId = "anthropic.claude-3-sonnet-20240229-v1:0" 
            # prompt_data = "\n\nHuman: " + prompt + "\n\nAssistant: "
            # body = json.dumps({"prompt": prompt_data, "max_tokens_to_sample": 300, "temperature": 0.1, "top_p": 0.9}
            fullprompt = ' '.join(pagetext) + f"\n\n Using the above text, answer this question: {prompt}"

            body = json.dumps({
                    "max_tokens": 256,
                    "messages": [{"role": "user", "content": fullprompt}],
                    "anthropic_version": "bedrock-2023-05-31"
                    })
            accept = '*/*'
            contentType = 'application/json'
            response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
            response_body = json.loads(response.get('body').read())
            output = response_body.get('content')[0]['text']
            # print(requests.post(URL,data=BODY, params=PARAMS))
            st.session_state.messages.append({"role": "assistant", "content": output})
            # st.chat_message("assistant").write_stream(stream_data(response['content']))
            st.chat_message("assistant").write(output)
        # st.write(len(reader.pages))
        # if prompt := st.chat_input("Enter your question"):
        #     st.session_state.messages.append({"role": "user", "content": prompt})
        #     st.chat_message("user").write(prompt)
        #     # prompt_data = "\nInstructions: " + instructions + "\n\nHuman: " + prompt + "\n\nAssistant: "
        #     modelId = "anthropic.claude-3-sonnet-20240229-v1:0" 
        #     # prompt_data = "\n\nHuman: " + prompt + "\n\nAssistant: "
        #     # body = json.dumps({"prompt": prompt_data, "max_tokens_to_sample": 300, "temperature": 0.1, "top_p": 0.9})
        #     body = json.dumps({
        #             "max_tokens": 256,
        #             "messages": [{"role": "user", "content": prompt}],
        #             "anthropic_version": "bedrock-2023-05-31"
        #             })
        #     accept = '*/*'
        #     contentType = 'application/json'
        #     response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
        #     response_body = json.loads(response.get('body').read())
        #     output = response_body.get('content')[0]['text']
        #     # print(requests.post(URL,data=BODY, params=PARAMS))
        #     st.session_state.messages.append({"role": "assistant", "content": output})
        #     # st.chat_message("assistant").write_stream(stream_data(response['content']))
        #     st.chat_message("assistant").write(output)

    
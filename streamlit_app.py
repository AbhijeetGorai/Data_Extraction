import streamlit as st
import requests
import json

st.title("Document Processor")

# Auth inputs
email = st.text_input("Email ID")
access_token = st.text_input("Access Token", type="password")

# File uploader
uploaded_files = st.file_uploader("Upload documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# Hardcoded prompt
prompt = "Please extract structured information from the document."

if st.button("Generate"):
    if not email or not access_token:
        st.error("Please enter Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        try:
            # Prepare file payload
            files = [("file", (f.name, f.read(), f.type)) for f in uploaded_files]

            # Form data
            data = {
                "access_token": access_token,
                "email": email,
                "prompt": prompt
            }

            # Replace with your actual API endpoint
            api_url = "https://your-api-endpoint.com/process"

            with st.spinner("Calling API..."):
                response = requests.post(api_url, data=data, files=files)

            # ✅ Show raw text to debug
            st.subheader("Raw Response Text:")
            st.code(response.text)

            # ✅ Now try to parse JSON
            try:
                result = response.json()
            except Exception as e:
                st.error("Failed to parse API response as JSON.")
                st.code(response.text)
                st.exception(e)
                st.stop()

            # ✅ Extract and clean the answer
            answer = result.get("message", {}).get("answer", None)

            if answer:
                try:
                    # Remove markdown wrapping
                    cleaned = answer.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(cleaned)
                    pretty_json = json.dumps(parsed, indent=4)

                    st.success("Extracted Information:")
                    st.code(pretty_json, language="json")
                except Exception as e:
                    st.error("Failed to clean or parse the answer.")
                    st.code(answer)
                    st.exception(e)
            else:
                st.warning("No 'answer' found in response.")
                st.json(result)

        except Exception as e:
            st.error("Something went wrong during the API call.")
            st.exception(e)

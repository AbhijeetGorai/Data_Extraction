import streamlit as st
import requests
import json

st.title("Simple Document Processor")

# Auth inputs
email = st.text_input("Email ID")
access_token = st.text_input("Access Token", type="password")

# File uploader
uploaded_files = st.file_uploader("Upload documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# Hardcoded prompt
prompt = "Please extract structured information from the document."

# Submit button
if st.button("Generate"):
    if not email or not access_token:
        st.error("Please enter Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        try:
            # Prepare file payload
            files = [("file", (f.name, f.read(), f.type)) for f in uploaded_files]

            # Prepare form data
            data = {
                "access_token": access_token,
                "email": email,
                "prompt": prompt
            }

            # Replace with your actual API endpoint
            api_url = "https://your-api-endpoint.com/process"

            with st.spinner("Calling API..."):
                response = requests.post(api_url, data=data, files=files)

            # Debug raw response
            st.subheader("Raw API Response:")
            st.code(response.text)

            # Try to parse the response
            try:
                result = response.json()
                answer = result.get("message", {}).get("answer", None)

                if answer:
                    try:
                        # Clean up markdown-style JSON block
                        cleaned = answer.replace("```json", "").replace("```", "").strip()

                        # Parse JSON string into a dict
                        parsed = json.loads(cleaned)

                        # Pretty-print JSON
                        pretty_json = json.dumps(parsed, indent=4)

                        st.success("Extracted Structured Information:")
                        st.code(pretty_json, language="json")

                    except Exception as e:
                        st.error("Failed to parse the answer into valid JSON.")
                        st.text("Raw answer:")
                        st.code(answer)
                        st.exception(e)

                else:
                    st.warning("No 'answer' found in the response.")
                    st.json(result)

            except json.JSONDecodeError:
                st.error("API did not return valid JSON.")
                st.text("Raw response:")
                st.code(response.text)

        except Exception as e:
            st.error("Something went wrong while calling the API.")
            st.exception(e)

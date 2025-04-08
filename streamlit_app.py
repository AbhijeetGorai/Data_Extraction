import streamlit as st
import requests

st.title("Document Processor")

# Auth and input fields
email = st.text_input("Email ID")
access_token = st.text_input("Access Token", type="password")
prompt = st.text_area("Enter your prompt")

# File uploader
uploaded_files = st.file_uploader("Upload your documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# Generate button
if st.button("Generate"):
    if not email or not access_token or not prompt:
        st.error("Please fill in Email, Access Token, and Prompt.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        try:
            # Prepare files for multipart upload
            files = []
            for f in uploaded_files:
                files.append(("file", (f.name, f.read(), f.type)))

            # Add form fields (text values)
            data = {
                "access_token": access_token,
                "email": email,
                "prompt": prompt
            }

            # API endpoint
            api_url = "https://dataextraction-gear.streamlit.app/"  # 🔁 Replace this

            with st.spinner("Processing..."):
                response = requests.post(api_url, data=data, files=files)

            if response.status_code == 200:
                st.success("Documents processed successfully!")
                st.markdown("### Result:")
                try:
                    st.json(response.json())
                except Exception:
                    st.write(response.text)
            else:
                st.error(f"Error {response.status_code}")
                st.write(response.text)
        except Exception as e:
            st.error("Something went wrong with the API call.")
            st.exception(e)

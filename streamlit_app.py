import streamlit as st
import requests

st.title("Document Processor")

# Authentication inputs
email = st.text_input("Email ID")
access_token = st.text_input("Access Token", type="password")

# File uploader - accepts multiple files
uploaded_files = st.file_uploader(
    "Upload your documents", accept_multiple_files=True, type=["pdf", "docx", "txt"]
)

# Generate button
if st.button("Generate"):
    if not email or not access_token:
        st.error("Please enter both Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        # Prepare the files for the API request
        files = [("files", (f.name, f, f.type)) for f in uploaded_files]

        # API endpoint
        api_url = "https://your-api-endpoint.com/process"  # Replace with your actual URL

        # Headers for authentication
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Email-ID": email
        }

        try:
            with st.spinner("Processing..."):
                response = requests.post(api_url, files=files, headers=headers)

            if response.status_code == 200:
                st.success("Documents processed successfully!")
                st.markdown("### Result:")
                st.json(response.json())
            else:
                st.error(f"Error: {response.status_code}")
                st.write(response.text)
        except Exception as e:
            st.error("Failed to connect to API")
            st.exception(e)

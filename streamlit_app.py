import streamlit as st
import requests

# Set the background color of the Streamlit app to white
st.markdown(
    """
    <style>
        .css-1d391kg {
            background-color: white;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# File upload option (Black and White)
st.markdown(
    """
    <style>
        .css-1d391kg input[type="file"] {
            background-color: white;
            border: 1px solid black;
            color: black;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Title for the app
st.title("File Upload and API Trigger")

# Input field for the API endpoint URL
api_url = st.text_input("Enter the API URL", value="https://your.api/endpoint")

# Input fields for authentication parameters
access_token = st.text_input("Enter your Access Token", type="password")
email = st.text_input("Enter your Email ID")

# File uploader widget
uploaded_file = st.file_uploader("Upload your document", type=["pdf", "txt", "docx"])

# Generate button (Red color)
if st.button("Generate", key="generate", use_container_width=True):
    if uploaded_file is not None:
        # Prepare the file for sending in the API call
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        
        # Set up headers with the provided authentication parameters
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        if email:
            headers["Email"] = email
        
        # Trigger the API call using the given URL
        try:
            response = requests.post(api_url, files=files, headers=headers)
            if response.ok:
                result = response.text  # Alternatively, use response.json() if API returns JSON
                st.markdown(f'<h3 style="color: green;">{result}</h3>', unsafe_allow_html=True)
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload a file before clicking 'Generate'.")

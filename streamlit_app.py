import streamlit as st
 
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
 
# File uploader widget

uploaded_file = st.file_uploader("Upload your document", type=["pdf", "txt", "docx"])
 
# Generate button (Red color)

if st.button("Generate", key="generate", use_container_width=True):

    if uploaded_file is not None:

        # Placeholder to show API result

        result = "This is a placeholder result after triggering the API."

        # Display result in green color

        st.markdown(f'<h3 style="color: green;">{result}</h3>', unsafe_allow_html=True)

    else:

        st.warning("Please upload a file before clicking 'Generate'.")
 
 

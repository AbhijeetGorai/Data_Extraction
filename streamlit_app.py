import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO

st.title("Multi-Document Processor with Excel Export")

# Auth inputs
email = st.text_input("Email ID")
access_token = st.text_input("Access Token", type="password")

# File uploader
uploaded_files = st.file_uploader("Upload documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# Hardcoded prompt
prompt = "Please extract structured information from the document."

# Prepare results storage
results = []

if st.button("Generate"):
    if not email or not access_token:
        st.error("Please enter Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        # Replace with your actual API endpoint
        api_url = "https://your-api-endpoint.com/process"

        with st.spinner("Processing documents..."):
            for file in uploaded_files:
                try:
                    # Prepare single file
                    files = [("file", (file.name, file.read(), file.type))]

                    # Form data
                    data = {
                        "access_token": access_token,
                        "email": email,
                        "prompt": prompt
                    }

                    # Call API
                    response = requests.post(api_url, data=data, files=files)

                    try:
                        result = response.json()
                        answer_raw = result.get("message", {}).get("answer", "")
                        file_name = result.get("message", {}).get("fileName", file.name)

                        # Clean and parse answer
                        cleaned = answer_raw.replace("```json", "").replace("```", "").strip()
                        parsed_json = json.loads(cleaned)
                        pretty_json = json.dumps(parsed_json, indent=4)

                        # Show result
                        st.success(f"Processed: {file_name}")
                        st.code(pretty_json, language="json")

                        # Store for Excel
                        results.append({
                            "File Name": file_name,
                            "Extracted JSON": pretty_json
                        })

                    except Exception as e:
                        st.error(f"Error parsing result for {file.name}")
                        st.code(response.text)
                        st.exception(e)

                except Exception as e:
                    st.error(f"API error with file: {file.name}")
                    st.exception(e)

        # Generate Excel if we have results
        if results:
            df = pd.DataFrame(results)

            # Convert DataFrame to Excel in-memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Extracted Data')

            # Create download button
            st.markdown("### Download Results")
            st.download_button(
                label="📥 Download Excel",
                data=output.getvalue(),
                file_name="extracted_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

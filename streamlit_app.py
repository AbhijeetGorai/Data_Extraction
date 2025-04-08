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

if st.button("Generate"):
    if not email or not access_token:
        st.error("Please enter Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        results = []  # Reset results for each run

        # API endpoint
        api_url = "https://your-api-endpoint.com/process"

        with st.spinner("Processing documents..."):
            for file in uploaded_files:
                try:
                    # Reset file read position before reading
                    file.seek(0)
                    files = [("file", (file.name, file.read(), file.type))]

                    data = {
                        "access_token": access_token,
                        "email": email,
                        "prompt": prompt
                    }

                    response = requests.post(api_url, data=data, files=files)

                    try:
                        result = response.json()
                        answer_raw = result.get("message", {}).get("answer", "")
                        file_name = result.get("message", {}).get("fileName", file.name)

                        # Clean and parse answer
                        cleaned = answer_raw.replace("```json", "").replace("```", "").strip()
                        parsed_json = json.loads(cleaned)
                        pretty_json = json.dumps(parsed_json, indent=4)

                        # Show result for each file
                        st.success(f"Processed: {file_name}")
                        st.code(pretty_json, language="json")

                        # Save for Excel
                        results.append({
                            "File Name": file_name,
                            "Extracted JSON": pretty_json
                        })

                    except Exception as e:
                        st.error(f"Error parsing JSON from API for: {file.name}")
                        st.code(response.text)
                        st.exception(e)

                except Exception as e:
                    st.error(f"API call failed for: {file.name}")
                    st.exception(e)

        # If results collected, prepare download
        if results:
            df = pd.DataFrame(results)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Extracted Data')
            output.seek(0)

            st.markdown("### 📥 Download All Extracted Data")
            st.download_button(
                label="Download Excel File",
                data=output,
                file_name="extracted_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO

st.title("📄 Batch Document Processor (Excel Export Only)")

# Auth inputs
email = st.text_input("Email ID")
access_token = st.text_input("Access Token", type="password")

# File uploader
uploaded_files = st.file_uploader("Upload multiple documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# Hardcoded prompt
prompt = "Please extract structured information from the document."

if st.button("Generate"):
    if not email or not access_token:
        st.error("Please enter Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        api_url = "https://your-api-endpoint.com/process"  # Replace with your actual endpoint
        extracted_data = []

        with st.spinner("Processing all documents..."):
            for uploaded_file in uploaded_files:
                try:
                    uploaded_file.seek(0)
                    files = [("file", (uploaded_file.name, uploaded_file.read(), uploaded_file.type))]
                    data = {
                        "access_token": access_token,
                        "email": email,
                        "prompt": prompt
                    }

                    response = requests.post(api_url, data=data, files=files)
                    result = response.json()

                    file_name = result.get("message", {}).get("fileName", uploaded_file.name)
                    answer_raw = result.get("message", {}).get("answer", "")

                    # Clean markdown wrapping
                    cleaned = answer_raw.replace("```json", "").replace("```", "").strip()

                    # Try to parse JSON
                    try:
                        parsed = json.loads(cleaned)
                        formatted = json.dumps(parsed, indent=4)
                        extracted_json = formatted
                    except json.JSONDecodeError:
                        extracted_json = cleaned  # fallback to raw cleaned string

                    # Append to final results
                    extracted_data.append({
                        "File Name": file_name,
                        "Extracted JSON": extracted_json
                    })

                except Exception as e:
                    extracted_data.append({
                        "File Name": uploaded_file.name,
                        "Extracted JSON": f"ERROR: {str(e)}"
                    })

        # Display and download after all processing
        if extracted_data:
            df = pd.DataFrame(extracted_data)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Extracted Results')
            output.seek(0)

            st.success("✅ All files processed.")
            st.markdown("### 📥 Download Extracted Results")
            st.download_button(
                label="Download Excel File",
                data=output,
                file_name="extracted_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No data to export.")

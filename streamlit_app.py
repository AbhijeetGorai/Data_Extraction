import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO

st.title("📄 Document Processor with Excel Export")

# User credentials
email = st.text_input("Email ID")
access_token = st.text_input("Access Token", type="password")

# File upload
uploaded_files = st.file_uploader("Upload multiple documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# Hardcoded prompt
prompt = "Please extract structured information from the document."

if st.button("Generate"):
    if not email or not access_token:
        st.error("Please fill in both Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        api_url = "https://your-api-endpoint.com/process"  # Replace with actual API
        extracted_data = []

        with st.spinner("Processing documents..."):
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

                    # Clean markdown
                    cleaned = answer_raw.replace("```json", "").replace("```", "").strip()

                    try:
                        parsed_json = json.loads(cleaned)
                        pretty_json = json.dumps(parsed_json, indent=4)
                        st.success(f"✅ {file_name}")
                        st.code(pretty_json, language="json")
                        extracted_json = pretty_json
                    except Exception as json_error:
                        st.warning(f"⚠️ Failed to parse JSON for {file_name}")
                        st.text("Showing raw answer instead:")
                        st.code(cleaned)
                        extracted_json = cleaned  # fallback to raw string

                    # Save result even if parsing fails
                    extracted_data.append({
                        "File Name": file_name,
                        "Extracted JSON": extracted_json
                    })

                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}")
                    st.exception(e)

        # Export to Excel
        if extracted_data:
            df = pd.DataFrame(extracted_data)

            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Results')
                output.seek(0)

                st.markdown("### 📥 Download Extracted Data")
                st.download_button(
                    label="Download Excel File",
                    data=output,
                    file_name="extracted_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error("Failed to generate Excel file.")
                st.exception(e)

import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO

st.title("📄 Batch Document Processor with Excel Export + Preview")

# Authentication
email = st.text_input("Email ID")
access_token = st.text_input("Access Token", type="password")

# File upload
uploaded_files = st.file_uploader("Upload multiple documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# Hardcoded prompt
prompt = "Please extract structured information from the document."

# Process on button click
if st.button("Generate"):
    if not email or not access_token:
        st.error("Please enter Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        api_url = "https://your-api-endpoint.com/process"  # Replace with your actual API endpoint
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

                    # Clean markdown-style formatting
                    cleaned = answer_raw.replace("```json", "").replace("```", "").strip()

                    try:
                        parsed = json.loads(cleaned)
                        formatted = json.dumps(parsed, indent=4)
                        extracted_json = formatted
                    except json.JSONDecodeError:
                        extracted_json = cleaned  # fallback to raw cleaned string

                    # Store result
                    extracted_data.append({
                        "File Name": file_name,
                        "Extracted JSON": extracted_json
                    })

                except Exception as e:
                    extracted_data.append({
                        "File Name": uploaded_file.name,
                        "Extracted JSON": f"ERROR: {str(e)}"
                    })

        # Generate Excel + Display Table
        if extracted_data:
            df = pd.DataFrame(extracted_data)

            # Excel generation
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Extracted Results')
            output.seek(0)

            st.success("✅ All documents processed.")

            # Paginated table
            st.markdown("### 📊 Extracted Results Preview")

            page_size = 5
            total_rows = len(df)
            total_pages = (total_rows + page_size - 1) // page_size

            if total_pages > 1:
                page = st.selectbox(
                    "Select page to view",
                    options=list(range(1, total_pages + 1)),
                    format_func=lambda x: f"Page {x} of {total_pages}"
                )
            else:
                page = 1

            start = (page - 1) * page_size
            end = start + page_size
            st.dataframe(df.iloc[start:end])

            # Download Excel
            st.markdown("### 📥 Download Extracted Results")
            st.download_button(
                label="Download Excel File",
                data=output,
                file_name="extracted_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No data extracted.")

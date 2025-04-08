import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO

st.title("📄 Document Processor with Flattened Table & Excel Export")

# Auth inputs
email = "abhijeet.gorai@origamis.ai"
access_token = "gAAAAABnhKC-u2n1_mSWDlroFECWdd_qqplTHfPnplQncjC0B4A-oSxMplEf117Zd0uXSmiJKX-hS9UalpqS3CkQDmvGbhhKIvvfBt4QiBgOliL7_vl_FncrR9YkqLOTg5cL0T3pBOeNYpy5kEXbdgH9jAPJWP2yBw=="
uploaded_files = st.file_uploader("Upload documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])
prompt = """
1.You are Finance Manager who oversee the reimbursement process in the company.
2.Your task is to extract the following details from the Invoices:
i)Type of Reimbursement - 
If the Invoice is of a Flight, you will respond with "FLIGHT_REIMBURSEMENT".
Similarly If the Invoice is of a Hotel, you will respond with "HOTEL_REIMBURSEMENT".
Similarly you will handle all the different Invoice types.
ii)Name of the Particulars - Passenger Name or Customer Name
iii)Date of Journey -
	->Start Date - Date of Journey
	->End Date - Date of Reaching Destination
iv)Time of Journey - 
	->Start Time - Time of starting the journey on the date of journey
	->End Time - Time of reaching the destination
v)Total Cost - Total payable amount
3.Generate a single JSON object in the below format only:
{
	"Type of Reimbursement" : {},
	"Name of the Particulars" : {},
	"Date of Journey" : [
		"Start Date" :
		"End Date" :
	]
	"Time of Journey" : [ 
		"Start Time" :
		"End Time" :
	],
	"Total Cost"
}
4. Remove the '\n' and '\t' characters from the output JSON structure
"""

# Init session state
if "data_ready" not in st.session_state:
    st.session_state.data_ready = False
if "df_results" not in st.session_state:
    st.session_state.df_results = pd.DataFrame()
if "page" not in st.session_state:
    st.session_state.page = 1

# Helper to flatten nested JSON
def flatten_json(data):
    flat = {}

    for key, value in data.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                flat[f"{key} - {subkey}"] = subvalue
        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            for subkey, subvalue in value[0].items():
                flat[f"{key} - {subkey}"] = subvalue
        else:
            flat[key] = value

    return flat

# Process files
if st.button("Generate"):
    if not email or not access_token:
        st.error("Please enter both Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        api_url = "https://neptune.origamis.ai:9001/gear/process"  # Replace with your actual API URL
        final_rows = []

        st.session_state.page = 1  # Reset page
        with st.spinner("Processing..."):
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

                    cleaned = answer_raw.replace("```json", "").replace("```", "").strip()

                    try:
                        parsed = json.loads(cleaned)
                        flat_data = flatten_json(parsed)
                    except Exception as e:
                        flat_data = {"ERROR": f"Could not parse JSON: {str(e)}"}

                    flat_data["File Name"] = file_name
                    final_rows.append(flat_data)

                except Exception as e:
                    final_rows.append({
                        "File Name": uploaded_file.name,
                        "ERROR": f"API Error: {str(e)}"
                    })

        # Convert to DataFrame
        df = pd.DataFrame(final_rows)
        df = df[["File Name"] + [col for col in df.columns if col != "File Name"]]  # File Name first

        st.session_state.df_results = df
        st.session_state.data_ready = True

# Show results
if st.session_state.data_ready and not st.session_state.df_results.empty:
    df = st.session_state.df_results

    st.success("✅ Processing complete!")

    # Paginated view
    st.markdown("### 📊 Extracted Results (Flattened View)")
    page_size = 5
    total_rows = len(df)
    total_pages = (total_rows + page_size - 1) // page_size

    if total_pages > 1:
        selected_page = st.selectbox(
            "Select page:",
            options=list(range(1, total_pages + 1)),
            index=st.session_state.page - 1,
            format_func=lambda x: f"Page {x} of {total_pages}",
            key="page_selector"
        )
        st.session_state.page = selected_page
    else:
        st.session_state.page = 1

    start = (st.session_state.page - 1) * page_size
    end = start + page_size
    st.dataframe(df.iloc[start:end], use_container_width=True)

    # Excel export
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Extracted Results')
    output.seek(0)

    st.markdown("### 📥 Download Extracted Data")
    st.download_button(
        label="Download Excel File",
        data=output,
        file_name="extracted_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

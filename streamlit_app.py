import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO
import re
import demjson3

st.title("📄 Data Extraction")

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
When mentioning the value, strictly check for the following things:
1)If name is not specifically mentioned, you wil check for the passenger or customer name in the Invoice.
For Example: In Invoices like cabs, customer name will be often written with a Thanks message.
2)For invoices like cabs, you will never pick a name written with string "You rode with".
3)You will always keep First Letter of the Name should always be in Capital Letters.
For Example: If name is written like "manas", you will format it as "Manas".
4)You will always keep Mr or Mrs as appropriate saluation in the front of the name.
For Example: If name is written like "Mahendra", you will format it as "Mr Mahendra".
5)You will always mention name in the format: <Salutation> <First Name> <Surname>
For Example: If name is written like "Agarwal Manas", you will format it as "Mr Manas Agarwal".
iii)Date of Journey -
	->Start Date - Date of Journey
	->End Date - Date of Reaching Destination
When mentioning the date, you will strictly check for the following things:
1)Always keep date in the format: <dd> <Month> <Year>.
For Example: If date is mentioned as "Mon, 03 Feb 2025", then you should format as "03 Feb 2025"
If date is mentioned as "2025-03-21", then you should format as "21 Mar 2025"
2)If Start Date or End Date is not specifically mentioned in the Invoice, then you will keep it as None.
iv)Time of Journey - 
	->Start Time - Time of starting the journey on the date of journey
	->End Time - Time of reaching the destination
When mentioning the time,you will strictly check for the following things:
1)Always keep time in the 12 hour format and with AM or PM
For Example: If time is mentioned as 18:15, then you should format as 6:15 PM (In 12 hour format).
If time is mentioned as 9:00 then you should format as 9:00 AM and if time is mentioned as 1:00 then you should format as 1:00 PM.
2)If time not specifically mentioned, then you should keep 'None'.
v)Total Cost - Total payable amount
When mentioning the value, you will check for the following things:
1)Always keep the cost in the format: Rs <Amount>
For Example: If cost is mentioned as INR 7760, then you should format as Rs 7760.
3.Generate a single JSON object in the below format only:
{
	"Type of Reimbursement",
	"Name of the Particulars",
	"Date of Journey" : {
		"Start Date"
		"End Date"
	},
	"Time of Journey" : { 
		"Start Time"
		"End Time"
	},
	"Total Cost"
}
4. Remove the '\n' and '\t' characters from the output JSON structure
"""

# Session state
if "data_ready" not in st.session_state:
    st.session_state.data_ready = False
if "df_results" not in st.session_state:
    st.session_state.df_results = pd.DataFrame()
if "page" not in st.session_state:
    st.session_state.page = 1

# 🔧 Flatten nested JSON
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

# 🔧 JSON Repair using demjson3
def try_fix_json(broken_json_str):
    cleaned = broken_json_str.replace("```json", "").replace("```", "").strip()
    cleaned = re.sub(r'\\n', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return cleaned  # return cleaned raw string, demjson will handle parsing later

# Process files
if st.button("Generate"):
    if not email or not access_token:
        st.error("Please enter both Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        api_url = "https://neptune.origamis.ai:9001/gear/process"  # Replace with your actual API
        rows = []
        st.session_state.page = 1

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
                    raw_cleaned = try_fix_json(answer_raw)

                    try:
                        parsed = demjson3.decode(raw_cleaned)
                        flat_data = flatten_json(parsed)
                        flat_data["Raw Answer"] = raw_cleaned
                    except Exception as e:
                        flat_data = {
                            "ERROR": f"Could not fully parse JSON: {str(e)}",
                            "Raw Answer": raw_cleaned
                        }

                    flat_data["File Name"] = file_name
                    rows.append(flat_data)

                except Exception as e:
                    rows.append({
                        "File Name": uploaded_file.name,
                        "ERROR": f"API Error: {str(e)}",
                        "Raw Answer": "N/A"
                    })

        df = pd.DataFrame(rows)
        cols = ["File Name", "Raw Answer"] + [col for col in df.columns if col not in ["File Name", "Raw Answer"]]
        df = df[cols]

        st.session_state.df_results = df
        st.session_state.data_ready = True

# Display UI
if st.session_state.data_ready and not st.session_state.df_results.empty:
    df = st.session_state.df_results

    st.success("✅ All documents processed.")

    st.markdown("### 📊 Extracted Results with Raw JSON")

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

    # Download Excel
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

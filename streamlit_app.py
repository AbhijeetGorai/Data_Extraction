import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO
import re
import demjson3

st.set_page_config(layout="wide")
st.title("📄 Reimbursement Automation - With Rules")

# Category selection
category = st.selectbox("Select Reimbursement Category", ["L1 - Manager/Senior Manager", "L2 - Director and above"])

# Rules definition
rules = {
    "L1 - Manager/Senior Manager": {
        "Travel": "Not allowed",
        "Hotel (per night)": "Up to ₹3000",
        "Food (per day)": "Up to ₹600"
    },
    "L2 - Director and above": {
        "Travel": "Allowed",
        "Hotel (per night)": "Up to ₹6000",
        "Food (per day)": "Up to ₹1200"
    }
}
rules_df = pd.DataFrame(rules[category].items(), columns=["Category", "Limit"])
st.markdown("### 🧾 Reimbursement Rules")
st.table(rules_df)

# Upload files
uploaded_files = st.file_uploader("Upload documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# Credentials
email = "abhijeet.gorai@origamis.ai"
access_token = "gAAAAABnhKC-u2n1_mSWDlroFECWdd_qqplTHfPnplQncjC0B4A-oSxMplEf117Zd0uXSmiJKX-hS9UalpqS3CkQDmvGbhhKIvvfBt4QiBgOliL7_vl_FncrR9YkqLOTg5cL0T3pBOeNYpy5kEXbdgH9jAPJWP2yBw=="  # Your actual token

# Prompt (your custom full prompt goes here)
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
6)If more than one name is mentioned in the Invoice, then you will mention both the names <name1> and <name2> and <name N>
For Example: If 2 names Ram,Shyam is mentioned in the Invoice, you will format as "Ram and Shyam".
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

# Flatten JSON
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

# Extract numeric value
def extract_amount(amount_str):
    if not amount_str:
        return 0.0
    digits = re.sub(r"[^\d.]", "", amount_str.replace(",", ""))
    try:
        return float(digits)
    except:
        return 0.0

# Validation logic
def evaluate_reimbursement(flat_data, level):
    cost = extract_amount(flat_data.get("Total Cost", "0"))
    rtype = flat_data.get("Type of Reimbursement", "").upper()
    travel_keywords = ["FLIGHT", "TAXI", "CAB", "AUTO", "RIDE", "TRAVEL", "TRAIN"]

    if level == "L1 - Manager/Senior Manager":
        if any(keyword in rtype for keyword in travel_keywords):
            return "FAIL: Travel reimbursement not allowed for L1"
        if rtype == "HOTEL_REIMBURSEMENT" and cost > 3000:
            return "FAIL: Hotel cost exceeds ₹3000 limit for L1"
        if "FOOD" in rtype and cost > 600:
            return "FAIL: Food cost exceeds ₹600 limit for L1"
    elif level == "L2 - Director and above":
        if rtype == "HOTEL_REIMBURSEMENT" and cost > 6000:
            return "FAIL: Hotel cost exceeds ₹6000 limit for L2"
        if "FOOD" in rtype and cost > 1200:
            return "FAIL: Food cost exceeds ₹1200 limit for L2"

    return "PASS"

# Clean and flatten JSON string
def try_fix_json(broken_json_str):
    cleaned = broken_json_str.replace("```json", "").replace("```", "").strip()
    cleaned = re.sub(r'\\n', '', cleaned)
    cleaned = re.sub(r'[\t\r\n]+', ' ', cleaned)  # make it one line
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    cleaned = re.sub(r'(?<=:\s)(None)(?=[,\}\]])', 'null', cleaned)
    return cleaned

# Status icon for display
def get_status_icon(val):
    if isinstance(val, str) and val.startswith("PASS"):
        return "✅ PASS"
    elif isinstance(val, str) and val.startswith("FAIL"):
        return "❌ " + val.replace("FAIL: ", "")
    return val

# Process files
if st.button("Generate"):
    if not email or not access_token:
        st.error("Missing credentials.")
    elif not uploaded_files:
        st.error("Please upload documents.")
    else:
        api_url = "https://neptune.origamis.ai:9001/gear/process"
        rows = []
        st.session_state.page = 1

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
                    raw_cleaned = try_fix_json(answer_raw)

                    try:
                        parsed = demjson3.decode(raw_cleaned)
                        flat_data = flatten_json(parsed)
                        flat_data["Raw Answer"] = raw_cleaned
                    except Exception as e:
                        flat_data = {
                            "ERROR": f"Parse Error: {str(e)}",
                            "Raw Answer": raw_cleaned
                        }

                    flat_data["File Name"] = file_name
                    flat_data["Category"] = category
                    flat_data["Validation Status"] = evaluate_reimbursement(flat_data, category)
                    flat_data["Validation"] = get_status_icon(flat_data["Validation Status"])
                    rows.append(flat_data)

                except Exception as e:
                    rows.append({
                        "File Name": uploaded_file.name,
                        "ERROR": f"API Error: {str(e)}",
                        "Raw Answer": "N/A",
                        "Category": category,
                        "Validation Status": "FAIL: API Error",
                        "Validation": "❌ API Error"
                    })

        df = pd.DataFrame(rows)
        cols = ["File Name", "Category", "Validation", "Raw Answer"] + [
            col for col in df.columns if col not in ["File Name", "Raw Answer", "Category", "Validation Status", "Validation"]
        ]
        df = df[cols]

        st.session_state.df_results = df
        st.session_state.data_ready = True

# Display table
if st.session_state.data_ready and not st.session_state.df_results.empty:
    df = st.session_state.df_results
    st.success("✅ Documents processed.")

    st.markdown("### 📊 Extracted & Validated Results")

    page_size = 5
    total_pages = (len(df) + page_size - 1) // page_size
    selected_page = st.selectbox(
        "Select page:",
        options=list(range(1, total_pages + 1)),
        index=st.session_state.page - 1,
        format_func=lambda x: f"Page {x} of {total_pages}",
        key="page_selector"
    )
    st.session_state.page = selected_page

    start = (selected_page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    # Use st.dataframe for interactive compact layout
    st.dataframe(page_df, use_container_width=True)

    # Excel export
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Extracted Results')
    output.seek(0)

    st.markdown("### 📥 Download Results")
    st.download_button(
        label="Download Excel File",
        data=output,
        file_name="extracted_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

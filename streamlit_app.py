import streamlit as st
import requests
import json

st.title("📄 Document Processor")

# --- Input fields ---
email = "abhijeet.gorai@origamis.ai"
access_token = "gAAAAABnhKC-u2n1_mSWDlroFECWdd_qqplTHfPnplQncjC0B4A-oSxMplEf117Zd0uXSmiJKX-hS9UalpqS3CkQDmvGbhhKIvvfBt4QiBgOliL7_vl_FncrR9YkqLOTg5cL0T3pBOeNYpy5kEXbdgH9jAPJWP2yBw=="
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

# --- File uploader ---
uploaded_files = st.file_uploader(
    "📎 Upload your documents",
    accept_multiple_files=True,
    type=["pdf", "docx", "txt"]
)

# --- Generate button ---
if st.button("🚀 Generate"):
    if not email or not access_token or not prompt:
        st.error("⚠️ Please fill in Email, Access Token, and Prompt.")
    elif not uploaded_files:
        st.error("⚠️ Please upload at least one document.")
    else:
        try:
            # Prepare files for upload
            files = []
            for f in uploaded_files:
                files.append(("file", (f.name, f.read(), f.type)))

            # Prepare data payload
            data = {
                "access_token": access_token,
                "email": email,
                "prompt": prompt
            }

            # ✅ Update to your actual backend API URL
            api_url = "https://neptune.origamis.ai:9001/gear/process"  # Replace this with your real endpoint

            with st.spinner("⏳ Processing documents..."):
                response = requests.post(api_url, data=data, files=files)

            if response.status_code == 200:
                result = response.json()

                if result.get("status") == "success":
                    raw_answer = result["message"]["answer"]
                    file_name = result["message"].get("fileName", "Unknown file")

                    # --- Strip markdown code block ---
                    if raw_answer.startswith("```json"):
                        raw_answer = raw_answer[len("```json"):].strip()
                    if raw_answer.endswith("```"):
                        raw_answer = raw_answer[:-len("```")].strip()

                    try:
                        parsed_json = json.loads(raw_answer)
                        st.success("✅ Documents processed successfully!")
                        st.markdown(f"**File:** {file_name}")
                        st.markdown("### 🧾 Extracted Information")
                        st.json(parsed_json)
                    except json.JSONDecodeError:
                        st.warning("⚠️ Couldn't parse the response as valid JSON.")
                        st.text(raw_answer)
                else:
                    st.error("❌ API responded with an error.")
                    st.write(result)
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.text(response.text)

        except Exception as e:
            st.error("⚠️ Something went wrong with the API call.")
            st.exception(e)

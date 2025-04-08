import streamlit as st
import requests
import json

st.title("Document Processor")

# Auth inputs
email = st.text_input("Email ID")
access_token = st.text_input("Access Token", type="password")

# File uploader
uploaded_files = st.file_uploader("Upload your documents", accept_multiple_files=True, type=["pdf", "docx", "txt"])

# Hardcoded prompt
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

# Generate button
if st.button("Generate"):
    if not email or not access_token:
        st.error("Please fill in Email ID and Access Token.")
    elif not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        try:
            # Prepare files
            files = []
            for f in uploaded_files:
                files.append(("file", (f.name, f.read(), f.type)))

            # Form data
            data = {
                "access_token": access_token,
                "email": email,
                "prompt": prompt
            }

            # API endpoint
            api_url = "https://dataextraction-gear.streamlit.app/"  # 🔁 Replace this

            with st.spinner("Calling API..."):
                response = requests.post(api_url, data=data, files=files)

            # Try extracting JSON content
            try:
                api_result = response.json()
            except json.JSONDecodeError:
                st.error("API did not return valid JSON.")
                st.code(response.text)
                st.stop()

            # Extract the 'answer' field
            answer_raw = api_result.get("message", {}).get("answer", None)

            if not answer_raw:
                st.warning("No answer found in API response.")
                st.json(api_result)
                st.stop()

            # Clean markdown-style formatting
            cleaned_json_str = (
                answer_raw.replace("```json", "")
                .replace("```", "")
                .strip()
            )

            # Try parsing the cleaned string into JSON
            try:
                parsed_json = json.loads(cleaned_json_str)
                pretty_json = json.dumps(parsed_json, indent=4)

                st.success("Structured Result Extracted:")
                st.code(pretty_json, language="json")

            except Exception as e:
                st.error("Couldn't parse the 'answer' content as JSON.")
                st.text("Raw content:")
                st.code(cleaned_json_str)
                st.exception(e)

        except Exception as e:
            st.error("Something went wrong during the API call.")
            st.exception(e)

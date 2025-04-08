import streamlit as st
import requests
import json

st.title("📄 Document Processor")

# --- Input fields ---
email = st.text_input("📧 Email ID")
access_token = st.text_input("🔐 Access Token", type="password")
prompt = st.text_area("💬 Enter your prompt")

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

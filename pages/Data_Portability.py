import streamlit as st
from datetime import datetime
from data_io import export_data_json, export_data_csv_zip, import_data_json
from database import get_assessments
from notifications import success, error, warning, info

from styles.theme import apply_theme

apply_theme()
from datetime import datetime


def render_export_card(
    title,
    description,
    button_label,
    export_function,
    session_key,
    filename,
    mime_type,
    empty_check,
    format_name,
    download_key,
):
    st.subheader(title)
    st.markdown(description)

    if st.button(button_label):
        with st.spinner(f"Generating {format_name}..."):
            export_data = export_function()

            if not empty_check(export_data):
                st.session_state[session_key] = export_data
            else:
                warning(
                    "⚠️ No data available to export. Add some data before exporting."
                )

    if st.session_state.get(session_key):
        success("✅ Export generated successfully!")

        st.markdown("#### Export Details")
        st.markdown(f"**📄 File Name:** `{filename}`")
        st.markdown(f"**🗂 Format:** {format_name}")
        st.markdown(
            f"**🕒 Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        st.download_button(
            label=f"⬇️ Download {format_name}",
            data=st.session_state[session_key],
            file_name=filename,
            mime=mime_type,
            key=download_key,
        )

# -----------------------------
# Session State Initialization
# -----------------------------
if "csv_export" not in st.session_state:
    st.session_state.csv_export = None

if "json_export" not in st.session_state:
    st.session_state.json_export = None


def show_export_details(file_name: str, export_format: str):
    success("✅ Export generated successfully!")

    st.markdown("#### Export Details")
    st.markdown(f"**📄 File Name:** `{file_name}`")
    st.markdown(f"**🗂 Format:** {export_format}")
    st.markdown(
        f"**🕒 Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )



st.title("💾 Data Portability")
st.markdown(
    "Manage your EcoBuddy data. You can export your data to take it with you, "
    "or import previously exported data to restore your profile."
)

user_id = st.session_state.get('user_id')
assessments = get_assessments(user_id=user_id) if user_id else get_assessments()
assessment_count = len(assessments) if assessments else 0

if assessment_count >= 5:
    warning(
        f"⚠️ **Backup Recommended:** You have accumulated **{assessment_count} saved assessments**. "
        "Consider exporting a backup copy below to ensure your data is safe."
    )

st.markdown("---")
st.header("📤 Export Data")
st.markdown(
    "Export your assessments, appliances, gamification progress, and more."
)

col1, col2 = st.columns(2)

# ======================================================
# CSV EXPORT
# ======================================================
with col1:

    render_export_card(
        title="CSV Export",
        description=(
            "Download your core data tables as CSV files bundled in a ZIP archive. "
            "This format is great for analyzing your data in Excel or other tools."
        ),
        button_label="Generate CSV Archive",
        export_function=export_data_csv_zip,
        session_key="csv_export",
        filename="ecobuddy_export.zip",
        mime_type="application/zip",
        empty_check=lambda data: not data,
        format_name="ZIP (CSV Archive)",
        download_key="download_csv_zip",
    )

    st.subheader("CSV Export")
    st.markdown(
        "Download your core data tables as CSV files bundled in a ZIP archive. "
        "This format is great for analyzing your data in Excel or other tools."
    )

    if st.button("Generate CSV Archive"):
        with st.spinner("Generating CSV archive..."):
            zip_data = export_data_csv_zip()

            if zip_data:
                st.session_state.csv_export = zip_data
            else:
                warning(
                    "⚠️ No data available to export. Add some data before exporting."
                )

    if st.session_state.csv_export:
        show_export_details(
            "ecobuddy_export.zip",
            "ZIP (CSV Archive)"
        )


        st.download_button(
            label="⬇️ Download ZIP",
            data=st.session_state.csv_export,
            file_name="ecobuddy_export.zip",
            mime="application/zip",
            key="download_csv_zip",
        )


# ======================================================
# JSON EXPORT
# ======================================================
with col2:

    render_export_card(
        title="JSON Export",
        description=(
            "Download a full dump of your data in JSON format. "
            "This format is required if you want to import your data back into EcoBuddy later."
        ),
        button_label="Generate JSON Export",
        export_function=export_data_json,
        session_key="json_export",
        filename="ecobuddy_export.json",
        mime_type="application/json",
        empty_check=lambda data: data == "{}",
        format_name="JSON",
        download_key="download_json",
    )

    st.subheader("JSON Export")
    st.markdown(
        "Download a full dump of your data in JSON format. "
        "This format is required if you want to import your data back into EcoBuddy later."
    )

    if st.button("Generate JSON Export"):
        with st.spinner("Generating JSON export..."):
            json_data = export_data_json()

            if json_data != "{}":
                st.session_state.json_export = json_data
            else:
                warning(
                    "⚠️ No data available to export. Add some data before exporting."
                )

    if st.session_state.json_export:
        show_export_details(
            "ecobuddy_export.json",
            "JSON"
        )

        st.download_button(
            label="⬇️ Download JSON",
            data=st.session_state.json_export,
            file_name="ecobuddy_export.json",
            mime="application/json",
            key="download_json",
        )



st.markdown("---")
st.header("📥 Import Data")
st.markdown(
    "Restore your data from a previously exported JSON file."
)

import_strategy = st.radio(
    "Import Strategy",
    options=["Merge", "Replace"],
    index=0,
    help=(
        "Merge: Keeps your existing data and adds new non-duplicate entries. "
        "Replace: Deletes your current data and replaces it entirely with the imported data."
    ),
)

uploaded_file = st.file_uploader(
    "Upload JSON Export File",
    type=["json"],
)

import json

if uploaded_file is not None:
    if st.button("Restore Data"):


        # Read uploaded file
        file_bytes = uploaded_file.read()

        # Empty file validation
        if not file_bytes:
            error("❌ The uploaded file is empty. Please upload a valid EcoBuddy JSON export.")
            st.stop()

        # Decode validation
        try:
            json_content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            error("❌ Unable to read the file. Please upload a UTF-8 encoded JSON file.")
            st.stop()

        # Empty content validation
        if not json_content.strip():
            error("❌ The uploaded file contains no data.")
            st.stop()

        # JSON validation
        try:
            json.loads(json_content)
        except json.JSONDecodeError as e:
            error(f"❌ Invalid JSON file.\n\nDetails: {e}")
            st.stop()

        # Import only after validation passes

        json_content = uploaded_file.read().decode("utf-8")


        with st.spinner("Importing data..."):
            import_success, message = import_data_json(
                json_content,
                strategy=import_strategy.lower(),

user_id = st.session_state.get('user_id')
if not user_id:
    warning('Please log in from the main application page.')
    st.stop()
            )

            if import_success:
                success(message)
                info(
                    "Please refresh the page or navigate to another section "
                    "to see the restored data."
                )
            else:
                error(message)
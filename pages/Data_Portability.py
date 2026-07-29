import streamlit as st
import json
import sys
from datetime import datetime
from data_io import export_data_json, export_data_csv_zip, import_data_json
from database import get_assessments
from background_tasks import submit_background_task, render_task_progress, clear_background_task
from styles.theme import apply_theme

apply_theme()


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

    task_key = f"bg_export_{session_key}"

    if st.button(button_label, key=f"btn_bg_{session_key}"):
        submit_background_task(
            task_key,
            export_function,
            task_name=f"Generating {format_name}"
        )

    is_done, export_data = render_task_progress(
        task_key,
        success_msg=f"{format_name} generated successfully!"
    )

    if is_done and export_data is not None:
        if not empty_check(export_data):
            st.session_state[session_key] = export_data
        else:
            st.warning("⚠️ No data available to export. Add some data before exporting.")
        clear_background_task(task_key)

    if st.session_state.get(session_key):
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


st.title("💾 Data Portability")
st.markdown(
    "Manage your EcoBuddy data. You can export your data to take it with you, "
    "or import previously exported data to restore your profile."
)

user_id = st.session_state.get('user_id')
assessments = get_assessments(user_id=user_id) if user_id else get_assessments()
assessment_count = len(assessments) if assessments else 0

if assessment_count >= 5:
    st.warning(
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

if import_strategy == "Replace":
    st.warning(
        "⚠ **Warning:** Replace will permanently delete your current EcoBuddy data before importing the new backup."
    )

uploaded_file = st.file_uploader(
    "Upload JSON Export File",
    type=["json"],
)

if uploaded_file is not None:
    try:
        json_bytes = uploaded_file.read()
        json_content = json_bytes.decode("utf-8")
        preview = json.loads(json_content)

        st.success("✅ Valid backup file detected")

        st.subheader("📋 Backup Preview")
        total_records = 0

        for key, value in preview.items():
            if isinstance(value, list):
                total_records += len(value)
                st.write(f"**{key.replace('_',' ').title()}** : {len(value)} records")

        st.info(f"📦 Total Records: {total_records}")
        file_size = uploaded_file.size / 1024
        st.caption(f"File Size: {file_size:.2f} KB")

        confirm_replace = True
        if import_strategy == "Replace":
            confirm_replace = st.checkbox(
                "I understand that my existing data will be permanently deleted."
            )

        if st.button("Restore Data") and confirm_replace:
            if not json_content.strip():
                st.error("❌ The uploaded file contains no data.")
            else:
                submit_background_task(
                    "bg_import_json",
                    import_data_json,
                    json_content,
                    strategy=import_strategy.lower(),
                    task_name="Restoring Backup Data"
                )

    except Exception:
        st.error("❌ Invalid JSON file.")

is_done, import_result = render_task_progress(
    "bg_import_json",
    success_msg="Import operation completed!"
)

if is_done and import_result is not None:
    success, message = import_result
    if success:
        st.success(message)
        st.info(
            "Please refresh the page or navigate to another section "
            "to see the restored data."
        )
    else:
        st.error(message)
    clear_background_task("bg_import_json")

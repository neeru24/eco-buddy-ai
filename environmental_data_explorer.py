"""Open Environmental Data Explorer UI and core logic."""

from __future__ import annotations

import json
import pandas as pd
import streamlit as st
from database import (
    get_environmental_datasets,
    add_environmental_dataset,
)

DATA_CATEGORIES = [
    "All Categories",
    "Global Carbon Emissions",
    "Air Quality Index",
    "Renewable Energy Growth",
    "Deforestation Rates",
    "Ocean Temperatures",
]


def render_environmental_data_explorer() -> None:
    """Render the Open Environmental Data Explorer interface."""
    st.title("🌐 Open Environmental Data Explorer")
    st.markdown(
        "Explore publicly available environmental datasets, preview data trends, "
        "and download structured dataset metadata for research."
    )

    tab1, tab2 = st.tabs(["📊 Browse & Preview Datasets", "➕ Contribute Dataset"])

    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_cat = st.selectbox(
                "Filter by Category",
                options=DATA_CATEGORIES,
                key="data_exp_category_select",
            )
        with col2:
            search_query = st.text_input(
                "Search Datasets",
                placeholder="e.g. CO2, Air Quality, Solar, Amazon...",
                key="data_exp_search_input",
            )

        datasets = get_environmental_datasets(
            category=selected_cat,
            search_query=search_query.strip() if search_query else None,
        )

        st.markdown(f"### Available Datasets ({len(datasets)})")

        if not datasets:
            st.info("No environmental datasets matched your search criteria.")
        else:
            for ds in datasets:
                with st.expander(f"📁 {ds['title']} — [{ds['category']}]", expanded=False):
                    st.caption(
                        f"**Provider:** {ds['provider']} | **License:** {ds['license']} | "
                        f"**Update Frequency:** {ds['update_frequency']}"
                    )
                    st.write(ds["description"])

                    # Parse data JSON
                    data_obj = _parse_data_json(ds["data_json"])
                    if data_obj and "headers" in data_obj and "records" in data_obj:
                        df = pd.DataFrame(data_obj["records"], columns=data_obj["headers"])
                        st.markdown("#### 📈 Data Preview")
                        st.dataframe(df, use_container_width=True)

                        # Display basic summary metrics
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric("Total Rows", len(df))
                        with c2:
                            st.metric("Total Columns", len(df.columns))
                        with c3:
                            st.metric("License", ds["license"])

                        # Download metadata & dataset
                        col_json, col_csv = st.columns(2)
                        with col_json:
                            metadata_json = json.dumps(
                                {
                                    "title": ds["title"],
                                    "category": ds["category"],
                                    "provider": ds["provider"],
                                    "license": ds["license"],
                                    "update_frequency": ds["update_frequency"],
                                    "description": ds["description"],
                                    "data": data_obj,
                                },
                                indent=2,
                            )
                            st.download_button(
                                label="📥 Download Metadata (JSON)",
                                data=metadata_json,
                                file_name=f"{_slugify(ds['title'])}_metadata.json",
                                mime="application/json",
                                key=f"dl_json_{ds['id']}",
                            )
                        with col_csv:
                            csv_data = df.to_csv(index=False)
                            st.download_button(
                                label="📊 Download Preview Data (CSV)",
                                data=csv_data,
                                file_name=f"{_slugify(ds['title'])}_preview.csv",
                                mime="text/csv",
                                key=f"dl_csv_{ds['id']}",
                            )
                    else:
                        st.warning("Data preview unavailable for this dataset.")

    with tab2:
        st.markdown("### Contribute an Environmental Dataset")
        with st.form("add_dataset_form", clear_on_submit=True):
            title = st.text_input("Dataset Title", placeholder="e.g. European Solar Energy Output (2020-2025)")
            category = st.selectbox("Category", options=[c for c in DATA_CATEGORIES if c != "All Categories"])
            provider = st.text_input("Provider / Source", placeholder="e.g. Copernicus Climate Change Service")
            license_type = st.text_input("License", value="CC-BY-4.0")
            update_freq = st.selectbox("Update Frequency", options=["Daily", "Monthly", "Quarterly", "Annual"])
            description = st.text_area("Dataset Description & Scope")

            st.markdown("#### Preview Data (JSON format: `{\"headers\": [...], \"records\": [[...]]}`)")
            data_json_input = st.text_area(
                "JSON Data Snippet",
                value='{\n  "headers": ["Year", "Output_TWh"],\n  "records": [\n    [2024, 142.5],\n    [2025, 168.0]\n  ]\n}',
            )

            submit = st.form_submit_button("Submit Dataset 🚀")

            if submit:
                if not title or not provider or not description or not data_json_input:
                    st.error("Please fill in all required fields.")
                else:
                    try:
                        # Validate JSON
                        parsed = json.loads(data_json_input)
                        if "headers" not in parsed or "records" not in parsed:
                            st.error("JSON must contain 'headers' and 'records' keys.")
                        else:
                            success = add_environmental_dataset(
                                title=title,
                                category=category,
                                provider=provider,
                                license=license_type,
                                update_frequency=update_freq,
                                description=description,
                                data_json=json.dumps(parsed),
                            )
                            if success:
                                st.success(f"Dataset '{title}' added successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to add dataset. Title may already exist.")
                    except json.JSONDecodeError as exc:
                        st.error(f"Invalid JSON format: {exc}")


def _parse_data_json(json_str: str) -> dict | None:
    """Parse data JSON string safely."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


def _slugify(text: str) -> str:
    """Convert text string into safe filename slug."""
    return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_")

"""Sustainable Brand Directory UI and core logic."""

from __future__ import annotations

import streamlit as st
from database import get_sustainable_brands, add_sustainable_brand

CATEGORIES = [
    "All Categories",
    "Apparel & Footwear",
    "Food & Beverage",
    "Home & Energy",
    "Personal Care",
    "Tech & Electronics",
    "Transportation",
]


def render_brand_directory() -> None:
    """Render the Sustainable Brand Directory interface."""
    st.title("🛍️ Sustainable Brand Directory")
    st.markdown(
        "Discover environmentally responsible companies, compare sustainability ratings, "
        "and make greener purchasing decisions."
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_category = st.selectbox(
            "Browse Categories",
            options=CATEGORIES,
            index=0,
            key="brand_dir_category_select",
        )
    with col2:
        search_query = st.text_input(
            "Search Brands, Keywords, or Certifications",
            placeholder="e.g. Patagonia, B Corp, Organic, Solar...",
            key="brand_dir_search_input",
        )

    brands = get_sustainable_brands(
        category=selected_category,
        search_query=search_query.strip() if search_query else None,
    )

    st.markdown(f"### Found {len(brands)} Sustainable Brand(s)")

    if not brands:
        st.info("No brands matched your search criteria. Try a different query or category.")
    else:
        for brand in brands:
            with st.container():
                cols = st.columns([3, 1, 1])
                with cols[0]:
                    st.markdown(f"#### [{brand['name']}]({brand['website']})")
                    st.caption(f"**Category:** {brand['category']}")
                    st.write(brand["description"])
                    if brand.get("certifications"):
                        certs = [c.strip() for c in brand["certifications"].split(",")]
                        cert_badges = " ".join([f"`{c}`" for c in certs])
                        st.markdown(f"**Certifications:** {cert_badges}")
                with cols[1]:
                    rating = brand["sustainability_rating"]
                    badge_color = "#22c55e" if "A" in rating else "#eab308" if "B" in rating else "#3b82f6"
                    st.markdown(
                        f"""
                        <div style="text-align: center; padding: 10px; border-radius: 8px; background: rgba(34, 197, 94, 0.1); border: 1px solid {badge_color};">
                            <div style="font-size: 12px; color: gray;">RATING</div>
                            <div style="font-size: 24px; font-weight: bold; color: {badge_color};">{rating}</div>
                            <div style="font-size: 13px; margin-top: 4px;">Score: <strong>{brand['eco_score']}/100</strong></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with cols[2]:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.link_button("🌐 Visit Website", brand["website"])

                st.divider()

    # Expandable section to add new brand
    with st.expander("➕ Suggest / Add a Sustainable Brand"):
        with st.form("add_brand_form", clear_on_submit=True):
            name = st.text_input("Brand Name")
            category = st.selectbox("Category", options=[c for c in CATEGORIES if c != "All Categories"])
            rating = st.selectbox("Sustainability Rating Grade", options=["A+", "A", "A-", "B+", "B", "B-", "C"])
            eco_score = st.slider("Eco Score (0 - 100)", min_value=0, max_value=100, value=85)
            certifications = st.text_input("Certifications (comma-separated)", placeholder="e.g. B Corp, Fair Trade")
            description = st.text_area("Brand Overview & Sustainability Practices")
            website = st.text_input("Official Website URL", placeholder="https://example.com")
            submit = st.form_submit_button("Submit Brand")

            if submit:
                if not name or not website or not description:
                    st.error("Please fill in the required fields (Name, Website, Description).")
                else:
                    if not website.startswith("http://") and not website.startswith("https://"):
                        website = "https://" + website
                    success = add_sustainable_brand(
                        name=name,
                        category=category,
                        sustainability_rating=rating,
                        eco_score=eco_score,
                        certifications=certifications,
                        description=description,
                        website=website,
                    )
                    if success:
                        st.success(f"Brand '{name}' added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add brand. It may already exist.")

import streamlit as st
import pandas as pd
from sustainability_library import (
    RESOURCE_TYPES, CATEGORIES, TAGS, search_resources,
    save_favorite, remove_favorite, get_favorites,
    mark_completed, get_completed,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>📚 Sustainability Library</div>", unsafe_allow_html=True)
st.markdown(
    "A curated library of books, documentaries, podcasts, and YouTube channels "
    "to keep your environmental learning going. Search, save favorites, and "
    "track what you've completed."
)

favorites = get_favorites(user_id)
completed = get_completed(user_id)

st.markdown("---")

c1, c2 = st.columns([1, 2])
with c1:
    category = st.selectbox("Category", CATEGORIES)
with c2:
    query = st.text_input("Search", placeholder="e.g., climate, fashion, energy, waste...")

st.markdown("---")

results = search_resources(query, category)

st.markdown(f"### 🗂️ Found {len(results)} resource{'s' if len(results) != 1 else ''}")

if not results:
    st.info("No resources match your search. Try a different keyword or category.")
else:
    for item in results:
        title = item.get("title", "")
        rtype = item.get("type", "")
        rid = item.get("id", "")

        meta_bits = []
        for key in ("author", "host", "channel", "director"):
            if item.get(key):
                meta_bits.append(item[key])
        if item.get("year"):
            meta_bits.append(str(item["year"]))
        meta = " · ".join(meta_bits)

        tag_str = " ".join(
            f"{TAGS.get(t, '#')} {t}" for t in item.get("tags", [])
        )

        is_fav = rid in favorites
        is_done = rid in completed

        with st.expander(f"{RESOURCE_TYPES.get(rtype, '📖')} **{title}** {('✅' if is_done else '')}"):
            if meta:
                st.caption(meta)
            st.write(item.get("summary", ""))
            if tag_str:
                st.caption(tag_str)
            if item.get("link"):
                st.markdown(f"[🔗 Open resource]({item['link']})")

            b1, b2, b3 = st.columns(3)
            with b1:
                if is_fav:
                    if st.button("⭐ Saved", key=f"unsave_{rid}"):
                        remove_favorite(user_id, rid)
                        st.rerun()
                else:
                    if st.button("☆ Save", key=f"save_{rid}", use_container_width=True):
                        save_favorite(user_id, rid)
                        st.rerun()
            with b2:
                if is_done:
                    st.markdown("✅ Completed")
                else:
                    if st.button("✔️ Mark Completed", key=f"done_{rid}", use_container_width=True):
                        mark_completed(user_id, rid)
                        st.rerun()
            with b3:
                st.markdown(" ")

st.markdown("---")

tab_fav, tab_done = st.tabs(["⭐ My Favorites", "✅ Completed Resources"])

with tab_fav:
    if favorites:
        fav_results = search_resources("", "All")
        fav_items = [r for r in fav_results if r["id"] in favorites]
        for item in fav_items:
            rtype = item.get("type", "")
            st.markdown(f"- **{item['title']}** — {RESOURCE_TYPES.get(rtype, '')}")
    else:
        st.info("You haven't saved any favorites yet. Click ☆ Save on a resource.")

with tab_done:
    if completed:
        done_results = search_resources("", "All")
        done_items = [r for r in done_results if r["id"] in completed]
        for item in done_items:
            rtype = item.get("type", "")
            st.markdown(f"- ✅ **{item['title']}** — {RESOURCE_TYPES.get(rtype, '')}")
        st.caption(f"You've completed **{len(completed)}** resource{'s' if len(completed) != 1 else ''} — great work!")
    else:
        st.info("Mark resources as completed to track your learning progress.")

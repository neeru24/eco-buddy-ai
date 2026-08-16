"""
Local Biodiversity Explorer Module (#352).

Enables exploration of native flora, birds, wildlife, and pollinators by region and category.
Includes species search, conservation status tracking, carbon impact ratings, and environmental facts.
"""

from typing import List, Dict, Any
import pandas as pd
import streamlit as st


CONSERVATION_STATUS_MAP = {
    "LC": {"label": "Least Concern", "color": "🟢", "bg": "#E8F5E9"},
    "NT": {"label": "Near Threatened", "color": "🟡", "bg": "#FFFDE7"},
    "VU": {"label": "Vulnerable", "color": "🟠", "bg": "#FFF3E0"},
    "EN": {"label": "Endangered", "color": "🔴", "bg": "#FFEBEE"},
    "CR": {"label": "Critically Endangered", "color": "🚨", "bg": "#FFCDD2"},
}


SPECIES_DATABASE: List[Dict[str, Any]] = [
    {
        "id": 1,
        "common_name": "Oak Tree (Quercus robur)",
        "scientific_name": "Quercus robur",
        "category": "Flora & Trees",
        "regions": ["Europe", "North America", "Global Urban"],
        "conservation_status": "LC",
        "carbon_impact": "High (Sequesters ~22kg CO2/year)",
        "ecological_role": "Primary habitat and food source for over 500 insect and bird species.",
        "environmental_facts": [
            "A single mature oak tree absorbs up to 48 pounds of CO2 annually.",
            "Supports high microbial and fungal biodiversity in root soil ecosystems.",
        ],
        "threats": "Deforestation, climate change induced droughts, and root rot.",
        "protection_tip": "Plant native oak saplings and avoid soil compaction around drip lines.",
    },
    {
        "id": 2,
        "common_name": "Monarch Butterfly",
        "scientific_name": "Danaus plexippus",
        "category": "Pollinators & Insects",
        "regions": ["North America", "Global Urban"],
        "conservation_status": "EN",
        "carbon_impact": "Essential Pollinator",
        "ecological_role": "Vital pollinator for wildflowers, crops, and native plants.",
        "environmental_facts": [
            "Monarch caterpillars feed exclusively on milkweed plants.",
            "Migrates up to 3,000 miles across North America every autumn.",
        ],
        "threats": "Pesticide usage, milkweed habitat loss, and climate shifts.",
        "protection_tip": "Plant native milkweed species and pesticide-free nectar flowers.",
    },
    {
        "id": 3,
        "common_name": "Peregrine Falcon",
        "scientific_name": "Falco peregrinus",
        "category": "Birds & Avian",
        "regions": ["North America", "Europe", "Asia", "Global Urban"],
        "conservation_status": "LC",
        "carbon_impact": "Apex Bio-indicator",
        "ecological_role": "Apex avian predator that controls urban and wild bird populations.",
        "environmental_facts": [
            "Fastest bird in the world, reaching diving speeds over 240 mph.",
            "Successfully adapted to urban skyscraper nesting ledges.",
        ],
        "threats": "Historical organochlorine pesticides, window collisions.",
        "protection_tip": "Support bird-safe building glass designs and raptor rehabilitation.",
    },
    {
        "id": 4,
        "common_name": "Honey Bee",
        "scientific_name": "Apis mellifera",
        "category": "Pollinators & Insects",
        "regions": ["Europe", "North America", "Asia", "Global Urban"],
        "conservation_status": "NT",
        "carbon_impact": "Critical Crop Pollinator",
        "ecological_role": "Pollinates over 80% of flowering plants and agricultural food crops.",
        "environmental_facts": [
            "A single bee colony can visit up to 50 million flowers per day.",
            "Provides natural ecosystem pollination valued in billions of dollars.",
        ],
        "threats": "Neonicotinoid pesticides, Varroa mites, and habitat fragmentation.",
        "protection_tip": "Create bee gardens with diverse, chemical-free wildflowers.",
    },
    {
        "id": 5,
        "common_name": "Red Panda",
        "scientific_name": "Ailurus fulgens",
        "category": "Wildlife & Mammals",
        "regions": ["Asia"],
        "conservation_status": "EN",
        "carbon_impact": "Forest Ecosystem Health Indicator",
        "ecological_role": "Seed dispersal and canopy ecosystem regulator in high-altitude forests.",
        "environmental_facts": [
            "Spends up to 13 hours daily feeding on bamboo leaves and shoots.",
            "Serves as an umbrella species for Eastern Himalayan broadleaf forests.",
        ],
        "threats": "Forest clearance, poaching, and habitat fragmentation.",
        "protection_tip": "Support community-based bamboo forest conservation programs.",
    },
    {
        "id": 6,
        "common_name": "Red Maple Tree",
        "scientific_name": "Acer rubrum",
        "category": "Flora & Trees",
        "regions": ["North America"],
        "conservation_status": "LC",
        "carbon_impact": "High (Sequesters ~20kg CO2/year)",
        "ecological_role": "Provides shade, urban heat island reduction, and nesting canopy.",
        "environmental_facts": [
            "Highly adaptable tree species capable of thriving in varied soils.",
            "Absorbs air pollutants like ozone and nitrogen dioxide in urban areas.",
        ],
        "threats": "Urban development and invasive insect pests.",
        "protection_tip": "Maintain urban tree canopy coverage in local neighborhoods.",
    },
]


def get_all_species() -> List[Dict[str, Any]]:
    """Return complete species database."""
    return SPECIES_DATABASE


def search_species(
    query: str = "", region: str = "All", category: str = "All", status: str = "All"
) -> List[Dict[str, Any]]:
    """
    Search and filter local biodiversity species based on search query and criteria.
    """
    results = []
    q = query.lower().strip()
    
    for sp in SPECIES_DATABASE:
        # Keyword query match
        if q:
            text = f"{sp['common_name']} {sp['scientific_name']} {sp['ecological_role']} {' '.join(sp['environmental_facts'])}".lower()
            if q not in text:
                continue
                
        # Region filter
        if region != "All" and region not in sp["regions"]:
            continue
            
        # Category filter
        if category != "All" and sp["category"] != category:
            continue
            
        # Status filter
        if status != "All" and sp["conservation_status"] != status:
            continue
            
        results.append(sp)
        
    return results


def get_conservation_stats(species_list: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate counts of species by conservation status code."""
    stats = {"LC": 0, "NT": 0, "VU": 0, "EN": 0, "CR": 0}
    for sp in species_list:
        st_code = sp.get("conservation_status", "LC")
        if st_code in stats:
            stats[st_code] += 1
    return stats


def render_biodiversity_explorer() -> None:
    """
    Render Streamlit UI for Local Biodiversity Explorer.
    """
    st.title("🌿 Local Biodiversity Explorer")
    st.markdown(
        "Discover native trees, birds, pollinators, and wildlife in your region. "
        "Learn about their conservation status, ecological roles, and environmental impact."
    )
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    with col1:
        region_filter = st.selectbox("Select Region", ["All", "North America", "Europe", "Asia", "Global Urban"])
    with col2:
        category_filter = st.selectbox("Species Category", ["All", "Flora & Trees", "Birds & Avian", "Wildlife & Mammals", "Pollinators & Insects"])
    with col3:
        status_filter = st.selectbox("Conservation Status", ["All", "LC", "NT", "VU", "EN", "CR"])
        
    search_query = st.text_input("🔍 Search species by name or ecological role...", placeholder="e.g. Oak, Pollinator, Falcon, Carbon...")
    
    filtered_species = search_species(
        query=search_query, region=region_filter, category=category_filter, status=status_filter
    )
    
    # Statistics Summary
    st.subheader("📊 Biodiversity Overview")
    stats = get_conservation_stats(filtered_species)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Species Found", len(filtered_species))
    s2.metric("Least Concern 🟢", stats["LC"])
    s3.metric("Near Threatened / Vulnerable 🟡", stats["NT"] + stats["VU"])
    s4.metric("Endangered / Critical 🔴", stats["EN"] + stats["CR"])
    
    st.divider()
    
    if not filtered_species:
        st.warning("No species matched your search filters. Try resetting search parameters.")
        return
        
    # Species Cards
    st.subheader(f"🌲 Native Species Directory ({len(filtered_species)})")
    
    for sp in filtered_species:
        st_info = CONSERVATION_STATUS_MAP.get(sp["conservation_status"], {"label": "Unknown", "color": "⚪"})
        
        with st.expander(f"{sp['common_name']} ({sp['scientific_name']}) — {st_info['color']} {st_info['label']}", expanded=True):
            c_left, c_right = st.columns([2, 1])
            with c_left:
                st.markdown(f"**Category:** `{sp['category']}` | **Regions:** `{', '.join(sp['regions'])}`")
                st.markdown(f"**Ecological Role:** {sp['ecological_role']}")
                st.markdown(f"**Environmental Impact:** `{sp['carbon_impact']}`")
                
                st.markdown("**🌱 Environmental Facts:**")
                for fact in sp["environmental_facts"]:
                    st.markdown(f"- {fact}")
            with c_right:
                st.info(f"**Threats:**\n{sp['threats']}")
                st.success(f"**Protection Action:**\n{sp['protection_tip']}")

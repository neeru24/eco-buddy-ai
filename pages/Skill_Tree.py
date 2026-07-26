import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

from skill_tree_data import SKILL_TREE_NODES
from gamification import (
    evaluate_skill_tree,
    complete_skill_node,
    initialize_skill_tree_status,
)
from database import get_total_xp

from styles.theme import apply_theme

apply_theme()

st.markdown(
    "<div class='section-header'>🌳 Eco-Action Roadmap</div>",
    unsafe_allow_html=True,
)
st.write(
    "Progress through the skill tree to unlock advanced sustainability "
    "practices and earn big rewards!"
)

USER_ID = 1

# Evaluate current progress and initialize missing node statuses consistently.
node_status_map = initialize_skill_tree_status(
    evaluate_skill_tree(USER_ID)
)


def get_node_color(status):
    if status == "Completed":
        return "#4CAF50"  # Green
    elif status == "In Progress":
        return "#2196F3"  # Blue
    elif status == "Unlocked":
        return "#FFC107"  # Yellow
    else:  # Locked
        return "#9E9E9E"  # Gray


nodes = []
edges = []

for node_id, node_data in SKILL_TREE_NODES.items():
    status = node_status_map[node_id]

    nodes.append(
        Node(
            id=node_id,
            label=f"{node_data['label']}\n({status})",
            size=25,
            color=get_node_color(status),
            title=node_data["description"],
        )
    )

    for prereq_id in node_data.get("prerequisites", []):
        edges.append(
            Edge(
                source=prereq_id,
                target=node_id,
                color="#757575",
                type="CURVE_SMOOTH",
            )
        )

config = Config(
    width=800,
    height=600,
    directed=True,
    physics=True,
    hierarchical=True,
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A6",
    collapsible=False,
    direction="UD",  # Up to down
)

col1, col2 = st.columns([2, 1])

with col1:
    return_value = agraph(
        nodes=nodes,
        edges=edges,
        config=config,
    )

with col2:
    if return_value:
        selected_node = SKILL_TREE_NODES.get(return_value)

        if selected_node:
            st.markdown(f"### {selected_node['label']}")
            st.markdown(f"**Reward:** {selected_node['xp_reward']} XP")

            status = node_status_map.get(return_value, "Locked")
            st.markdown(f"**Status:** {status}")

            st.markdown("---")
            st.markdown(selected_node["content"])

            if status == "Unlocked":
                if st.button("Mark as Completed", type="primary"):
                    success = complete_skill_node(USER_ID, return_value)

                    if success:
                        st.success(
                            f"Completed! You earned "
                            f"{selected_node['xp_reward']} XP."
                        )
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(
                            "Could not complete the action. Please try again."
                        )

            elif status == "Locked":
                st.warning(
                    "You must complete the prerequisite actions "
                    "before unlocking this node."
                )
    else:
        st.info(
            "Click on a node in the roadmap to view details "
            "and update your progress."
        )

st.markdown("---")

total_xp = get_total_xp(USER_ID)
st.metric("Total XP", f"{total_xp} XP")
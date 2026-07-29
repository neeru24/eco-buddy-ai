import logging

import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

from skill_tree_data import SKILL_TREE_NODES
from gamification import evaluate_skill_tree, complete_skill_node
from database import get_total_xp

from styles.theme import apply_theme
apply_theme()

logger = logging.getLogger(__name__)

def load_skill_tree(user_id):
    try:
        return evaluate_skill_tree(user_id)
    except Exception:
        logger.exception("Failed to evaluate skill tree for user %s", user_id)
        st.error(
            "Unable to load your skill tree progress at the moment. "
            "Displaying default progress."
        )
        return {}


def load_total_xp(user_id):
    try:
        return get_total_xp(user_id)
    except Exception:
        logger.exception("Failed to retrieve total XP for user %s", user_id)
        st.warning("XP information is currently unavailable.")
        return 0
st.markdown(
    "<div class='section-header'>🌳 Eco-Action Roadmap</div>",
    unsafe_allow_html=True,
)
st.write(
    "Progress through the skill tree to unlock advanced sustainability practices and earn big rewards!"
)

USER_ID = 1

# Safely load skill tree progress
try:
    node_status_map = load_skill_tree(USER_ID)
except Exception:
    logger.exception("Failed to evaluate skill tree for user %s", USER_ID)
    st.error(
        "Unable to load your skill tree progress at the moment. "
        "Displaying default progress."
    )
    node_status_map = {}

# Initialize default status if no data exists
if not node_status_map:
    node_status_map = {}
    for n_id, n_data in SKILL_TREE_NODES.items():
        if not n_data.get("prerequisites"):
            node_status_map[n_id] = "Unlocked"
        else:
            node_status_map[n_id] = "Locked"


def get_node_color(status):
    if status == "Completed":
        return "#4CAF50"
    elif status == "In Progress":
        return "#2196F3"
    elif status == "Unlocked":
        return "#FFC107"
    else:
        return "#9E9E9E"


nodes = []
edges = []

for node_id, node_data in SKILL_TREE_NODES.items():
    status = node_status_map.get(node_id, "Locked")

    if status == "Locked" and not node_data.get("prerequisites"):
        status = "Unlocked"
        node_status_map[node_id] = status

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
    direction="UD",
)

col1, col2 = st.columns([2, 1])

with col1:
    return_value = agraph(nodes=nodes, edges=edges, config=config)

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
                    try:
                        success = complete_skill_node(USER_ID, return_value)

                        if success:
                            st.success(
                                f"Completed! You earned {selected_node['xp_reward']} XP."
                            )
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(
                                "Could not complete the action. Please try again."
                            )

                    except Exception:
                        logger.exception(
                            "Failed to complete skill node %s", return_value
                        )
                        st.error(
                            "An unexpected error occurred while completing the skill."
                        )

            elif status == "Locked":
                st.warning(
                    "You must complete the prerequisite actions before unlocking this node."
                )

    else:
        st.info(
            "Click on a node in the roadmap to view details and update your progress."
        )

st.markdown("---")

# Safely load total XP
try:
    total_xp = load_total_xp(USER_ID)
except Exception:
    logger.exception("Failed to retrieve total XP for user %s", USER_ID)
    st.warning("XP information is currently unavailable.")
    total_xp = 0

st.metric("Total XP", f"{total_xp} XP")
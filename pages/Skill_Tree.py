import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

from skill_tree_data import SKILL_TREE_NODES
from gamification import evaluate_skill_tree, complete_skill_node
from database import get_total_xp
from styles.theme import apply_theme

apply_theme()


st.markdown("<div class='section-header'>🌳 Eco-Action Roadmap</div>", unsafe_allow_html=True)
st.write(
    "Progress through the skill tree to unlock advanced sustainability practices and earn big rewards!"
)

st.markdown(
    "<div class='section-header'>🌳 Eco-Action Roadmap</div>",
    unsafe_allow_html=True,
)
st.write(
    "Progress through the skill tree to unlock advanced sustainability "
    "practices and earn big rewards!"
)

# Retrieve the currently authenticated user instead of using a hardcoded ID.
user_id = st.session_state.get("user_id")

if user_id is None:
    st.warning("Please log in to access your skill tree.")
    st.stop()


# First evaluate current state (unlock nodes if prerequisites are met)
node_status_map = evaluate_skill_tree(user_id)

if not node_status_map:
    # If the user has never interacted, evaluate will return an empty dict,
    # but we should at least unlock the ones with no prerequisites.
    node_status_map = {}

    for n_id, n_data in SKILL_TREE_NODES.items():
        if not n_data.get("prerequisites"):
            node_status_map[n_id] = "Unlocked"
        else:
            node_status_map[n_id] = "Locked"


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

# Collect all valid node IDs for prerequisite validation
valid_node_ids = set(SKILL_TREE_NODES.keys())

# Track invalid prerequisite references
invalid_prerequisites = []

for node_id, node_data in SKILL_TREE_NODES.items():
    status = node_status_map.get(node_id, "Locked")


    # For nodes with no prerequisites, if they are not in DB, they are Unlocked

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

    # Validate prerequisite references
    for prereq_id in node_data.get("prerequisites", []):
        if prereq_id not in valid_node_ids:
            invalid_prerequisites.append((node_id, prereq_id))
            continue

        edges.append(
            Edge(
                source=prereq_id,
                target=node_id,
                color="#757575",
                type="CURVE_SMOOTH",
            )
        )

# Display warnings for invalid prerequisite references
if invalid_prerequisites:
    for node_id, prereq_id in invalid_prerequisites:
        st.warning(
            f"Skill node '{node_id}' has an invalid prerequisite '{prereq_id}'. "
            "The invalid relationship has been ignored."
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
                    success = complete_skill_node(user_id, return_value)

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

total_xp = get_total_xp(user_id)

st.metric("Total XP", f"{total_xp} XP")
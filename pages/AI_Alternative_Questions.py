import streamlit as st


# Lazy import - only load when user interacts
def get_engine():
    from alternative_question_engine import AlternativeQuestionEngine
    return AlternativeQuestionEngine()

if "seen_question_ids" not in st.session_state:
    st.session_state.seen_question_ids = set()

st.set_page_config(
    page_title="AI Alternative Question Recommendations",
    page_icon="🤖",
    layout="wide",
)


QUESTION_BANK = [
    {
        "id": "python-001",
        "question": "What is Python?",
        "concept": "Python Basics",
        "topic": "Python Basics",
        "company": "General",
        "difficulty": "Easy",
    },
    {
        "id": "python-002",
        "question": "Why is Python popular?",
        "concept": "Python Basics",
        "topic": "Python Basics",
        "company": "Google",
        "difficulty": "Easy",
    },
    {
        "id": "python-003",
        "question": "What are the main features of Python?",
        "concept": "Python Basics",
        "topic": "Python Basics",
        "company": "Microsoft",
        "difficulty": "Easy",
    },
    {
        "id": "python-004",
        "question": "What is a variable in Python?",
        "concept": "Python Basics",
        "topic": "Python Basics",
        "company": "Amazon",
        "difficulty": "Easy",
    },
    {
        "id": "python-005",
        "question": "What are Python data types?",
        "concept": "Python Data Types",
        "topic": "Python Data Types",
        "company": "Google",
        "difficulty": "Easy",
    },
    {
        "id": "python-006",
        "question": "What is a list in Python?",
        "concept": "Python Data Structures",
        "topic": "Python Data Structures",
        "company": "Amazon",
        "difficulty": "Easy",
    },
    {
        "id": "python-007",
        "question": "What is a tuple in Python?",
        "concept": "Python Data Structures",
        "topic": "Python Data Structures",
        "company": "Microsoft",
        "difficulty": "Easy",
    },
    {
        "id": "python-008",
        "question": "What is a dictionary in Python?",
        "concept": "Python Data Structures",
        "topic": "Python Data Structures",
        "company": "Google",
        "difficulty": "Medium",
    },
    {
        "id": "python-009",
        "question": "What is inheritance in Python?",
        "concept": "Python OOP",
        "topic": "Python OOP",
        "company": "Amazon",
        "difficulty": "Medium",
    },
    {
        "id": "python-010",
        "question": "Explain method overriding in Python.",
        "concept": "Python OOP",
        "topic": "Python OOP",
        "company": "Microsoft",
        "difficulty": "Medium",
    },
    {
        "id": "python-011",
        "question": "What is polymorphism in Python?",
        "concept": "Python OOP",
        "topic": "Python OOP",
        "company": "Google",
        "difficulty": "Medium",
    },
    {
        "id": "python-012",
        "question": "What are Python functions?",
        "concept": "Python Functions",
        "topic": "Python Functions",
        "company": "Amazon",
        "difficulty": "Easy",
    },
    {
        "id": "python-013",
        "question": "What is exception handling in Python?",
        "concept": "Python Exception Handling",
        "topic": "Python Exception Handling",
        "company": "Microsoft",
        "difficulty": "Medium",
    },
    {
        "id": "python-014",
        "question": "How do you handle exceptions in Python?",
        "concept": "Python Exception Handling",
        "topic": "Python Exception Handling",
        "company": "Google",
        "difficulty": "Medium",
    },
]


st.title("🤖 AI Alternative Question Recommendation Engine")
if st.button("🔄 Reset seen questions"):
    st.session_state.seen_question_ids.clear()
    st.success("Seen-question history has been reset.")

st.write(
    "Enter an interview question to generate alternative "
    "questions covering the same concept."
)

col1, col2, col3 = st.columns(3)

with col1:
    selected_company = st.selectbox(
        "Company",
        [
            "Any",
            "Google",
            "Microsoft",
            "Amazon",
        ],
    )

with col2:
    selected_topic = st.selectbox(
        "Topic",
        [
            "Any",
            "Python Basics",
            "Python Data Types",
            "Python Data Structures",
            "Python OOP",
            "Python Functions",
            "Python Exception Handling",
        ],
    )

with col3:
    selected_difficulty = st.selectbox(
        "Difficulty",
        [
            "Any",
            "Easy",
            "Medium",
        ],
    )


question = st.text_area(
    "Enter your interview question",
    height=150,
    placeholder=(
        "Example:\n"
        "What is inheritance in Python?"
    ),
)


if st.button(
    "🔍 Generate Alternatives",
    type="primary",
):

    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    with st.spinner(
        "🤖 Loading AI model and generating alternatives..."
    ):

        engine = get_engine()

        recommendations = engine.recommend(
    question=question,
    question_bank=QUESTION_BANK,
    top_k=5,
    min_similarity=0.45,
    seen_question_ids=st.session_state.seen_question_ids,
    company=(
        None
        if selected_company == "Any"
        else selected_company
    ),
    topic=(
        None
        if selected_topic == "Any"
        else selected_topic
    ),
    difficulty=(
        None
        if selected_difficulty == "Any"
        else selected_difficulty
    ),
)

    st.subheader("💡 Alternative Questions")

    if not recommendations:

        st.info(
            "No sufficiently similar alternative questions "
            "were found."
        )

    else:

        for index, recommendation in enumerate(
            recommendations,
            start=1,
        ):

            similarity = recommendation["similarity"] * 100

            st.markdown(
                f"### {index}. "
                f"{recommendation['question']}"
            )


    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(
            f"**Topic:** "
            f"{recommendation['topic']}"
        )

    with col2:
        st.write(
            f"**Difficulty:** "
            f"{recommendation['difficulty']}"
        )

    with col3:
        st.write(
            f"**Company:** "
            f"{recommendation['company']}"
        )

    st.caption(
        f"Semantic similarity: "
        f"{similarity:.1f}%"
    )

    st.divider()
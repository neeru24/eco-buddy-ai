import re
import streamlit as st


st.set_page_config(
    page_title="AI Concept Coverage Analyzer",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 AI Concept Coverage Analyzer")

st.write(
    "Analyze a set of interview questions to identify covered "
    "concepts, weak areas, and missing concepts."
)


# ---------------------------------------------------------
# Concept Knowledge Base
# ---------------------------------------------------------

CONCEPTS = {
    "Python Basics": [
        "python",
        "python language",
        "programming language",
        "syntax",
        "variables",
        "data types",
    ],
    "Python Data Structures": [
        "list",
        "tuple",
        "set",
        "dictionary",
        "dict",
        "data structure",
    ],
    "Python Functions": [
        "function",
        "functions",
        "lambda",
        "argument",
        "parameters",
        "return",
    ],
    "Python OOP": [
        "class",
        "object",
        "inheritance",
        "polymorphism",
        "encapsulation",
        "abstraction",
        "oop",
        "object oriented",
    ],
    "Python Exception Handling": [
        "exception",
        "exceptions",
        "try",
        "except",
        "finally",
        "error handling",
    ],
    "Python File Handling": [
        "file handling",
        "file",
        "open",
        "read file",
        "write file",
        "csv",
    ],
    "SQL": [
        "sql",
        "query",
        "select",
        "insert",
        "update",
        "delete",
        "sql joins",
        "join",
    ],
    "Database": [
        "database",
        "normalization",
        "normal forms",
        "primary key",
        "foreign key",
        "index",
        "transaction",
    ],
    "Machine Learning": [
        "machine learning",
        "model",
        "training",
        "prediction",
        "classification",
        "regression",
    ],
    "Machine Learning Evaluation": [
        "overfitting",
        "underfitting",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "confusion matrix",
        "cross validation",
    ],
    "Data Preprocessing": [
        "data preprocessing",
        "missing values",
        "normalization",
        "standardization",
        "feature scaling",
        "encoding",
    ],
}


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def normalize_text(text):
    """Normalize text for keyword matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_concepts(questions):
    """
    Detect concepts covered by the supplied questions.

    Returns:
        concept_matches:
            Dictionary containing matching questions for each concept.
    """

    concept_matches = {}

    normalized_questions = [
        normalize_text(question)
        for question in questions
    ]

    for concept, keywords in CONCEPTS.items():

        matched_questions = []

        for index, question in enumerate(normalized_questions):

            matched = False

            for keyword in keywords:

                normalized_keyword = normalize_text(keyword)

                if normalized_keyword in question:
                    matched = True
                    break

            if matched:
                matched_questions.append(index)

        if matched_questions:
            concept_matches[concept] = matched_questions

    return concept_matches


def get_coverage_level(question_count):
    """Classify concept coverage based on related question count."""

    if question_count >= 2:
        return "Covered"

    if question_count == 1:
        return "Weak"

    return "Missing"


# ---------------------------------------------------------
# Input
# ---------------------------------------------------------

questions_text = st.text_area(
    "Enter your interview questions",
    height=250,
    placeholder="""Example:

1. What is a Python list?
2. Explain inheritance in Python.
3. What is database normalization?
4. Explain SQL joins.
5. What is overfitting in machine learning?""",
)


# ---------------------------------------------------------
# Analyze
# ---------------------------------------------------------

if st.button(
    "🔍 Analyze Concept Coverage",
    type="primary",
):

    if not questions_text.strip():
        st.warning("Please enter at least one question.")
        st.stop()

    questions = [
        q.strip()
        for q in questions_text.splitlines()
        if q.strip()
    ]

    # -----------------------------------------------------
    # Questions Analyzed
    # -----------------------------------------------------

    st.subheader("📋 Questions Analyzed")

    for index, question in enumerate(
        questions,
        start=1,
    ):
        st.write(
            f"**{index}.** {question}"
        )

    st.success(
        f"Successfully loaded {len(questions)} question(s)."
    )

    # -----------------------------------------------------
    # Detect Concepts
    # -----------------------------------------------------

    concept_matches = detect_concepts(questions)

    total_concepts = len(CONCEPTS)

    covered_concepts = []
    weak_concepts = []
    missing_concepts = []

    for concept in CONCEPTS:

        question_count = len(
            concept_matches.get(
                concept,
                [],
            )
        )

        level = get_coverage_level(
            question_count
        )

        if level == "Covered":
            covered_concepts.append(
                (concept, question_count)
            )

        elif level == "Weak":
            weak_concepts.append(
                (concept, question_count)
            )

        else:
            missing_concepts.append(
                concept
            )

    # -----------------------------------------------------
    # Coverage Score
    # -----------------------------------------------------

    covered_count = len(covered_concepts)

    coverage_score = (
        covered_count / total_concepts
    ) * 100

    st.divider()

    st.subheader("📊 Concept Coverage Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Coverage Score",
            f"{coverage_score:.0f}%",
        )

    with col2:
        st.metric(
            "Covered Concepts",
            len(covered_concepts),
        )

    with col3:
        st.metric(
            "Weak Areas",
            len(weak_concepts),
        )

    with col4:
        st.metric(
            "Missing Concepts",
            len(missing_concepts),
        )

    st.progress(
        min(coverage_score / 100, 1.0)
    )

    # -----------------------------------------------------
    # Covered Concepts
    # -----------------------------------------------------

    st.subheader("✅ Covered Concepts")

    if covered_concepts:

        for concept, count in covered_concepts:

            st.success(
                f"**{concept}** — "
                f"{count} related question(s)"
            )

    else:

        st.info(
            "No concepts have strong coverage yet."
        )

    # -----------------------------------------------------
    # Weak Areas
    # -----------------------------------------------------

    st.subheader("⚠️ Weak Areas")

    if weak_concepts:

        for concept, count in weak_concepts:

            st.warning(
                f"**{concept}** — "
                f"only {count} related question(s)"
            )

    else:

        st.info(
            "No weak areas detected."
        )

    # -----------------------------------------------------
    # Missing Concepts
    # -----------------------------------------------------

    st.subheader("❌ Missing Concepts")

    if missing_concepts:

        for concept in missing_concepts:

            st.error(
                f"**{concept}** — "
                "No related interview question detected."
            )

    else:

        st.success(
            "All tracked concepts are represented."
        )

    # -----------------------------------------------------
    # Detailed Concept Analysis
    # -----------------------------------------------------

    st.subheader("🔎 Detailed Concept Analysis")

    for concept in CONCEPTS:

        question_indexes = concept_matches.get(
            concept,
            [],
        )

        question_count = len(
            question_indexes
        )

        if question_count >= 2:
            status = "🟢 Covered"

        elif question_count == 1:
            status = "🟡 Weak"

        else:
            status = "🔴 Missing"

        with st.expander(
            f"{status} — {concept}"
        ):

            if question_indexes:

                st.write(
                    "Related questions:"
                )

                for question_index in question_indexes:

                    st.write(
                        f"- {questions[question_index]}"
                    )

            else:

                st.write(
                    "No related questions were detected."
                )

    # -----------------------------------------------------
    # Recommendations
    # -----------------------------------------------------

    st.subheader("💡 Recommendations")

    if missing_concepts:

        st.write(
            "Consider adding interview questions "
            "covering these missing concepts:"
        )

        for concept in missing_concepts[:5]:

            st.write(
                f"- **{concept}**"
            )

    elif weak_concepts:

        st.write(
            "Your question set covers the main concepts, "
            "but some areas need more practice:"
        )

        for concept, count in weak_concepts:

            st.write(
                f"- **{concept}** "
                f"({count} question(s))"
            )

    else:

        st.success(
            "🎉 Your question set provides strong "
            "coverage across the tracked concepts!"
        )
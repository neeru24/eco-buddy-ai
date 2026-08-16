from typing import List, Dict, Tuple

class AlternativeQuestionEngine:
    """Generate semantically similar and diverse interview questions."""

    def __init__(self):
     self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def recommend(
        self,
        question,
        question_bank,
        top_k=5,
        min_similarity=0.45,
    ):
        """Return the most semantically similar questions."""

        if not question or not question.strip():
            return []

        if not question_bank:
            return []

        query = question.strip()

        if seen_question_ids is None:
            seen_question_ids = set()

        candidates = []

        for item in question_bank:
            candidate = item.get("question", "").strip()
            if not candidate:
                continue

            if candidate.lower() == query.lower():
                continue

            candidates.append(item)

        if not candidates:
            return []

        candidate_questions = [item["question"] for item in candidates]

        # Ensure model is loaded lazily
        if self.model is None:
            self.model = self.get_model()

        # Lazy import/use util from class var (set in get_model)
        util = getattr(self.__class__, "_util", None)
        if util is None:
            # fallback: import util locally if not present
            from sentence_transformers import util as util

        # Cache candidate embeddings keyed by the tuple of questions
        cache_key: Tuple[str, ...] = tuple(candidate_questions)
        if cache_key not in self.__class__._embedding_cache:
            embeddings = self.model.encode(
                candidate_questions,
                convert_to_tensor=True,
                normalize_embeddings=True,
            )
            self.__class__._embedding_cache[cache_key] = embeddings

        candidate_embeddings = self.__class__._embedding_cache[cache_key]

        query_embedding = self.model.encode(
            query,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )

        similarity_scores = util.cos_sim(
            query_embedding,
            candidate_embeddings,
        )[0]

        recommendations = []
        for item, score in zip(candidates, similarity_scores):
            similarity = float(score)

            if similarity >= min_similarity:
                recommendations.append(
                    {
                        "question": item["question"],
                        "concept": item.get("concept", "General"),
                        "similarity": similarity,
                    }
                )

        recommendations.sort(
            key=lambda item: item["similarity"],
            reverse=True,
        )

        return recommendations[:top_k]
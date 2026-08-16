import streamlit as st
from collections import Counter
from typing import Any
from cache import cached
from cache_config import TTL_COMPUTED_ANALYTICS, CACHE_CATEGORY_COMPUTED
from database import get_all_assessments
from emissions import calculate_footprint
from recommendations import generate_recommendations


def calculate_platform_stats(
    assessments: list[dict[str, Any]] | list[tuple[Any, ...]],
) -> dict[str, Any]:
    """
    Computes anonymized platform statistics from assessment records.

    Args:
        assessments (list): List of assessment tuples or dictionaries.

    Returns:
        dict: Anonymized platform metrics (total_assessments, average_eco_score,
              active_users, popular_recommendations, recommendation_breakdown).
    """
    if not assessments:
        return {
            "total_assessments": 0,
            "average_eco_score": 0.0,
            "active_users": 0,
            "popular_recommendations": [],
            "recommendation_breakdown": [],
        }

    total_assessments = len(assessments)
    eco_scores = []
    user_ids = set()
    rec_counter = Counter()
    rec_scores = {}

    for row in assessments:
        if isinstance(row, dict):
            u_id = row.get("user_id")
            t = row.get("transport", "Car")
            d = row.get("distance", 0.0)
            e = row.get("electricity", 0.0)
            diet_val = row.get("diet", "Vegetarian")
            f = row.get("flights", 0)
            score = row.get("eco_score", 0)
        else:
            # Tuple: (id, user_id, date, transport, distance, electricity, diet, flights, footprint, eco_score)
            u_id = row[1] if len(row) > 1 else 1
            t = row[3] if len(row) > 3 else "Car"
            d = row[4] if len(row) > 4 else 0.0
            e = row[5] if len(row) > 5 else 0.0
            diet_val = row[6] if len(row) > 6 else "Vegetarian"
            f = row[7] if len(row) > 7 else 0
            score = row[9] if len(row) > 9 else 0

        if u_id is not None:
            user_ids.add(u_id)
        if score is not None:
            eco_scores.append(score)

        # Derive recommendations for aggregation
        try:
            _, contributors = calculate_footprint(t, d, e, diet_val, f)
            _, recs = generate_recommendations(t, e, diet_val, f, contributors)
            for r in recs:
                if not r.startswith("🎯 Priority Focus:") and not r.startswith("🌱 Excellent!"):
                    rec_counter[r] += 1
                    if r not in rec_scores:
                        rec_scores[r] = []
                    if score is not None:
                        rec_scores[r].append(score)
        except Exception as err:
            print(f"Error deriving recommendations for admin stats: {err}")

    average_eco_score = round(sum(eco_scores) / len(eco_scores), 1) if eco_scores else 0.0
    active_users = len(user_ids)
    popular_recommendations = rec_counter.most_common()

    # Build complementary analytical breakdown
    recommendation_breakdown = []
    for r, count in popular_recommendations:
        r_lower = r.lower()
        if any(icon in r for icon in ["🚗", "🚌", "🚴", "🚶"]) or "transport" in r_lower:
            domain = "🚗 Transport"
        elif any(icon in r for icon in ["💡", "🔌", "⚡"]) or "electricity" in r_lower:
            domain = "⚡ Electricity"
        elif any(icon in r for icon in ["🥗", "🥩", "🥬"]) or "meat" in r_lower or "plant" in r_lower:
            domain = "🥩 Diet"
        elif any(icon in r for icon in ["✈️", "🛫", "🌍", "🌎"]) or "flight" in r_lower or "air travel" in r_lower:
            domain = "✈️ Flights"
        else:
            domain = "🌿 Lifestyle"

        scores_list = rec_scores.get(r, [])
        target_avg_score = round(sum(scores_list) / len(scores_list), 1) if scores_list else 0.0
        trigger_rate = round((count / total_assessments) * 100, 1)

        recommendation_breakdown.append({
            "domain": domain,
            "recommendation": r,
            "count": count,
            "trigger_rate": trigger_rate,
            "target_avg_score": target_avg_score
        })

    return {
        "total_assessments": total_assessments,
        "average_eco_score": average_eco_score,
        "active_users": active_users,
        "popular_recommendations": popular_recommendations,
        "recommendation_breakdown": recommendation_breakdown,
    }


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def get_admin_platform_stats() -> dict[str, Any]:
    """
    Queries all assessments and returns aggregated platform statistics.
    """
    assessments = get_all_assessments()
    return calculate_platform_stats(assessments)

"""Future Self Sustainability Report — predicts long-term environmental impact."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from database import get_assessments
from emissions import calculate_footprint, calculate_eco_score

logger = logging.getLogger(__name__)


@dataclass
class FutureScenario:
    annual_footprint: float
    contributors: dict[str, float]
    cumulative_emissions: float
    eco_score: int


@dataclass
class FutureSelfReport:
    current_footprint: float
    current_contributors: dict[str, float]
    current_eco_score: int
    latest_date: str
    scenarios: dict[int, FutureScenario]
    trend_slope: float
    history_df: Optional[pd.DataFrame]
    num_assessments: int


def get_assessment_history_df(user_id: int) -> Optional[pd.DataFrame]:
    history = get_assessments(user_id)
    if not history:
        return None
    df = pd.DataFrame(
        history,
        columns=[
            "id", "date", "transport", "distance",
            "electricity", "diet", "flights", "footprint", "eco_score",
        ],
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def compute_trend_slope(history_df: pd.DataFrame) -> float:
    if len(history_df) < 2:
        return 0.0
    x = np.arange(len(history_df))
    y = history_df["footprint"].values
    slope = np.polyfit(x, y, 1)[0]
    return slope


def project_footprint(current: float, slope: float, years_ahead: int) -> float:
    projected = current + slope * years_ahead
    return max(projected, 0.0)


def generate_future_self_report(user_id: int) -> Optional[FutureSelfReport]:
    df = get_assessment_history_df(user_id)
    if df is None or df.empty:
        return None

    latest = df.iloc[-1]
    current_fp = float(latest["footprint"])
    latest_date = str(latest["date"])
    current_eco = int(latest["eco_score"])

    _, current_contributors = calculate_footprint(
        latest["transport"],
        float(latest["distance"]),
        float(latest["electricity"]),
        latest["diet"],
        int(latest["flights"]),
    )

    slope = compute_trend_slope(df)

    scenarios: dict[int, FutureScenario] = {}
    for year in (1, 5, 10):
        projected_fp = project_footprint(current_fp, slope, year)
        scale = projected_fp / current_fp if current_fp > 0 else 1.0
        projected_contributors = {
            k: round(v * scale, 2) for k, v in current_contributors.items()
        }
        projected_score = calculate_eco_score(projected_fp, projected_contributors)

        scenarios[year] = FutureScenario(
            annual_footprint=round(projected_fp, 2),
            contributors=projected_contributors,
            cumulative_emissions=round(projected_fp * year, 2),
            eco_score=projected_score,
        )

    return FutureSelfReport(
        current_footprint=current_fp,
        current_contributors=current_contributors,
        current_eco_score=current_eco,
        latest_date=latest_date,
        scenarios=scenarios,
        trend_slope=slope,
        history_df=df,
        num_assessments=len(df),
    )


def build_projection_timeline(
    report: FutureSelfReport,
) -> pd.DataFrame:
    rows = []
    if report.history_df is not None:
        for _, row in report.history_df.iterrows():
            rows.append({
                "label": row["date"].strftime("%b %Y"),
                "value": float(row["footprint"]),
                "type": "Historical",
            })
    for year in (1, 5, 10):
        scenario = report.scenarios[year]
        label = f"Year {year}"
        rows.append({
            "label": label,
            "value": scenario.annual_footprint,
            "type": "Projected",
        })
    return pd.DataFrame(rows)

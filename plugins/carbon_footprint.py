"""
Carbon Footprint Calculator Plugin
"""

from plugins.base import CalculatorPlugin, InputField, CalcResult
from emissions import calculate_footprint, calculate_eco_score, generate_full_audit_log
from recommendations import generate_recommendations
from config import DIET_TYPES, TRANSPORT_EMISSION_FACTORS, VALID_REGIONS
from typing import Any


class CarbonFootprintPlugin(CalculatorPlugin):

    @property
    def name(self) -> str:
        return "carbon_footprint"

    @property
    def description(self) -> str:
        return "Estimate your annual carbon footprint from transport, electricity, diet, and flights."

    @property
    def category(self) -> str:
        return "Emissions"

    def get_input_fields(self) -> list[InputField]:
        return [
            InputField(
                name="transport",
                label="Primary Transport Mode",
                type="select",
                default="Car",
                options=tuple(sorted(TRANSPORT_EMISSION_FACTORS.keys())),
            ),
            InputField(
                name="distance",
                label="Daily Commute Distance (km)",
                type="number",
                default=20.0,
                min_val=0.0,
                max_val=500.0,
            ),
            InputField(
                name="electricity",
                label="Monthly Electricity Usage (kWh)",
                type="number",
                default=250.0,
                min_val=0.0,
                max_val=10000.0,
            ),
            InputField(
                name="diet",
                label="Diet Type",
                type="select",
                default="Vegetarian",
                options=tuple(DIET_TYPES),
            ),
            InputField(
                name="flights",
                label="Flights Per Year",
                type="number",
                default=0,
                min_val=0,
                max_val=365,
            ),
            InputField(
                name="region",
                label="Region",
                type="select",
                default="Global",
                options=tuple(sorted(VALID_REGIONS)),
            ),
        ]


    def _build_metadata(
        self,
        transport: str,
        distance: float,
        electricity: float,
        diet: str,
        flights: int,
        region: str,
        eco_score: int,
        audit_log: dict[str, Any],
    ) -> dict[str, Any]:
        """Build metadata for the calculation result."""
        return {
            "eco_score": eco_score,
            "transport": transport,
            "distance": distance,
            "electricity": electricity,
            "diet": diet,
            "flights": flights,
            "region": region,
            "audit_log": audit_log,
        }


    def calculate(self, inputs: dict) -> CalcResult:
        transport = inputs["transport"]
        distance = inputs["distance"]
        electricity = inputs["electricity"]
        diet = inputs["diet"]
        flights = inputs["flights"]
        region = inputs.get("region", "Global")

        total_kg, contributors, audit_log = calculate_footprint(
            transport=transport,
            distance=distance,
            electricity=electricity,
            diet=diet,
            flights=flights,
            region=region,

            return_audit=True,
        )

        eco_score = calculate_eco_score(total_kg, contributors)
        full_audit = generate_full_audit_log(
            transport,
            distance,
            electricity,
            diet,
            flights,
            region,
        )

        metadata = self._build_metadata(
            transport=transport,
            distance=distance,
            electricity=electricity,
            diet=diet,
            flights=flights,
            region=region,
            eco_score=eco_score,
            audit_log=full_audit,
        )

        return CalcResult(
            total=total_kg,
            unit="kg CO2/year",
            contributors=contributors,
            metadata=metadata,
        )

    def get_recommendations(self, result: CalcResult) -> list[str]:
        meta = result.metadata
        _, recs = generate_recommendations(
            transport=meta.get("transport", ""),
            electricity=meta.get("electricity", 0),
            diet=meta.get("diet", ""),
            flights=meta.get("flights", 0),
            contributors=result.contributors,
        )
        return recs


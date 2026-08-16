"""
Carbon Payback Plugin for EcoBuddy AI Calculator Plugin System.
"""

from plugins.base import CalculatorPlugin, InputField, CalcResult
from carbon_payback import calculate_carbon_payback, PRESET_ECO_PRODUCTS


class CarbonPaybackPlugin(CalculatorPlugin):

    @property
    def name(self) -> str:
        return "carbon_payback"

    @property
    def description(self) -> str:
        return "Estimates how long it takes for an eco-friendly purchase to offset its manufacturing carbon emissions."

    @property
    def category(self) -> str:
        return "Emissions"

    def get_input_fields(self) -> list[InputField]:
        return [
            InputField(
                name="embodied_carbon_kg",
                label="Manufacturing / Embodied Carbon (kg CO2)",
                type="number",
                default=12.0,
                min_val=0.1,
                max_val=50000.0,
                help_text="The carbon emitted during raw material extraction, manufacturing, and shipping."
            ),
            InputField(
                name="daily_usage",
                label="Daily Usage Intensity",
                type="number",
                default=5.0,
                min_val=0.0,
                max_val=1000.0,
                help_text="Daily hours, kilometers, or single-use items avoided."
            ),
            InputField(
                name="savings_per_unit",
                label="CO2 Savings per Unit of Usage (kg CO2)",
                type="number",
                default=0.045,
                min_val=0.0001,
                max_val=100.0,
                help_text="Operational kg CO2 saved per unit of usage."
            )
        ]

    def calculate(self, inputs: dict) -> CalcResult:
        embodied = float(inputs.get("embodied_carbon_kg", 12.0))
        usage = float(inputs.get("daily_usage", 5.0))
        savings_per_unit = float(inputs.get("savings_per_unit", 0.045))

        res = calculate_carbon_payback(
            embodied_carbon_kg=embodied,
            daily_usage=usage,
            savings_per_unit=savings_per_unit,
            usage_unit="units/day",
            product_name="Eco Purchase"
        )

        payback_months = res.get("payback_months") or 0.0

        return CalcResult(
            total=payback_months,
            unit="months",
            contributors={"Embodied Carbon": embodied, "Annual Savings": res["annual_savings_kg"]},
            metadata=res
        )

    def get_recommendations(self, result: CalcResult) -> list[str]:
        months = result.total
        annual_sav = result.metadata.get("annual_savings_kg", 0.0)
        net_5yr = result.metadata.get("net_savings_5yr_kg", 0.0)

        recs = [
            f"⏱️ Payback Period: Your purchase pays off its carbon debt in approx {months:.1f} months.",
            f"🌱 Net 5-Year Carbon Return: Over 5 years, this purchase prevents {net_5yr:,.1f} kg CO2 from entering the atmosphere.",
            f"💡 High operational savings of {annual_sav:,.1f} kg CO2/year make this a sustainable long-term choice."
        ]
        return recs

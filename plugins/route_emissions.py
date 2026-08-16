from plugins.base import CalculatorPlugin, InputField, CalcResult
from marketplace import calculate_trip_emissions, compare_transit_modes, EMISSION_FACTORS


class RouteEmissionsPlugin(CalculatorPlugin):

    @property
    def name(self) -> str:
        return "route_emissions"

    @property
    def description(self) -> str:
        return "Calculate trip emissions and compare transit modes for route planning."

    @property
    def category(self) -> str:
        return "Transport"

    def get_input_fields(self) -> list[InputField]:
        return [
            InputField(
                name="distance_km",
                label="Trip Distance (km)",
                type="number",
                default=10.0,
                min_val=0.0,
                max_val=10000.0,
            ),
            InputField(
                name="transport_mode",
                label="Transport Mode",
                type="select",
                default="Single-occupancy car",
                options=tuple(EMISSION_FACTORS.keys()),
            ),
            InputField(
                name="passengers",
                label="Number of Passengers",
                type="number",
                default=1,
                min_val=1,
                max_val=10,
            ),
        ]

    def calculate(self, inputs: dict) -> CalcResult:
        distance = inputs.get("distance_km", 0)
        mode = inputs.get("transport_mode", "Single-occupancy car")
        passengers = inputs.get("passengers", 1)

        trip_kg = calculate_trip_emissions(distance, mode, passengers)
        comparison = compare_transit_modes(distance, passengers)

        return CalcResult(
            total=trip_kg,
            unit="kg CO2e",
            contributors={mode: trip_kg},
            metadata={"comparison": comparison},
        )

    def get_recommendations(self, result: CalcResult) -> list[str]:
        recs = []
        comparison = result.metadata.get("comparison", [])
        if comparison:
            lowest = comparison[0]
            if lowest["emissions_kg"] == 0:
                recs.append(f"{lowest['mode']} produces zero emissions for this distance.")
            else:
                recs.append(
                    f"Lowest emission option: {lowest['mode']} "
                    f"({lowest['emissions_kg']} kg CO2e)."
                )
        return recs

from plugins.base import CalculatorPlugin, InputField, CalcResult
from water import calculate_water_footprint, validate_water_inputs
from recommendations import generate_water_recommendations
from config import DIET_VIRTUAL_WATER


class WaterFootprintPlugin(CalculatorPlugin):

    @property
    def name(self) -> str:
        return "water_footprint"

    @property
    def description(self) -> str:
        return "Estimate your daily water footprint including direct usage and virtual water from diet."

    @property
    def category(self) -> str:
        return "Water"

    def get_input_fields(self) -> list[InputField]:
        return [
            InputField(
                name="shower_mins_per_day",
                label="Average Shower Duration (min/day)",
                type="number",
                default=10.0,
                min_val=0.0,
                max_val=180.0,
            ),
            InputField(
                name="laundry_loads_per_week",
                label="Laundry Loads (per week)",
                type="number",
                default=2,
                min_val=0,
                max_val=50,
            ),
            InputField(
                name="dishwasher_runs_per_week",
                label="Dishwasher Runs (per week)",
                type="number",
                default=3,
                min_val=0,
                max_val=50,
            ),
            InputField(
                name="garden_mins_per_week",
                label="Garden Watering (min/week)",
                type="number",
                default=0.0,
                min_val=0.0,
                max_val=600.0,
            ),
            InputField(
                name="diet",
                label="Diet Type (Virtual Water)",
                type="select",
                default="Omnivore",
                options=tuple(sorted(DIET_VIRTUAL_WATER.keys())),
            ),
        ]

    def calculate(self, inputs: dict) -> CalcResult:
        shower = inputs.get("shower_mins_per_day", 0)
        laundry = inputs.get("laundry_loads_per_week", 0)
        dishwasher = inputs.get("dishwasher_runs_per_week", 0)
        garden = inputs.get("garden_mins_per_week", 0)
        diet = inputs.get("diet", "Omnivore")

        warnings = validate_water_inputs(
            shower_mins=shower,
            laundry_loads=laundry,
            dishwasher_runs=dishwasher,
            garden_mins=garden,
        )
        total_daily, contributors = calculate_water_footprint(
            shower_mins_per_day=shower,
            laundry_loads_per_week=laundry,
            dishwasher_runs_per_week=dishwasher,
            garden_mins_per_week=garden,
            diet=diet,
        )
        return CalcResult(
            total=round(total_daily, 2),
            unit="liters/day",
            contributors=contributors,
            metadata={"warnings": warnings},
        )

    def get_recommendations(self, result: CalcResult) -> list[str]:
        _, recs = generate_water_recommendations(
            contributors=result.contributors,
            total_daily=result.total,
            diet="",
        )
        return recs

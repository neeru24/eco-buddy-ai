from plugins.base import CalculatorPlugin, InputField, CalcResult
import energy_audit as ea


class EnergyAuditPlugin(CalculatorPlugin):

    @property
    def name(self) -> str:
        return "energy_audit"

    @property
    def description(self) -> str:
        return "Audit your home energy usage and evaluate solar installation ROI."

    @property
    def category(self) -> str:
        return "Energy"

    def get_input_fields(self) -> list[InputField]:
        return [
            InputField(
                name="appliances",
                label="Home Appliances",
                type="text",
                default=(),
                help_text=(
                    "List of appliance dicts, each with keys: "
                    "power_rating_watts, hours_used_per_day, "
                    "standby_draw_watts, quantity."
                ),
            ),
            InputField(
                name="roof_space_m2",
                label="Roof Space for Solar Panels (m\u00b2)",
                type="number",
                default=0.0,
                min_val=0.0,
                max_val=500.0,
            ),
            InputField(
                name="panel_efficiency_pct",
                label="Solar Panel Efficiency (%)",
                type="number",
                default=20.0,
                min_val=5.0,
                max_val=50.0,
            ),
            InputField(
                name="utility_rate",
                label="Utility Rate ($/kWh)",
                type="number",
                default=0.12,
                min_val=0.0,
                max_val=1.0,
            ),
        ]

    def calculate(self, inputs: dict) -> CalcResult:
        appliances = inputs.get("appliances", [])
        daily, monthly, yearly = ea.calculate_home_energy_summary(appliances)

        solar_data = {}
        roof = inputs.get("roof_space_m2", 0)
        efficiency = inputs.get("panel_efficiency_pct", 20)
        rate = inputs.get("utility_rate", 0.12)

        if roof > 0:
            system_kw = ea.calculate_solar_system_size(roof, efficiency)
            annual_gen = ea.calculate_annual_solar_generation(system_kw, 5.0)
            install_cost = ea.calculate_solar_installation_cost(system_kw, 1000)
            annual_savings = annual_gen * rate
            payback = ea.calculate_solar_payback_period(install_cost, annual_savings)
            carbon_offset = ea.calculate_solar_carbon_offset(annual_gen)
            solar_data = {
                "system_size_kw": round(system_kw, 2),
                "annual_generation_kwh": round(annual_gen, 2),
                "installation_cost": round(install_cost, 2),
                "payback_years": round(payback, 1),
                "annual_carbon_offset_kg": round(carbon_offset, 2),
            }

        return CalcResult(
            total=round(yearly, 2),
            unit="kWh/year",
            contributors={
                "Daily (kWh)": round(daily, 3),
                "Monthly (kWh)": round(monthly, 2),
                "Yearly (kWh)": round(yearly, 2),
            },
            metadata=solar_data,
        )

    def get_recommendations(self, result: CalcResult) -> list[str]:
        recs = []
        yearly = result.contributors.get("Yearly (kWh)", 0)
        if yearly > 10000:
            recs.append("Your energy usage is very high. Consider energy-efficient appliances.")
        elif yearly > 5000:
            recs.append("Moderate usage. Look for standby power reduction opportunities.")
        else:
            recs.append("Good energy efficiency. Keep it up!")
        payback = result.metadata.get("payback_years")
        if payback is not None:
            recs.append(f"Solar payback period: {payback} years.")
        return recs

"""Tests for the Investment & Pension Financed Emissions Tracker."""
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import financed_emissions
from financed_emissions import (
    COMPARISON_ACTIONS,
    DEFAULT_CURRENT_FUND,
    DEFAULT_DECARBONISATION_RATE,
    DEFAULT_PROPOSED_FUND,
    FUND_ARCHETYPES,
    INTENSITY_BASIS,
    MAX_YEARS,
    SECTOR_INTENSITIES,
    PortfolioError,
    compare_funds,
    compare_to_operational,
    concentration,
    custom_portfolio,
    delete_portfolio,
    equivalent_actions,
    financed_emissions as financed,
    fund_intensity,
    get_caveats,
    get_fund,
    get_portfolios,
    get_switch_advice,
    list_asset_classes,
    list_fund_archetypes,
    list_sectors,
    nearest_archetype,
    portfolio_emissions,
    project_switch,
    save_portfolio,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = financed_emissions.DB_NAME
    financed_emissions.DB_NAME = db_path
    yield db_path
    financed_emissions.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


# A pension of this size is unremarkable after fifteen years of contributions,
# which is rather the point of the feature.
PENSION = 120000.0


# --- Catalogue --------------------------------------------------------------


def test_fund_catalogue_is_sorted_cleanest_first():
    funds = list_fund_archetypes()
    assert funds == sorted(funds, key=lambda item: item["intensity"])
    assert funds[0]["name"] == "Green bonds"


def test_every_fund_documents_its_basis():
    for fund in list_fund_archetypes():
        assert fund["description"]
        assert fund["basis"]
        assert fund["asset_class"]
        assert fund["intensity"] > 0


def test_no_fund_is_claimed_to_be_zero_carbon():
    # Including the clean energy and green bond entries. Manufacturing emits,
    # and a catalogue with a zero in it would be making a claim it cannot support.
    assert all(fund["intensity"] > 0 for fund in list_fund_archetypes())


def test_the_default_pension_fund_is_dirtier_than_the_screened_options():
    tracker = fund_intensity("Global equity tracker")
    assert tracker > fund_intensity("ESG screened equity")
    assert tracker > fund_intensity("Fossil fuel free equity")
    assert tracker > fund_intensity("Paris aligned benchmark")


def test_an_energy_sector_fund_is_the_dirtiest_equity_option():
    equities = list_fund_archetypes(asset_class="Equity")
    assert equities[-1]["name"] == "Energy sector fund"


def test_asset_class_filter_returns_only_that_class():
    for fund in list_fund_archetypes(asset_class="Fixed income"):
        assert fund["asset_class"] == "Fixed income"


def test_asset_classes_are_listed():
    classes = list_asset_classes()
    assert "Equity" in classes
    assert "Fixed income" in classes


def test_an_unknown_fund_falls_back_rather_than_raising():
    assert get_fund("Definitely Not A Fund")["name"] == DEFAULT_CURRENT_FUND


def test_sectors_are_listed_dirtiest_first():
    sectors = list_sectors()
    assert sectors[0]["name"] == "Energy (oil, gas, coal)"
    assert sectors == sorted(sectors, key=lambda item: item["intensity"], reverse=True)


def test_heavy_industry_is_far_dirtier_than_services():
    assert SECTOR_INTENSITIES["Utilities"] > 10 * SECTOR_INTENSITIES["Financials"]


# --- Financed emissions -----------------------------------------------------


def test_financed_emissions_scale_with_holding_and_intensity():
    assert financed(INTENSITY_BASIS, 55.0) == pytest.approx(55.0)
    assert financed(PENSION, 55.0) == pytest.approx(PENSION * 55.0 / INTENSITY_BASIS)


def test_a_typical_default_pension_finances_meaningful_tonnage():
    # The headline claim of the whole feature: a default pension routinely
    # finances more than a household's driving. If this figure came out at
    # 0.05 tonnes the feature would not be worth building.
    tonnes = financed(PENSION, fund_intensity(DEFAULT_CURRENT_FUND))
    assert 3.0 < tonnes < 12.0


def test_nothing_invested_finances_nothing():
    assert financed(0, 55.0) == 0.0


def test_financed_emissions_reject_junk():
    with pytest.raises(PortfolioError):
        financed("a lot", 55.0)
    with pytest.raises(PortfolioError):
        financed(-100, 55.0)
    with pytest.raises(PortfolioError):
        financed(float("nan"), 55.0)
    with pytest.raises(PortfolioError):
        financed(float("inf"), 55.0)


def test_portfolio_sums_its_holdings():
    result = portfolio_emissions(
        [
            {"name": "Pension", "value": 100000, "fund": "Global equity tracker"},
            {"name": "ISA", "value": 20000, "fund": "Paris aligned benchmark"},
        ]
    )
    assert result["total_value"] == pytest.approx(120000)
    assert result["total_emissions"] == pytest.approx(
        (100000 * 55.0 + 20000 * 15.0) / INTENSITY_BASIS
    )


def test_portfolio_shares_sum_to_one():
    result = portfolio_emissions(
        [
            {"name": "Pension", "value": 100000, "fund": "Global equity tracker"},
            {"name": "ISA", "value": 20000, "fund": "Paris aligned benchmark"},
        ]
    )
    assert sum(line["share_of_value"] for line in result["holdings"]) == pytest.approx(1.0)
    assert sum(line["share_of_carbon"] for line in result["holdings"]) == pytest.approx(1.0)


def test_a_small_dirty_holding_can_dominate_the_carbon():
    # The result that makes the breakdown worth showing: 17% of the money,
    # most of the carbon.
    result = portfolio_emissions(
        [
            {"name": "Clean pension", "value": 100000, "fund": "Paris aligned benchmark"},
            {"name": "Energy punt", "value": 20000, "fund": "Energy sector fund"},
        ]
    )
    energy = next(line for line in result["holdings"] if line["name"] == "Energy punt")
    assert energy["share_of_value"] < 0.2
    assert energy["share_of_carbon"] > 0.8
    # Holdings come back ordered by carbon, not by value.
    assert result["holdings"][0]["name"] == "Energy punt"


def test_portfolio_accepts_an_explicit_intensity():
    result = portfolio_emissions([{"name": "My fund", "value": 100000, "intensity": 33.0}])
    assert result["blended_intensity"] == pytest.approx(33.0)


def test_an_explicit_intensity_overrides_the_named_fund():
    result = portfolio_emissions(
        [{"name": "Mine", "value": 100000, "fund": "Energy sector fund", "intensity": 10.0}]
    )
    assert result["blended_intensity"] == pytest.approx(10.0)


def test_blended_intensity_is_value_weighted():
    result = portfolio_emissions(
        [
            {"name": "A", "value": 100000, "intensity": 100.0},
            {"name": "B", "value": 300000, "intensity": 20.0},
        ]
    )
    assert result["blended_intensity"] == pytest.approx(40.0)


def test_an_empty_portfolio_is_refused():
    with pytest.raises(PortfolioError):
        portfolio_emissions([])
    with pytest.raises(PortfolioError):
        portfolio_emissions(None)


def test_a_portfolio_of_nothing_does_not_divide_by_zero():
    result = portfolio_emissions([{"name": "Empty", "value": 0, "fund": "Cash / money market"}])
    assert result["total_emissions"] == 0.0
    assert result["blended_intensity"] == 0.0
    assert result["holdings"][0]["share_of_value"] == 0.0


# --- Custom portfolios ------------------------------------------------------


def test_sector_weights_produce_a_weighted_intensity():
    result = custom_portfolio({"Financials": 50, "Utilities": 50})
    expected = (SECTOR_INTENSITIES["Financials"] + SECTOR_INTENSITIES["Utilities"]) / 2
    assert result["intensity"] == pytest.approx(expected)


def test_weights_are_normalised_rather_than_required_to_sum_to_one():
    # Factsheet percentages rarely add to exactly 100, and refusing them over
    # a rounding error would be useless pedantry.
    tidy = custom_portfolio({"Financials": 0.5, "Utilities": 0.5})
    untidy = custom_portfolio({"Financials": 49, "Utilities": 51})
    assert tidy["intensity"] == pytest.approx(
        (SECTOR_INTENSITIES["Financials"] + SECTOR_INTENSITIES["Utilities"]) / 2
    )
    assert untidy["intensity"] > 0


def test_unknown_and_junk_sectors_are_ignored():
    result = custom_portfolio(
        {"Financials": 50, "Utilities": 50, "Quidditch": 100, "Healthcare": "lots"}
    )
    assert result["sectors"] == 2


def test_a_portfolio_with_no_usable_weights_is_refused():
    with pytest.raises(PortfolioError):
        custom_portfolio({"Quidditch": 100})
    with pytest.raises(PortfolioError):
        custom_portfolio({"Financials": 0})
    with pytest.raises(PortfolioError):
        custom_portfolio({})


def test_carbon_shares_sum_to_one_across_sectors():
    result = custom_portfolio({"Financials": 40, "Utilities": 30, "Healthcare": 30})
    assert sum(entry["share_of_carbon"] for entry in result["breakdown"]) == pytest.approx(1.0)


def test_sector_breakdown_is_ordered_by_carbon_contribution():
    result = custom_portfolio({"Financials": 60, "Utilities": 20, "Healthcare": 20})
    assert result["breakdown"][0]["sector"] == "Utilities"


def test_a_market_like_portfolio_lands_near_the_tracker_archetype():
    # Cross-check between the two independent data tables: sector weights
    # roughly matching a global index should reproduce roughly the tracker
    # intensity. If the two tables disagreed wildly, one of them is wrong.
    market = custom_portfolio(
        {
            "Information technology": 24,
            "Financials": 16,
            "Healthcare": 12,
            "Consumer discretionary": 11,
            "Industrials": 10,
            "Communication services": 8,
            "Consumer staples": 7,
            "Energy (oil, gas, coal)": 5,
            "Materials (cement, steel, chemicals)": 4,
            "Utilities": 3,
            "Real estate": 2,
        }
    )
    assert market["intensity"] == pytest.approx(fund_intensity("Global equity tracker"), rel=0.3)


def test_a_few_sectors_carry_most_of_the_carbon():
    # The result that makes screening make sense.
    market = custom_portfolio(
        {
            "Information technology": 24,
            "Financials": 16,
            "Healthcare": 12,
            "Consumer discretionary": 11,
            "Industrials": 10,
            "Communication services": 8,
            "Consumer staples": 7,
            "Energy (oil, gas, coal)": 5,
            "Materials (cement, steel, chemicals)": 4,
            "Utilities": 3,
            "Real estate": 2,
        }
    )
    top = concentration(market["breakdown"], top_n=3)
    assert top["share_of_carbon"] > 0.6
    assert top["share_of_value"] < 0.2


def test_concentration_of_nothing_is_empty():
    assert concentration([])["top_sectors"] == []


def test_nearest_archetype_finds_the_closest_entry():
    assert nearest_archetype(FUND_ARCHETYPES["Paris aligned benchmark"]["intensity"]) == (
        "Paris aligned benchmark"
    )
    assert nearest_archetype("junk") == DEFAULT_CURRENT_FUND


# --- Switching --------------------------------------------------------------


def test_switching_to_a_cleaner_fund_avoids_emissions():
    result = compare_funds(PENSION, 55.0, 15.0)
    assert result["is_improvement"]
    assert result["annual_avoided"] == pytest.approx(PENSION * 40.0 / INTENSITY_BASIS)
    assert result["percent_avoided"] == pytest.approx(72.7, rel=0.01)


def test_switching_to_a_dirtier_fund_is_reported_as_no_improvement():
    result = compare_funds(PENSION, 15.0, 55.0)
    assert not result["is_improvement"]
    assert result["annual_avoided"] < 0


def test_switching_between_identical_funds_changes_nothing():
    result = compare_funds(PENSION, 55.0, 55.0)
    assert result["annual_avoided"] == pytest.approx(0.0)
    assert not result["is_improvement"]


def test_comparison_of_an_empty_holding_does_not_divide_by_zero():
    assert compare_funds(0, 55.0, 15.0)["percent_avoided"] == 0.0


def test_projection_compounds_contributions_and_avoided_carbon():
    projection = project_switch(PENSION, 6000, 55.0, 15.0, years=25)
    single_year = compare_funds(PENSION, 55.0, 15.0)["annual_avoided"]
    # Contributions grow the balance, so 25 years must beat 25 flat years.
    assert projection["cumulative_avoided"] > single_year * 25
    assert projection["final_balance"] > PENSION


def test_projection_timeline_covers_every_year():
    projection = project_switch(PENSION, 6000, 55.0, 15.0, years=10)
    assert len(projection["timeline"]) == 10
    assert projection["timeline"][-1]["year"] == 10


def test_cumulative_avoided_is_monotonic():
    projection = project_switch(PENSION, 6000, 55.0, 15.0, years=15)
    running = [entry["cumulative_avoided"] for entry in projection["timeline"]]
    assert running == sorted(running)


def test_market_decarbonisation_reduces_the_credit_claimed_for_switching():
    # Part of the improvement arrives whether the user acts or not, and
    # crediting the switch with all of it would overstate the case.
    with_decline = project_switch(PENSION, 6000, 55.0, 15.0, years=25)
    without_decline = project_switch(
        PENSION, 6000, 55.0, 15.0, years=25, decarbonisation_rate=0.0
    )
    assert with_decline["cumulative_avoided"] < without_decline["cumulative_avoided"]


def test_projection_clamps_absurd_inputs():
    assert project_switch(PENSION, 0, 55.0, 15.0, years=500)["years"] == MAX_YEARS
    assert project_switch(PENSION, 0, 55.0, 15.0, years=0)["years"] == 1
    assert project_switch(PENSION, 0, 55.0, 15.0, years="ages")["years"] == 25
    clamped = project_switch(
        PENSION, 0, 55.0, 15.0, growth_rate="lots", decarbonisation_rate=5.0
    )
    assert clamped["growth_rate"] == pytest.approx(0.05)
    assert clamped["decarbonisation_rate"] == pytest.approx(0.20)


def test_projection_rejects_negative_money():
    with pytest.raises(PortfolioError):
        project_switch(-100, 6000, 55.0, 15.0)


# --- Sizing against the rest of the footprint -------------------------------


def test_a_large_pension_dominates_a_household_footprint():
    financed_tonnes = financed(400000, fund_intensity("Global equity tracker"))
    result = compare_to_operational(financed_tonnes, 5.0)
    assert result["verdict"] in ("larger", "dominates")
    assert result["ratio"] > 1.0


def test_a_small_holding_is_reported_as_smaller():
    result = compare_to_operational(financed(5000, 55.0), 5.0)
    assert result["verdict"] == "smaller"


def test_nothing_invested_is_negligible():
    assert compare_to_operational(0.0, 5.0)["verdict"] == "negligible"


def test_the_two_boundaries_are_never_silently_summed():
    result = compare_to_operational(8.0, 5.0)
    # A combined view is offered, but it is labelled and the note explains why
    # it is not the user's footprint.
    assert result["combined_view"] == pytest.approx(13.0)
    assert "double-count" in result["boundary_note"]


def test_comparison_with_no_operational_footprint_does_not_divide_by_zero():
    assert compare_to_operational(8.0, 0.0)["ratio"] == 0.0


def test_equivalents_translate_tonnes_into_recognisable_actions():
    equivalents = equivalent_actions(4.8)
    car_free = next(item for item in equivalents if item["action"] == "going car free")
    assert car_free["equivalent_years"] == pytest.approx(2.0)


def test_equivalents_are_ordered_by_how_long_the_action_would_take():
    equivalents = equivalent_actions(4.8)
    assert equivalents == sorted(
        equivalents, key=lambda item: item["equivalent_years"], reverse=True
    )


def test_equivalents_handle_zero_and_junk():
    assert all(item["equivalent_years"] == 0.0 for item in equivalent_actions(0))
    assert all(item["equivalent_years"] == 0.0 for item in equivalent_actions("lots"))


# --- Advice and caveats -----------------------------------------------------


def test_advice_quotes_the_saving_and_the_projection():
    comparison = compare_funds(PENSION, 55.0, 15.0)
    projection = project_switch(PENSION, 6000, 55.0, 15.0, years=25)
    advice = get_switch_advice(comparison, projection)
    assert any("%" in line for line in advice)
    assert any("25 years" in line for line in advice)


def test_advice_always_says_this_is_not_investment_advice():
    advice = get_switch_advice(compare_funds(PENSION, 55.0, 15.0))
    assert any("not investment advice" in line for line in advice)


def test_advice_refuses_to_endorse_a_dirtier_switch():
    advice = get_switch_advice(compare_funds(PENSION, 15.0, 55.0))
    assert len(advice) == 1
    assert "not lighter" in advice[0]


def test_caveats_cover_the_known_criticisms_of_the_method():
    caveats = " ".join(get_caveats()).lower()
    # Divestment not being a physical reduction is the strongest objection to
    # this whole feature, and the module must not omit it.
    assert "does not by itself reduce" in caveats
    assert "engagement" in caveats
    assert "scope 3" in caveats
    assert "archetypes" in caveats


def test_there_are_several_caveats_not_a_token_one():
    assert len(get_caveats()) >= 4


# --- Persistence ------------------------------------------------------------


def test_saved_portfolio_round_trips():
    result = portfolio_emissions(
        [{"name": "Pension", "value": PENSION, "fund": DEFAULT_CURRENT_FUND}]
    )
    assert save_portfolio(1, "My pension", result)

    portfolios = get_portfolios(1)
    assert len(portfolios) == 1
    assert portfolios[0]["name"] == "My pension"
    assert portfolios[0]["total_value"] == pytest.approx(PENSION)
    assert len(portfolios[0]["holdings"]) == 1


def test_portfolios_come_back_newest_first():
    result = portfolio_emissions([{"name": "Pension", "value": PENSION, "fund": DEFAULT_CURRENT_FUND}])
    save_portfolio(1, "Older", result)
    save_portfolio(1, "Newer", result)
    assert [item["name"] for item in get_portfolios(1)] == ["Newer", "Older"]


def test_portfolios_are_scoped_to_their_user():
    result = portfolio_emissions([{"name": "Pension", "value": PENSION, "fund": DEFAULT_CURRENT_FUND}])
    save_portfolio(1, "Mine", result)
    assert get_portfolios(2) == []


def test_deleting_a_portfolio_removes_it():
    result = portfolio_emissions([{"name": "Pension", "value": PENSION, "fund": DEFAULT_CURRENT_FUND}])
    portfolio_id = save_portfolio(1, "Temporary", result)
    assert delete_portfolio(1, portfolio_id)
    assert get_portfolios(1) == []


def test_a_portfolio_cannot_be_deleted_by_another_user():
    result = portfolio_emissions([{"name": "Pension", "value": PENSION, "fund": DEFAULT_CURRENT_FUND}])
    portfolio_id = save_portfolio(1, "Mine", result)
    assert not delete_portfolio(2, portfolio_id)
    assert len(get_portfolios(1)) == 1


def test_persistence_helpers_ignore_missing_ids():
    assert save_portfolio(None, "x", {}) is None
    assert get_portfolios(None) == []
    assert delete_portfolio(None, 1) is False
    assert delete_portfolio(1, None) is False

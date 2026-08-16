"""Unit tests for Climate Career Hub functionality."""

from database import (
    init_climate_careers_db,
    seed_climate_careers,
    get_career_opportunities,
    add_career_opportunity,
    toggle_career_bookmark,
    get_bookmarked_careers,
    is_career_bookmarked,
)


def test_init_and_seed_climate_careers():
    """Verify database initialization and career seeding."""
    assert init_climate_careers_db() is True
    seed_climate_careers()

    careers = get_career_opportunities()
    assert len(careers) >= 7
    titles = [c["title"] for c in careers]
    assert "Solar Energy Systems Engineer" in titles


def test_filter_careers_by_domain_and_type():
    """Verify filtering by opportunity type and domain."""
    solar_jobs = get_career_opportunities(domain="Renewable Energy")
    assert len(solar_jobs) >= 1
    assert solar_jobs[0]["domain"] == "Renewable Energy"

    fellowships = get_career_opportunities(opportunity_type="Fellowships")
    assert len(fellowships) >= 2
    for f in fellowships:
        assert f["type"] == "Fellowships"


def test_filter_careers_by_location_and_search():
    """Verify location and keyword search."""
    remote_jobs = get_career_opportunities(location="Remote")
    assert len(remote_jobs) >= 3

    search_res = get_career_opportunities(search_query="Carbon")
    assert len(search_res) >= 2


def test_add_and_bookmark_career():
    """Verify posting a career and bookmarking it."""
    import uuid
    test_user_id = 42
    unique_title = f"Grid Decarbonization Specialist {uuid.uuid4().hex[:6]}"
    success = add_career_opportunity(
        title=unique_title,
        company="GreenGrid Corp",
        opportunity_type="Full-Time Jobs",
        domain="Renewable Energy",
        location="Remote",
        description="Lead transmission line grid integration modeling.",
        apply_url="https://greengrid.com/apply",
    )
    assert success is True

    jobs = get_career_opportunities(search_query=unique_title)
    assert len(jobs) == 1
    job_id = jobs[0]["id"]


    assert is_career_bookmarked(test_user_id, job_id) is False

    # Toggle bookmark ON
    toggle_career_bookmark(test_user_id, job_id)
    assert is_career_bookmarked(test_user_id, job_id) is True

    user_bookmarks = get_bookmarked_careers(test_user_id)
    bm_ids = [b["id"] for b in user_bookmarks]
    assert job_id in bm_ids

    # Toggle bookmark OFF
    toggle_career_bookmark(test_user_id, job_id)
    assert is_career_bookmarked(test_user_id, job_id) is False

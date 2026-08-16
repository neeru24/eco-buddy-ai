"""Sustainability Book & Podcast Library.

Recommends books, documentaries, podcasts, and YouTube channels related to
sustainability. Supports categorization, keyword search, saving favorites,
and tracking completed resources.

Self-contained module: static curated catalogue plus a lazily-created SQLite
table for per-user favorites and completion tracking.
"""

import os
import json
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

RESOURCE_TYPES = {
    "books": "📚 Books",
    "documentaries": "🎬 Documentaries",
    "podcasts": "🎧 Podcasts",
    "youtube": "▶️ YouTube Channels",
}

LIBRARY = {
    "books": [
        {
            "id": "book_1",
            "title": "How to Avoid a Climate Disaster",
            "author": "Bill Gates",
            "year": 2021,
            "summary": "A practical, technology-focused roadmap of what it will take to reach net-zero.",
            "tags": ["climate", "policy", "technology"],
            "link": "https://www.gatesnotes.com/How-to-Avoid-a-Climate-Disaster",
        },
        {
            "id": "book_2",
            "title": "The Uninhabitable Earth",
            "author": "David Wallace-Wells",
            "year": 2019,
            "summary": "A vivid account of what a warming planet means for life as we know it.",
            "tags": ["climate", "impacts", "warming"],
            "link": "https://www.penguinrandomhouse.com/books/591318/the-uninhabitable-earth-by-david-wallace-wells/",
        },
        {
            "id": "book_3",
            "title": "Braiding Sweetgrass",
            "author": "Robin Wall Kimmerer",
            "year": 2013,
            "summary": "Indigenous wisdom, scientific knowledge, and the teachings of plants.",
            "tags": ["nature", "indigenous", "ecology"],
            "link": "https://milkweed.org/book/braiding-sweetgrass",
        },
        {
            "id": "book_4",
            "title": "Silent Spring",
            "author": "Rachel Carson",
            "year": 1962,
            "summary": "The landmark book that launched the modern environmental movement.",
            "tags": ["pollution", "pesticides", "history"],
            "link": "https://www.rachelcarson.org/silentSpring.aspx",
        },
        {
            "id": "book_5",
            "title": "Drawdown",
            "author": "Paul Hawken",
            "year": 2017,
            "summary": "The most comprehensive plan ever proposed to reverse global warming.",
            "tags": ["solutions", "climate", "action"],
            "link": "https://drawdown.org/",
        },
        {
            "id": "book_6",
            "title": "Cradle to Cradle",
            "author": "Michael Braungart & William McDonough",
            "year": 2002,
            "summary": "Redesigning products so waste becomes food — the circular-economy classic.",
            "tags": ["circular economy", "design", "waste"],
            "link": "https://mcdonough.com/writings/cradle-cradle/",
        },
        {
            "id": "book_7",
            "title": "The Future We Choose",
            "author": "Christiana Figueres & Tom Rivett-Carnac",
            "year": 2020,
            "summary": "Surviving the climate crisis — the mindset and actions that can build a better world.",
            "tags": ["climate", "optimism", "action"],
            "link": "https://thefuturewechoose.com/",
        },
        {
            "id": "book_8",
            "title": "No One Is Too Small to Make a Difference",
            "author": "Greta Thunberg",
            "year": 2019,
            "summary": "A collection of Greta's urgent speeches on the climate crisis.",
            "tags": ["climate", "activism", "speeches"],
            "link": "https://www.penguin.co.uk/books/111/1118703/no-one-is-too-small-to-make-a-difference/9780141991740",
        },
        {
            "id": "book_9",
            "title": "Doughnut Economics",
            "author": "Kate Raworth",
            "year": 2017,
            "summary": "Seven ways to think like a 21st-century economist, balancing people and planet.",
            "tags": ["economics", "policy", "wellbeing"],
            "link": "https://www.kateraworth.com/doughnut/",
        },
        {
            "id": "book_10",
            "title": "The Nature of Nature",
            "author": "Enric Sala",
            "year": 2020,
            "summary": "A marine ecologist's case for why we need the wild for our own survival.",
            "tags": ["nature", "biodiversity", "ocean"],
            "link": "https://www.nationalgeographic.com/books/related/nature-of-nature",
        },
    ],
    "documentaries": [
        {
            "id": "doc_1",
            "title": "An Inconvenient Truth",
            "director": "Davis Guggenheim",
            "year": 2006,
            "summary": "Al Gore's landmark documentary that brought climate change to the mainstream.",
            "tags": ["climate", "awareness", "politics"],
            "link": "https://www.imdb.com/title/tt0497116/",
        },
        {
            "id": "doc_2",
            "title": "Our Planet",
            "director": "Alastair Fothergill",
            "year": 2019,
            "summary": "A breathtaking nature series narrated by David Attenborough.",
            "tags": ["nature", "biodiversity", "wildlife"],
            "link": "https://www.ourplanet.com/",
        },
        {
            "id": "doc_3",
            "title": "Chasing Ice",
            "director": "Jeff Orlowski",
            "year": 2012,
            "summary": "Time-lapse photography documenting the melting of Arctic glaciers.",
            "tags": ["climate", "glaciers", "visual"],
            "link": "https://www.chasingice.com/",
        },
        {
            "id": "doc_4",
            "title": "Cowspiracy",
            "director": "Kip Andersen & Keegan Kuhn",
            "year": 2014,
            "summary": "An investigation into the environmental impact of animal agriculture.",
            "tags": ["agriculture", "meat", "environment"],
            "link": "https://www.cowspiracy.com/",
        },
        {
            "id": "doc_5",
            "title": "The True Cost",
            "director": "Andrew Morgan",
            "year": 2015,
            "summary": "The hidden human and environmental costs of fast fashion.",
            "tags": ["fashion", "consumption", "workers"],
            "link": "https://truecostmovie.com/",
        },
        {
            "id": "doc_6",
            "title": "Kiss the Ground",
            "director": "Josh Tickell",
            "year": 2020,
            "summary": "How regenerative agriculture can help heal the planet's soil and climate.",
            "tags": ["regenerative", "soil", "farming"],
            "link": "https://kissthegroundmovie.com/",
        },
        {
            "id": "doc_7",
            "title": "Before the Flood",
            "director": "Fisher Stevens",
            "year": 2016,
            "summary": "Leonardo DiCaprio's global journey documenting climate impacts and solutions.",
            "tags": ["climate", "impacts", "solutions"],
            "link": "https://www.imdb.com/title/tt5929776/",
        },
        {
            "id": "doc_8",
            "title": "My Octopus Teacher",
            "director": "Pippa Ehrlich & James Reed",
            "year": 2020,
            "summary": "An award-winning story of connection between a diver and a wild octopus.",
            "tags": ["ocean", "nature", "connection"],
            "link": "https://www.netflix.com/title/81045007",
        },
    ],
    "podcasts": [
        {
            "id": "pod_1",
            "title": "How to Save a Planet",
            "host": "Alex Blumberg & Dr. Ayana Elizabeth Johnson",
            "summary": "Asks the big questions about climate change and explores real solutions.",
            "tags": ["climate", "solutions", "interviews"],
            "link": "https://gimletmedia.com/shows/howtosaveaplanet",
        },
        {
            "id": "pod_2",
            "title": "The Climate Question",
            "host": "BBC World Service",
            "summary": "Answers your questions about the biggest issues of the climate crisis.",
            "tags": ["climate", "explainers", "bbc"],
            "link": "https://www.bbc.co.uk/programmes/w3ct1xxl",
        },
        {
            "id": "pod_3",
            "title": "Sustainability Defined",
            "host": "Jay Siegel & Scott Breen",
            "summary": "Breaks down the buzzwords of sustainability one episode at a time.",
            "tags": ["sustainability", "education", "definitions"],
            "link": "https://sustainabilitydefined.com/",
        },
        {
            "id": "pod_4",
            "title": "The Great Simplification",
            "host": "Nate Hagens",
            "summary": "Explores energy, economy, and the environment through a systems lens.",
            "tags": ["systems", "energy", "economy"],
            "link": "https://www.thegreatsimplification.com/",
        },
        {
            "id": "pod_5",
            "title": "Waste Not Why Not",
            "host": "Lisa Heinze & Bob Lilienfeld",
            "summary": "Practical, upbeat conversations about reducing waste in daily life.",
            "tags": ["waste", "lifestyle", "tips"],
            "link": "https://wastenotwhynot.com/",
        },
        {
            "id": "pod_6",
            "title": "A Matter of Degrees",
            "host": "Dr. Leah Stokes & Katharine Wilkinson",
            "summary": "Stories of the people powering the clean-energy transition.",
            "tags": ["energy", "transition", "stories"],
            "link": "https://www.degreespod.com/",
        },
    ],
    "youtube": [
        {
            "id": "yt_1",
            "title": "Kurzgesagt – In a Nutshell",
            "channel": "Kurzgesagt",
            "summary": "Animated explainers on climate science, energy, and big ideas.",
            "tags": ["explainers", "science", "animation"],
            "link": "https://www.youtube.com/@Kurzgesagt",
        },
        {
            "id": "yt_2",
            "title": "Undecided with Matt Ferrell",
            "channel": "Matt Ferrell",
            "summary": "Explores clean energy and smart-home tech with real-world experiments.",
            "tags": ["energy", "technology", "home"],
            "link": "https://www.youtube.com/@UndecidedMF",
        },
        {
            "id": "yt_3",
            "title": "Terra Mater",
            "channel": "Terra Mater",
            "summary": "High-quality nature documentaries and wildlife storytelling.",
            "tags": ["nature", "wildlife", "documentary"],
            "link": "https://www.youtube.com/@TerraMaterOfficial",
        },
        {
            "id": "yt_4",
            "title": "Simon Clark",
            "channel": "Simon Clark",
            "summary": "Climate and atmospheric science explained accessibly.",
            "tags": ["science", "climate", "education"],
            "link": "https://www.youtube.com/@SimonOxfPhys",
        },
        {
            "id": "yt_5",
            "title": "Our Changing Climate",
            "channel": "Our Changing Climate",
            "summary": "In-depth essays on climate justice, solutions, and the environment.",
            "tags": ["climate", "justice", "essays"],
            "link": "https://www.youtube.com/@OurChangingClimate",
        },
        {
            "id": "yt_6",
            "title": "Minimalist Tech",
            "channel": "Minimalist Tech",
            "summary": "Sustainable, low-consumption technology reviews and guides.",
            "tags": ["tech", "minimalism", "reviews"],
            "link": "https://www.youtube.com/@MinimalistTech",
        },
    ],
}

CATEGORIES = ["All", "Books", "Documentaries", "Podcasts", "YouTube Channels"]

TAGS = {
    "climate": "🌡️",
    "energy": "⚡",
    "nature": "🌿",
    "ocean": "🌊",
    "waste": "♻️",
    "solutions": "💡",
    "action": "🚀",
    "policy": "🏛️",
}


def get_resources(resource_type: str | None = None) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
    """Return resources of a given type, or all resources grouped by type."""
    if resource_type and resource_type in LIBRARY:
        return LIBRARY[resource_type]
    return LIBRARY


def search_resources(query: str, category: str = "All") -> list[dict[str, Any]]:
    """Search resources by keyword (title, author, summary, tags) with optional category filter."""
    query_lower = (query or "").strip().lower()

    type_map = {
        "Books": "books",
        "Documentaries": "documentaries",
        "Podcasts": "podcasts",
        "YouTube Channels": "youtube",
    }

    results = []
    for rtype, items in LIBRARY.items():
        if category != "All" and rtype != type_map.get(category):
            continue
        for item in items:
            haystack = " ".join([
                str(item.get("title", "")),
                str(item.get("author", "")),
                str(item.get("host", "")),
                str(item.get("channel", "")),
                str(item.get("director", "")),
                str(item.get("summary", "")),
                " ".join(item.get("tags", [])),
            ]).lower()
            if not query_lower or query_lower in haystack:
                results.append({"type": rtype, **item})
    return results


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_library_db() -> bool:
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS library_saved (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resource_id TEXT NOT NULL,
                UNIQUE(user_id, resource_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS library_completed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resource_id TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, resource_id)
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Library init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def save_favorite(user_id: int, resource_id: str) -> bool:
    init_library_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO library_saved (user_id, resource_id) VALUES (?, ?)",
            (user_id, resource_id),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to save favorite: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def remove_favorite(user_id: int, resource_id: str) -> bool:
    init_library_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            "DELETE FROM library_saved WHERE user_id = ? AND resource_id = ?",
            (user_id, resource_id),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to remove favorite: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_favorites(user_id: int) -> list[str]:
    init_library_db()
    conn = None
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT resource_id FROM library_saved WHERE user_id = ?", (user_id,)
        ).fetchall()
        return [r[0] for r in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load favorites: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def mark_completed(user_id: int, resource_id: str) -> bool:
    init_library_db()
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO library_completed (user_id, resource_id) VALUES (?, ?)",
            (user_id, resource_id),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Unable to mark completed: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def get_completed(user_id: int) -> list[str]:
    init_library_db()
    conn = None
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT resource_id FROM library_completed WHERE user_id = ?", (user_id,)
        ).fetchall()
        return [r[0] for r in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load completed: %s", exc)
        return []
    finally:
        if conn:
            conn.close()

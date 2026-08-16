import io
import json
import datetime
import pytest
from location_parser import (
    parse_gpx,
    parse_google_takeout_json,
    parse_and_segment_file_bytes,
    segment_trips,
    process_segment,
)

GPX_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Mock">
  <trk>
    <trkseg>
      <trkpt lat="47.644548" lon="-122.326897">
        <time>2023-10-01T10:00:00Z</time>
      </trkpt>
      <trkpt lat="47.645000" lon="-122.327000">
        <time>2023-10-01T10:02:00Z</time>
      </trkpt>
      <trkpt lat="47.648000" lon="-122.330000">
        <time>2023-10-01T10:05:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""


def test_parse_gpx_returns_correct_waypoint_count():
    waypoints = parse_gpx(GPX_CONTENT)
    assert len(waypoints) == 3


def test_parse_gpx_waypoint_structure():
    waypoints = parse_gpx(GPX_CONTENT)
    for wp in waypoints:
        assert "lat" in wp
        assert "lon" in wp
        assert "timestamp" in wp
        assert isinstance(wp["lat"], float)
        assert isinstance(wp["lon"], float)
        assert isinstance(wp["timestamp"], datetime.datetime)


def test_segment_trips_single_continuous_segment():
    waypoints = parse_gpx(GPX_CONTENT)
    segments = segment_trips(waypoints, time_threshold_minutes=30)
    assert len(segments) == 1


def test_segment_trips_detects_mode():
    waypoints = parse_gpx(GPX_CONTENT)
    segments = segment_trips(waypoints, time_threshold_minutes=30)
    assert len(segments) > 0
    mode = segments[0]["mode"]
    assert mode in ["Walking", "Bike", "Public Transport", "Car"]


def test_segment_trips_distance_positive():
    waypoints = parse_gpx(GPX_CONTENT)
    segments = segment_trips(waypoints, time_threshold_minutes=30)
    assert len(segments) > 0
    assert segments[0]["distance_km"] > 0


def test_segment_trips_splits_on_time_gap():
    wpts = [
        {"lat": 47.644, "lon": -122.326, "timestamp": datetime.datetime(2023, 10, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)},
        {"lat": 47.645, "lon": -122.327, "timestamp": datetime.datetime(2023, 10, 1, 10, 2, 0, tzinfo=datetime.timezone.utc)},
        {"lat": 47.648, "lon": -122.330, "timestamp": datetime.datetime(2023, 10, 1, 11, 0, 0, tzinfo=datetime.timezone.utc)},
    ]
    segments = segment_trips(wpts, time_threshold_minutes=30)
    assert len(segments) == 1


def test_detect_transport_mode_speed_ranges():
    from location_parser import detect_transport_mode
    assert detect_transport_mode(5.0) == "Walking"
    assert detect_transport_mode(15.0) == "Bike"
    assert detect_transport_mode(35.0) == "Public Transport"
    assert detect_transport_mode(60.0) == "Car"


class TestParsingErrors:
    """Tests that malformed input produces specific, descriptive errors
    instead of a generic message or a silently-empty result (see issue:
    'Improve API Error Messages')."""

    def test_parse_gpx_with_invalid_xml_raises_parsing_error(self):
        from errors import ParsingError

        with pytest.raises(ParsingError) as exc_info:
            parse_gpx("this is not gpx xml at all")

        assert exc_info.value.code == "PARSING_ERROR"
        assert "GPX" in exc_info.value.message

    def test_parse_google_takeout_json_with_malformed_json_raises_parsing_error(self):
        from errors import ParsingError

        with pytest.raises(ParsingError) as exc_info:
            parse_google_takeout_json(io.BytesIO(b"{not: valid json"))

        assert exc_info.value.code == "PARSING_ERROR"

    def test_parse_and_segment_unsupported_extension(self):
        result = parse_and_segment_file_bytes(b"whatever", "trip.csv")

        assert result["success"] is False
        assert result["error_code"] == "VALIDATION_ERROR"
        assert ".csv" in result["error"]
        assert result["waypoints"] == []
        assert result["segments"] == []

    def test_parse_and_segment_corrupted_gpx(self):
        result = parse_and_segment_file_bytes(b"not a gpx file", "trip.gpx")

        assert result["success"] is False
        assert result["error_code"] == "PARSING_ERROR"
        assert result["error"]

    def test_parse_and_segment_empty_takeout_json(self):
        payload = json.dumps({"locations": []}).encode("utf-8")
        result = parse_and_segment_file_bytes(payload, "Location History.json")

        assert result["success"] is False
        assert result["error_code"] == "PARSING_ERROR"
        assert "waypoints" in result["error"].lower()

    def test_parse_and_segment_valid_gpx_succeeds(self):
        result = parse_and_segment_file_bytes(GPX_CONTENT.encode("utf-8"), "trip.gpx")

        assert result["success"] is True
        assert result["error"] is None
        assert result["error_code"] is None
        assert len(result["waypoints"]) == 3


def test_process_segment_returns_required_keys():
    wpts = [
        {"lat": 47.644, "lon": -122.326, "timestamp": datetime.datetime(2023, 10, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)},
        {"lat": 47.645, "lon": -122.327, "timestamp": datetime.datetime(2023, 10, 1, 10, 2, 0, tzinfo=datetime.timezone.utc)},
    ]
    result = process_segment(wpts)
    assert "start_time" in result
    assert "end_time" in result
    assert "distance_km" in result
    assert "mode" in result
    assert "avg_speed_kmh" in result
    assert "waypoints" in result

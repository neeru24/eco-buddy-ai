import io
import gpxpy
import ijson
import datetime
from geopy.distance import geodesic

def parse_gpx(file_content_str):
    gpx = gpxpy.parse(file_content_str)
    waypoints = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.time:
                    waypoints.append({
                        "lat": point.latitude,
                        "lon": point.longitude,
                        "timestamp": point.time
                    })
    return waypoints

def parse_google_takeout_json(file_stream):
    waypoints = []
    try:
        objects = ijson.items(file_stream, 'locations.item')
        for obj in objects:
            if 'latitudeE7' in obj and 'longitudeE7' in obj:
                lat = obj['latitudeE7'] / 1e7
                lon = obj['longitudeE7'] / 1e7
                ts_str = obj.get('timestamp')
                if not ts_str:
                    if 'timestampMs' in obj:
                        ts = datetime.datetime.fromtimestamp(int(obj['timestampMs'])/1000.0, tz=datetime.timezone.utc)
                    else:
                        continue
                else:
                    try:
                        ts = datetime.datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                        
                waypoints.append({
                    "lat": lat,
                    "lon": lon,
                    "timestamp": ts
                })
    except Exception as e:
        print(f"JSON parsing error: {e}")
    return waypoints

def detect_transport_mode(avg_speed_kmh):
    if avg_speed_kmh < 7:
        return "Walking"
    elif avg_speed_kmh < 25:
        return "Bike"
    elif avg_speed_kmh < 50:
        return "Public Transport"
    else:
        return "Car"

def segment_trips(waypoints, time_threshold_minutes=30):
    if not waypoints:
        return []
    
    waypoints = sorted(waypoints, key=lambda x: x["timestamp"])
    
    segments = []
    current_segment = [waypoints[0]]
    
    for i in range(1, len(waypoints)):
        prev_wp = waypoints[i-1]
        curr_wp = waypoints[i]
        
        time_diff = (curr_wp["timestamp"] - prev_wp["timestamp"]).total_seconds() / 60.0
        
        if time_diff > time_threshold_minutes:
            if len(current_segment) > 1:
                processed = process_segment(current_segment)
                if processed["distance_km"] > 0.1:
                    segments.append(processed)
            current_segment = [curr_wp]
        else:
            current_segment.append(curr_wp)
            
    if len(current_segment) > 1:
        processed = process_segment(current_segment)
        if processed["distance_km"] > 0.1:
            segments.append(processed)
        
    return segments

def process_segment(segment_waypoints):
    total_distance_km = 0.0
    for i in range(1, len(segment_waypoints)):
        coord1 = (segment_waypoints[i-1]["lat"], segment_waypoints[i-1]["lon"])
        coord2 = (segment_waypoints[i]["lat"], segment_waypoints[i]["lon"])
        total_distance_km += geodesic(coord1, coord2).kilometers
        
    start_time = segment_waypoints[0]["timestamp"]
    end_time = segment_waypoints[-1]["timestamp"]
    total_time_hours = (end_time - start_time).total_seconds() / 3600.0
    
    avg_speed = total_distance_km / total_time_hours if total_time_hours > 0 else 0
    mode = detect_transport_mode(avg_speed)
    
    return {
        "start_time": start_time,
        "end_time": end_time,
        "distance_km": total_distance_km,
        "mode": mode,
        "avg_speed_kmh": avg_speed,
        "waypoints": segment_waypoints
    }

def parse_and_segment_file_bytes(file_bytes: bytes, filename: str, progress_callback=None):
    """
    Parses GPX or Google Takeout JSON bytes and segments trips in a background worker thread.
    Thread-safe helper supporting optional progress callbacks.
    """
    if progress_callback:
        progress_callback(0.1, "Reading file bytes...")

    filename_lower = filename.lower()
    if filename_lower.endswith(".gpx"):
        content = file_bytes.decode("utf-8")
        if progress_callback:
            progress_callback(0.3, "Parsing GPX waypoints...")
        waypoints = parse_gpx(content)
    elif filename_lower.endswith(".json"):
        if progress_callback:
            progress_callback(0.3, "Parsing Google Takeout JSON...")
        waypoints = parse_google_takeout_json(io.BytesIO(file_bytes))
    else:
        waypoints = []

    if not waypoints:
        return {"waypoints": [], "segments": [], "error": "No valid waypoints found."}

    if progress_callback:
        progress_callback(0.7, "Segmenting trips & calculating geodesic distances...")

    segments = segment_trips(waypoints)

    if progress_callback:
        progress_callback(1.0, "Parsing and segmentation complete!")

    return {"waypoints": waypoints, "segments": segments, "error": None}

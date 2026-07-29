import math
import os
import streamlit as st
import datetime
from PIL import Image, ImageDraw, ImageFont
from cache import cached
from cache_config import TTL_COMPUTED_ANALYTICS, CACHE_CATEGORY_COMPUTED

from database import (
    award_xp, get_total_xp, get_user_challenges, complete_challenge,
    get_unlocked_badges, unlock_badge_in_db, update_challenge_progress,
    enroll_challenge, get_skill_tree_progress, update_skill_node_status,
    get_assessments, get_diet_history
)
from config import normalize_diet
from skill_tree_data import SKILL_TREE_NODES

CHALLENGES = {
    'c1': {'title': 'Walk or bike 20 km', 'category': 'Transport', 'target': 20, 'unit': 'km', 'xp': 50},
    'c2': {'title': 'Avoid non-vegetarian meals for 3 days', 'category': 'Diet', 'target': 3, 'unit': 'days', 'xp': 40},
    'c3': {'title': 'Reduce electricity use', 'category': 'Energy', 'target': 1, 'unit': 'completion', 'xp': 30},
    'c4': {'title': 'Complete a carbon-footprint assessment', 'category': 'General', 'target': 1, 'unit': 'completion', 'xp': 60},
    'c5': {'title': 'Avoid single-use plastic for 5 days', 'category': 'General', 'target': 5, 'unit': 'days', 'xp': 50}
}

BADGES = {
    'b1': {'name': 'First Assessment', 'desc': 'Completed your first footprint assessment', 'xp': 20},
    'b2': {'name': '7-Day Streak', 'desc': 'Logged activity for 7 consecutive days', 'xp': 50},
    'b3': {'name': 'Challenge Champion', 'desc': 'Completed 5 weekly challenges', 'xp': 100},
    'b4': {'name': 'Plant-Based Week', 'desc': 'Avoided non-vegetarian meals for 7 days', 'xp': 50}
}


def calculate_level(total_xp):
    if total_xp < 0:
        return 1
    return math.floor(math.sqrt(total_xp / 100)) + 1


def calculate_level_progress(total_xp):
    current_level = calculate_level(total_xp)
    next_level = current_level + 1
    
    xp_for_current_level = ((current_level - 1) ** 2) * 100
    xp_for_next_level = ((next_level - 1) ** 2) * 100
    
    xp_in_level = total_xp - xp_for_current_level
    level_xp_req = xp_for_next_level - xp_for_current_level
    
    progress = 0
    if level_xp_req > 0:
         progress = xp_in_level / level_xp_req
         
    return progress


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def calculate_streak(user_id, activities_dates):
    # Adjust check to allow yesterday's log to keep streak alive (#86).
    # If the most recent log was yesterday, the streak remains active;
    # only reset if the last log was more than 1 day ago.
    if not activities_dates:
        return 0

    # Parse and standardise all entries to datetime.date objects
    parsed_dates = []
    for date in activities_dates:
        if isinstance(date, str):
            try:
                parsed_date = datetime.datetime.strptime(date.split(' ')[0], '%Y-%m-%d').date()
                parsed_dates.append(parsed_date)
            except ValueError:
                continue
        elif isinstance(date, datetime.datetime):
            parsed_dates.append(date.date())
        elif isinstance(date, datetime.date):
            parsed_dates.append(date)

    if not parsed_dates:
        return 0

    # Remove duplicates and sort descending (most recent first)
    unique_dates = sorted(list(set(parsed_dates)), reverse=True)

    today = datetime.date.today()
    most_recent = unique_dates[0]

    days_since_last = (today - most_recent).days
    if days_since_last > 1:
        return 0  # Streak is broken (last log was before yesterday)

    # Count backwards from the most recent activity
    streak = 1
    curr_date = most_recent
    for i in range(1, len(unique_dates)):
        next_date = unique_dates[i]
        if (curr_date - next_date).days == 1:
            streak += 1
            curr_date = next_date
        elif (curr_date - next_date).days > 1:
            break  # Gap detected

    return streak


def validate_challenge_progress(user_id, challenge_id):
    challenges = get_user_challenges(user_id)
    for c in challenges:
        if c['challenge_id'] == challenge_id and c['status'] == 'enrolled':
            ch_def = CHALLENGES.get(challenge_id)
            if not ch_def:
                continue
                
            if c['progress_value'] >= ch_def['target']:
                return is_challenge_complete(user_id, challenge_id)
    return False


def is_challenge_complete(user_id, challenge_id):
    ch_def = CHALLENGES.get(challenge_id)
    if not ch_def:
        return False
        
    success = complete_challenge(user_id, challenge_id)
    if success:
        award_challenge_xp(user_id, challenge_id)
        check_badge_eligibility(user_id)
        return True
    return False


def award_challenge_xp(user_id, challenge_id):
    ch_def = CHALLENGES.get(challenge_id)
    if ch_def:
        award_xp(user_id, 'challenge', challenge_id, ch_def['xp'], f"Completed {ch_def['title']}")


def check_badge_eligibility(user_id, check_diet=False):
    unlocked_ids = [b['badge_id'] for b in get_unlocked_badges(user_id)]

    # b1: Completed at least one footprint assessment
    if 'b1' not in unlocked_ids:
        assessments = get_assessments()
        if assessments and len(assessments) > 0:
            unlock_badge(user_id, 'b1')

    # b2: 7-day activity streak
    if 'b2' not in unlocked_ids:
        history = get_assessments()
        activities_dates = [row[1] for row in history]
        streak = calculate_streak(user_id, activities_dates)
        if streak >= 7:
            unlock_badge(user_id, 'b2')

    # b3: Completed 5 challenges
    if 'b3' not in unlocked_ids:
        challenges = get_user_challenges(user_id)
        completed_count = sum(1 for c in challenges if c['status'] == 'completed')
        if completed_count >= 5:
            unlock_badge(user_id, 'b3')

    # b4: Plant-based diet for 7 consecutive days
    if 'b4' not in unlocked_ids:
        diet_logs = get_diet_history(user_id, limit=7)
        plant_based = {"Vegetarian", "Vegan", "vegan", "vegetarian"}
        if len(diet_logs) >= 7:
            all_plant = all(row[1] in plant_based for row in diet_logs)
            if all_plant:
                unlock_badge(user_id, 'b4')


def unlock_badge(user_id, badge_id):
    if unlock_badge_in_db(user_id, badge_id):
        badge_def = BADGES.get(badge_id)
        if badge_def and badge_def.get('xp'):
            award_xp(user_id, 'badge', badge_id, badge_def['xp'], f"Unlocked badge: {badge_def['name']}")


def generate_achievement_card(user_id, badge_id, filename="badge_card.png"):
    badge_def = BADGES.get(badge_id)
    if not badge_def:
        return None
        
    width = 600
    height = 400
    
    # Create image with simple background
    img = Image.new('RGB', (width, height), color=(232, 244, 216))
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_dir, "assets", "fonts", "DejaVuSans.ttf")
    
    try:
        title_font = ImageFont.truetype(font_path, 36)
        desc_font = ImageFont.truetype(font_path, 20)
        user_font = ImageFont.truetype(font_path, 16)
    except IOError:
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        user_font = ImageFont.load_default()
        
    # Draw title
    title_text = f"🏆 {badge_def['name']}"
    draw.text((width/2, 100), title_text, fill=(46, 125, 50), font=title_font, anchor="mm")
    
    # Draw description
    desc_text = badge_def['desc']
    draw.text((width/2, 180), desc_text, fill=(55, 71, 79), font=desc_font, anchor="mm")
    
    # Draw XP
    xp_text = f"+{badge_def.get('xp', 0)} XP"
    draw.text((width/2, 240), xp_text, fill=(230, 81, 0), font=title_font, anchor="mm")
    
    # Draw user ID
    footer_text = f"EcoBuddy AI • User #{user_id}"
    draw.text((width/2, 340), footer_text, fill=(120, 144, 156), font=user_font, anchor="mm")
    
    # Draw border
    draw.rectangle([10, 10, width-10, height-10], outline=(76, 175, 80), width=4)
    
    img.save(filename)
    return filename


def evaluate_skill_tree(user_id):
    """Evaluate prerequisites and unlock nodes if ready."""
    progress = get_skill_tree_progress(user_id)
    # Convert list of dicts to a map of node_id -> status
    progress_map = {row['node_id']: row['status'] for row in progress}
    
    updates_made = False
    
    for node_id, node_data in SKILL_TREE_NODES.items():
        current_status = progress_map.get(node_id, 'Locked')
        
        if current_status == 'Locked':
            # Check if prerequisites are met
            prereqs = node_data.get('prerequisites', [])
            all_met = all(progress_map.get(p) == 'Completed' for p in prereqs)
            
            if all_met:
                update_skill_node_status(user_id, node_id, 'Unlocked')
                progress_map[node_id] = 'Unlocked'
                updates_made = True
                
    if updates_made:
        # Re-fetch if updates were made
        progress = get_skill_tree_progress(user_id)
        
    return {row['node_id']: row['status'] for row in progress}


def complete_skill_node(user_id, node_id):
    node_data = SKILL_TREE_NODES.get(node_id)
    if not node_data:
        return False
        
    success = update_skill_node_status(user_id, node_id, 'Completed')
    if success:
        award_xp(user_id, 'skill_tree', node_id, node_data['xp_reward'], f"Completed Skill: {node_data['label']}")
        # Evaluate to unlock next nodes
        evaluate_skill_tree(user_id)
        return True
    return False

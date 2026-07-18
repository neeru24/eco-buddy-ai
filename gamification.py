import math
import os
import datetime
from PIL import Image, ImageDraw, ImageFont

from database import (
    award_xp, get_total_xp, get_user_challenges, complete_challenge,
    get_unlocked_badges, unlock_badge_in_db, update_challenge_progress,
    enroll_challenge
)

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
    'b4': {'name': 'Plant-Based Week', 'desc': 'Avoided non-vegetarian meals for 7 days', 'xp': 50},
    'b5': {'name': 'Squad Founder', 'desc': 'Created a new Squad and took the lead', 'xp': 30},
    'b6': {'name': 'Squad Champion', 'desc': 'Won a multiplayer Monthly Challenge', 'xp': 100}
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

def calculate_streak(user_id, activities_dates):
    # Simplified streak calculation
    # activities_dates should be a sorted list of unique date strings or dates
    if not activities_dates:
        return 0
        
    streak = 0
    today = datetime.date.today()
    
    for i in range(len(activities_dates)):
        # Assuming dates are parsed or already date objects
        date = activities_dates[len(activities_dates) - 1 - i]
        if isinstance(date, str):
            try:
                date = datetime.datetime.strptime(date.split(' ')[0], '%Y-%m-%d').date()
            except ValueError:
                continue
                
        diff = (today - date).days
        if diff == streak: # Action done today, or consecutive
            streak += 1
        elif diff > streak:
            break
            
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

def check_badge_eligibility(user_id):
    # This would contain the logic to check if a user has met badge conditions
    # For now, it's a stub that can be expanded
    challenges = get_user_challenges(user_id)
    completed_count = sum(1 for c in challenges if c['status'] == 'completed')
    
    if completed_count >= 5:
        unlock_badge(user_id, 'b3')

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
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        desc_font = ImageFont.truetype("arial.ttf", 24)
        brand_font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        # Fallback to default font
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()
        
    total_xp = get_total_xp(user_id)
    level = calculate_level(total_xp)

    # Draw Text
    draw.text((40, 50), badge_def['name'], font=title_font, fill=(8, 11, 10))
    draw.text((40, 110), badge_def['desc'], font=desc_font, fill=(102, 115, 106))
    
    draw.text((40, 200), f"Level {level}", font=desc_font, fill=(120, 169, 69))
    draw.text((40, 240), f"Total XP: {total_xp}", font=desc_font, fill=(47, 94, 50))
    
    draw.text((450, 350), "EcoBuddy AI", font=brand_font, fill=(120, 169, 69))
    
    # Save Image
    filepath = os.path.join(os.getcwd(), filename)
    img.save(filepath)
    return filepath


def evaluate_monthly_challenges():
    # Import locally to avoid circular dependencies
    from database import get_active_monthly_challenges, get_squad_leaderboard, get_squad_members, DB_NAME
    import sqlite3

    active_challenges = get_active_monthly_challenges()
    results = []

    for challenge in active_challenges:
        leaderboard = get_squad_leaderboard() # list of squads with total_xp
        winning_squads = [s for s in leaderboard if s['total_xp'] >= challenge['target_xp']]

        badge_id = challenge['reward_badge_id']
        for squad in winning_squads:
            members = get_squad_members(squad['id'])
            for member in members:
                uid = member['user_id']
                unlock_badge(uid, badge_id)

        # Update challenge status to completed in DB
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE monthly_challenges SET status = 'completed' WHERE id = ?", (challenge['id'],))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error marking challenge completed: {e}")

        results.append({
            'challenge_id': challenge['id'],
            'winning_squads': [s['name'] for s in winning_squads]
        })

    return results

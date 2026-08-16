import math
import os
import streamlit as st
import datetime
from cache import cached
from cache_config import TTL_COMPUTED_ANALYTICS, CACHE_CATEGORY_COMPUTED

from database import (
    award_xp, get_total_xp, get_user_challenges, complete_challenge,
    get_unlocked_badges, unlock_badge_in_db, update_challenge_progress,
    enroll_challenge, get_skill_tree_progress, update_skill_node_status,
    get_assessments, get_diet_history,
    unlock_card_in_db, get_unlocked_cards,
    get_freeze_token_balance, award_freeze_tokens, redeem_freeze_token,
    use_streak_freeze, get_streak_freeze_dates,
    get_total_freeze_tokens_earned, record_environmental_milestone,
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

FREEZE_TOKEN_MILESTONES = [
    (7, 1, 'streak_7', '7-day streak'),
    (14, 1, 'streak_14', '14-day streak'),
    (30, 2, 'streak_30', '30-day streak'),
    (60, 3, 'streak_60', '60-day streak'),
    (90, 5, 'streak_90', '90-day streak'),
]

CARD_RARITIES = {
    'common':   {'label': 'Common',   'color_bg': (232, 244, 216), 'color_accent': (76, 175, 80),   'color_text': (46, 125, 50)},
    'uncommon': {'label': 'Uncommon', 'color_bg': (216, 234, 248), 'color_accent': (33, 150, 243),  'color_text': (21, 101, 192)},
    'rare':     {'label': 'Rare',     'color_bg': (239, 216, 248), 'color_accent': (156, 39, 176),  'color_text': (106, 27, 154)},
    'legendary':{'label': 'Legendary','color_bg': (255, 248, 216), 'color_accent': (255, 152, 0),   'color_text': (230, 81, 0)},
}

CARDS = {
    'crd_1': {
        'name': 'First Footprint',
        'desc': 'Completed your first carbon footprint assessment',
        'rarity': 'common',
        'icon': '👣',
        'condition': 'Complete 1 assessment',
    },
    'crd_2': {
        'name': 'Streak Master',
        'desc': 'Maintained a 7-day activity streak',
        'rarity': 'uncommon',
        'icon': '🔥',
        'condition': '7-day streak',
    },
    'crd_3': {
        'name': 'Challenge Crusher',
        'desc': 'Completed 5 weekly eco challenges',
        'rarity': 'rare',
        'icon': '🏆',
        'condition': 'Complete 5 challenges',
    },
    'crd_4': {
        'name': 'Green Palate',
        'desc': 'Ate plant-based for 7 consecutive days',
        'rarity': 'uncommon',
        'icon': '🥗',
        'condition': '7 plant-based days',
    },
    'crd_5': {
        'name': 'Compost Starter',
        'desc': 'Started your composting journey',
        'rarity': 'common',
        'icon': '🌱',
        'condition': 'Unlock Start Composting skill',
    },
    'crd_6': {
        'name': 'Zero Waste Hero',
        'desc': 'Embraced zero-waste grocery shopping',
        'rarity': 'uncommon',
        'icon': '♻️',
        'condition': 'Unlock Zero-Waste skill',
    },
    'crd_7': {
        'name': 'Plant Powered',
        'desc': 'Mastered a plant-based diet skill',
        'rarity': 'rare',
        'icon': '🌿',
        'condition': 'Complete Plant-Based Diet skill',
    },
    'crd_8': {
        'name': 'Solar Pioneer',
        'desc': 'Installed solar panels in your skill tree',
        'rarity': 'legendary',
        'icon': '☀️',
        'condition': 'Complete Install Solar Panels skill',
    },
    'crd_9': {
        'name': 'Low Carbon Champion',
        'desc': 'Achieved a carbon footprint under 2 tonnes',
        'rarity': 'rare',
        'icon': '💚',
        'condition': 'Footprint < 2 tonnes',
    },
    'crd_10': {
        'name': 'Eco Legend',
        'desc': 'Completed 10 eco challenges',
        'rarity': 'legendary',
        'icon': '🌟',
        'condition': 'Complete 10 challenges',
    },
    'crd_11': {
        'name': 'Century Streak',
        'desc': 'Logged activity for 30 consecutive days',
        'rarity': 'legendary',
        'icon': '💪',
        'condition': '30-day streak',
    },
    'crd_12': {
        'name': 'Active Mover',
        'desc': 'Walked or biked 100 km total',
        'rarity': 'uncommon',
        'icon': '🚲',
        'condition': '100 km walked/biked',
    },
    'crd_13': {
        'name': 'Energy Saver',
        'desc': 'Added appliances and completed an energy audit',
        'rarity': 'common',
        'icon': '💡',
        'condition': 'Complete energy audit',
    },
    'crd_14': {
        'name': 'Water Watcher',
        'desc': 'Tracked your water footprint',
        'rarity': 'common',
        'icon': '💧',
        'condition': 'Complete water assessment',
    },
    'crd_15': {
        'name': 'Herb Gardener',
        'desc': 'Started growing your own herbs',
        'rarity': 'common',
        'icon': '🌿',
        'condition': 'Unlock Grow Herbs skill',
    },
}


def calculate_level(total_xp: int) -> int:
    if total_xp < 0:
        return 1
    return math.floor(math.sqrt(total_xp / 100)) + 1


def calculate_level_progress(total_xp: int) -> float:
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
def calculate_streak(
    user_id: int,
    activities_dates: list[str | datetime.datetime | datetime.date],
    freeze_dates: list[str | datetime.datetime | datetime.date] | None = None,
) -> int:
    # Adjust check to allow yesterday's log to keep streak alive (#86).
    # If the most recent log was yesterday, the streak remains active;
    # only reset if the last log was more than 1 day ago.
    if not activities_dates and not freeze_dates:
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

    if freeze_dates:
        for fd in freeze_dates:
            if isinstance(fd, str):
                try:
                    parsed_dates.append(datetime.datetime.strptime(fd.split(' ')[0], '%Y-%m-%d').date())
                except ValueError:
                    continue
            elif isinstance(fd, datetime.datetime):
                parsed_dates.append(fd.date())
            elif isinstance(fd, datetime.date):
                parsed_dates.append(fd)

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


def validate_challenge_progress(user_id: int, challenge_id: str) -> bool:
    challenges = get_user_challenges(user_id)
    for c in challenges:
        if c['challenge_id'] == challenge_id and c['status'] == 'enrolled':
            ch_def = CHALLENGES.get(challenge_id)
            if not ch_def:
                continue
                
            if c['progress_value'] >= ch_def['target']:
                return is_challenge_complete(user_id, challenge_id)
    return False


def is_challenge_complete(user_id: int, challenge_id: str) -> bool:
    ch_def = CHALLENGES.get(challenge_id)
    if not ch_def:
        return False
        
    success = complete_challenge(user_id, challenge_id)
    if success:
        award_challenge_xp(user_id, challenge_id)
        check_badge_eligibility(user_id)
        return True
    return False


def award_challenge_xp(user_id: int, challenge_id: str) -> None:
    ch_def = CHALLENGES.get(challenge_id)
    if ch_def:
        award_xp(user_id, 'challenge', challenge_id, ch_def['xp'], f"Completed {ch_def['title']}")


def check_badge_eligibility(user_id: int, check_diet: bool = False) -> None:
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


def get_user_streak(user_id: int) -> int:
    assessments = get_assessments(user_id)
    activities_dates = [row[1] for row in assessments]
    freeze_dates = get_streak_freeze_dates(user_id)
    return calculate_streak(user_id, activities_dates, freeze_dates)


def award_freeze_tokens_for_streak_milestones(user_id: int) -> int:
    streak = get_user_streak(user_id)
    awarded = 0
    for threshold, tokens, milestone_type, label in FREEZE_TOKEN_MILESTONES:
        if streak >= threshold:
            success = record_environmental_milestone(
                user_id, milestone_type,
                f"Streak: {label}",
                f"Reached a {label} and earned {tokens} freeze token{'s' if tokens > 1 else ''}",
                icon="🧊"
            )
            if success:
                award_freeze_tokens(user_id, tokens, f"Streak milestone: {label}")
                awarded += tokens
    return awarded


def protect_streak_with_freeze(user_id: int) -> tuple[bool, str]:
    assessments = get_assessments(user_id)
    activities_dates = [row[1] for row in assessments]
    freeze_dates = get_streak_freeze_dates(user_id)

    current_streak = calculate_streak(user_id, activities_dates, freeze_dates)
    if current_streak == 0:
        return False, "No active streak to protect"

    today = datetime.date.today()
    parsed = []
    for date in activities_dates:
        if isinstance(date, str):
            try:
                parsed.append(datetime.datetime.strptime(date.split(' ')[0], '%Y-%m-%d').date())
            except ValueError:
                continue
        elif isinstance(date, datetime.datetime):
            parsed.append(date.date())
        elif isinstance(date, datetime.date):
            parsed.append(date)
    if freeze_dates:
        for fd in freeze_dates:
            if isinstance(fd, str):
                try:
                    parsed.append(datetime.datetime.strptime(fd.split(' ')[0], '%Y-%m-%d').date())
                except ValueError:
                    continue
            elif isinstance(fd, datetime.datetime):
                parsed.append(fd.date())
            elif isinstance(fd, datetime.date):
                parsed.append(fd)

    unique_dates = sorted(list(set(parsed)), reverse=True)
    if unique_dates and unique_dates[0] >= today:
        return False, "You already logged activity today — no freeze needed"

    balance = get_freeze_token_balance(user_id)
    if balance < 1:
        return False, "No freeze tokens available"

    yesterday = today - datetime.timedelta(days=1)
    freeze_target = yesterday
    if use_streak_freeze(user_id, str(freeze_target)):
        redeem_freeze_token(user_id)
        return True, f"Streak frozen! Protected your {current_streak}-day streak."
    return False, "Failed to apply streak freeze"


def unlock_badge(user_id: int, badge_id: str) -> None:
    if unlock_badge_in_db(user_id, badge_id):
        badge_def = BADGES.get(badge_id)
        if badge_def and badge_def.get('xp'):
            award_xp(user_id, 'badge', badge_id, badge_def['xp'], f"Unlocked badge: {badge_def['name']}")


def generate_achievement_card(user_id: int, badge_id: str, filename: str = "badge_card.png") -> str | None:
    badge_def = BADGES.get(badge_id)
    if not badge_def:
        return None

    from PIL import Image, ImageDraw, ImageFont
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


def unlock_card(user_id: int, card_id: str) -> bool:
    if unlock_card_in_db(user_id, card_id):
        return True
    return False


def generate_trading_card(user_id: int, card_id: str, filename: str = "trading_card.png") -> str | None:
    card_def = CARDS.get(card_id)
    if not card_def:
        return None

    from PIL import Image, ImageDraw, ImageFont

    rarity = CARD_RARITIES.get(card_def['rarity'], CARD_RARITIES['common'])
    width = 500
    height = 700

    img = Image.new('RGB', (width, height), rarity['color_bg'])
    draw = ImageDraw.Draw(img)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_dir, "assets", "fonts", "DejaVuSans.ttf")

    try:
        icon_font = ImageFont.truetype(font_path, 64)
        title_font = ImageFont.truetype(font_path, 32)
        rarity_font = ImageFont.truetype(font_path, 18)
        desc_font = ImageFont.truetype(font_path, 20)
        info_font = ImageFont.truetype(font_path, 16)
        footer_font = ImageFont.truetype(font_path, 14)
    except IOError:
        icon_font = title_font = rarity_font = desc_font = info_font = footer_font = ImageFont.load_default()

    accent = rarity['color_accent']
    text_color = rarity['color_text']

    # Border with double-line effect
    draw.rounded_rectangle([12, 12, width - 12, height - 12], radius=20, outline=accent, width=6)
    draw.rounded_rectangle([20, 20, width - 20, height - 20], radius=16, outline=accent, width=2)

    # Rarity badge at top
    rarity_label = rarity['label']
    draw.rounded_rectangle(
        [width // 2 - 80, 35, width // 2 + 80, 65], radius=12,
        fill=accent, outline=accent, width=2
    )
    draw.text((width // 2, 50), rarity_label, fill=(255, 255, 255), font=rarity_font, anchor="mm")

    # Icon
    draw.text((width // 2, 150), card_def['icon'], fill=text_color, font=icon_font, anchor="mm")

    # Card name
    draw.text((width // 2, 250), card_def['name'], fill=text_color, font=title_font, anchor="mm")

    # Description
    draw.text((width // 2, 320), card_def['desc'], fill=(55, 71, 79), font=desc_font, anchor="mm")

    # Condition
    draw.text((width // 2, 400), f"Unlock: {card_def['condition']}", fill=(120, 144, 156), font=info_font, anchor="mm")

    # Serial / user
    card_index = list(CARDS.keys()).index(card_id) + 1
    draw.text((width // 2, 520), f"Card #{card_index:02d} of {len(CARDS)}", fill=(120, 144, 156), font=info_font, anchor="mm")
    draw.text((width // 2, 560), f"EcoBuddy AI • User #{user_id}", fill=(180, 180, 180), font=footer_font, anchor="mm")

    # Decorative line
    draw.line([(100, 490), (width - 100, 490)], fill=accent, width=3)

    img.save(filename)
    return filename


def check_card_eligibility(user_id: int) -> list[str]:
    unlocked_ids = [c['card_id'] for c in get_unlocked_cards(user_id)]
    newly_unlocked = []

    assessments = get_assessments()

    # crd_1: First assessment
    if 'crd_1' not in unlocked_ids:
        if assessments and len(assessments) > 0:
            unlock_card(user_id, 'crd_1')
            newly_unlocked.append('crd_1')

    # crd_2: 7-day streak
    if 'crd_2' not in unlocked_ids:
        activity_dates = [row[1] for row in assessments]
        streak = calculate_streak(user_id, activity_dates)
        if streak >= 7:
            unlock_card(user_id, 'crd_2')
            newly_unlocked.append('crd_2')

    # crd_3: 5 challenges completed
    if 'crd_3' not in unlocked_ids:
        challenges = get_user_challenges(user_id)
        completed_count = sum(1 for c in challenges if c['status'] == 'completed')
        if completed_count >= 5:
            unlock_card(user_id, 'crd_3')
            newly_unlocked.append('crd_3')

    # crd_4: 7 plant-based days
    if 'crd_4' not in unlocked_ids:
        diet_logs = get_diet_history(user_id, limit=7)
        plant_based = {"Vegetarian", "Vegan", "vegan", "vegetarian"}
        if len(diet_logs) >= 7:
            all_plant = all(row[1] in plant_based for row in diet_logs)
            if all_plant:
                unlock_card(user_id, 'crd_4')
                newly_unlocked.append('crd_4')

    # crd_5: Start Composting skill unlocked
    if 'crd_5' not in unlocked_ids:
        progress = get_skill_tree_progress(user_id)
        for row in progress:
            if row['node_id'] == 'start_composting' and row['status'] in ('Unlocked', 'Completed'):
                unlock_card(user_id, 'crd_5')
                newly_unlocked.append('crd_5')
                break

    # crd_6: Zero-Waste skill unlocked
    if 'crd_6' not in unlocked_ids:
        progress = get_skill_tree_progress(user_id)
        for row in progress:
            if row['node_id'] == 'zero_waste_grocery' and row['status'] in ('Unlocked', 'Completed'):
                unlock_card(user_id, 'crd_6')
                newly_unlocked.append('crd_6')
                break

    # crd_7: Plant-Based Diet skill completed
    if 'crd_7' not in unlocked_ids:
        progress = get_skill_tree_progress(user_id)
        for row in progress:
            if row['node_id'] == 'plant_based_diet' and row['status'] == 'Completed':
                unlock_card(user_id, 'crd_7')
                newly_unlocked.append('crd_7')
                break

    # crd_8: Install Solar Panels skill completed
    if 'crd_8' not in unlocked_ids:
        progress = get_skill_tree_progress(user_id)
        for row in progress:
            if row['node_id'] == 'install_solar_panels' and row['status'] == 'Completed':
                unlock_card(user_id, 'crd_8')
                newly_unlocked.append('crd_8')
                break

    # crd_9: Footprint < 2 tonnes
    if 'crd_9' not in unlocked_ids:
        if assessments:
            best = min((row[7] for row in assessments if row[7] is not None), default=None)
            if best is not None and best < 2.0:
                unlock_card(user_id, 'crd_9')
                newly_unlocked.append('crd_9')

    # crd_10: 10 challenges completed
    if 'crd_10' not in unlocked_ids:
        challenges = get_user_challenges(user_id)
        completed_count = sum(1 for c in challenges if c['status'] == 'completed')
        if completed_count >= 10:
            unlock_card(user_id, 'crd_10')
            newly_unlocked.append('crd_10')

    # crd_11: 30-day streak
    if 'crd_11' not in unlocked_ids:
        activity_dates = [row[1] for row in assessments]
        streak = calculate_streak(user_id, activity_dates)
        if streak >= 30:
            unlock_card(user_id, 'crd_11')
            newly_unlocked.append('crd_11')

    # crd_12: 100 km walked/biked
    if 'crd_12' not in unlocked_ids:
        if assessments:
            total_km = sum(
                row[3] for row in assessments
                if row[2] and row[2].lower() in ('walking', 'walk', 'cycling', 'biking', 'bicycle', 'bike')
            )
            if total_km >= 100:
                unlock_card(user_id, 'crd_12')
                newly_unlocked.append('crd_12')

    # crd_13: Energy audit completed (has appliances)
    if 'crd_13' not in unlocked_ids:
        from database import get_appliances
        apps = get_appliances(user_id)
        if apps and len(apps) > 0:
            unlock_card(user_id, 'crd_13')
            newly_unlocked.append('crd_13')

    # crd_14: Water assessment completed
    if 'crd_14' not in unlocked_ids:
        from database import get_water_assessments
        water_data = get_water_assessments(user_id)
        if water_data and len(water_data) > 0:
            unlock_card(user_id, 'crd_14')
            newly_unlocked.append('crd_14')

    # crd_15: Grow Herbs skill unlocked
    if 'crd_15' not in unlocked_ids:
        progress = get_skill_tree_progress(user_id)
        for row in progress:
            if row['node_id'] == 'grow_herbs' and row['status'] in ('Unlocked', 'Completed'):
                unlock_card(user_id, 'crd_15')
                newly_unlocked.append('crd_15')
                break

    return newly_unlocked


def evaluate_skill_tree(user_id: int) -> dict[str, str]:
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
        progress_map = {row['node_id']: row['status'] for row in progress}
        
    return {node_id: progress_map.get(node_id, 'Locked') for node_id in SKILL_TREE_NODES}


def complete_skill_node(user_id: int, node_id: str) -> bool:
    node_data = SKILL_TREE_NODES.get(node_id)
    if not node_data:
        return False

    status_map = evaluate_skill_tree(user_id)
    if status_map.get(node_id) != 'Unlocked':
        return False

    success = update_skill_node_status(user_id, node_id, 'Completed')
    if success:
        award_xp(user_id, 'skill_tree', node_id, node_data['xp_reward'], f"Completed Skill: {node_data['label']}")
        # Evaluate to unlock next nodes
        evaluate_skill_tree(user_id)
        return True
    return False

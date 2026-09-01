"""
Water Footprint Calculator for EcoBuddy AI
Calculates water usage across various activities and provides insights.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class WaterActivity:
    """Data class for a water usage activity."""
    id: str = ""
    name: str = ""
    category: str = ""  # shower, laundry, dishes, toilet, garden, drinking, cooking, cleaning, car_wash, pool
    usage_liters: float = 0.0
    frequency: str = "daily"  # daily, weekly, monthly, occasional
    count: int = 1
    duration_minutes: float = 0.0
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WaterFootprint:
    """Data class for water footprint summary."""
    total_daily_liters: float = 0.0
    total_weekly_liters: float = 0.0
    total_monthly_liters: float = 0.0
    total_yearly_liters: float = 0.0
    by_category: Dict[str, float] = field(default_factory=dict)
    by_activity: List[Dict[str, Any]] = field(default_factory=list)
    average_daily: float = 0.0
    comparison_to_average: float = 0.0  # percentage
    efficiency_score: int = 0  # 0-100
    tips: List[str] = field(default_factory=list)


class WaterCalculator:
    """
    Calculates water footprint based on user activities and usage patterns.
    """

    # Average water usage references (liters)
    AVERAGES = {
        'shower': 45,  # per 10-minute shower
        'bath': 150,  # per bath
        'toilet': 6,  # per flush
        'washing_machine': 80,  # per load
        'dishwasher': 15,  # per cycle
        'hand_washing_dishes': 20,  # per session
        'drinking': 2,  # per day
        'cooking': 5,  # per day
        'cleaning': 10,  # per day
        'garden_watering': 100,  # per session
        'car_wash': 150,  # per wash
        'pool': 100,  # per day
        'lawn_sprinkler': 60,  # per 15 minutes
        'faucet': 8,  # per minute
        'leak': 50,  # per day (drip)
    }

    # Daily recommended intake
    RECOMMENDED_DAILY = 50  # liters per person per day

    # Efficiency scoring
    EFFICIENCY_LEVELS = {
        'excellent': (80, 100, '🌟 Excellent water conservation!'),
        'good': (60, 79, '🌿 Good water usage! Room for improvement.'),
        'average': (40, 59, '💧 Average usage. Consider making changes.'),
        'needs_improvement': (20, 39, '⚠️ High water usage. Please review your habits.'),
        'critical': (0, 19, '🔴 Critical water usage. Immediate action needed!')
    }

    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self._activities: List[WaterActivity] = []
        self._history: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load water data from storage."""
        # In production, this would load from database
        pass

    def add_activity(self, activity: WaterActivity) -> Dict[str, Any]:
        """
        Add a water usage activity.
        
        Args:
            activity: WaterActivity object
        
        Returns:
            Result dictionary
        """
        try:
            self._activities.append(activity)
            return {
                'success': True,
                'message': f'Activity "{activity.name}" added successfully! 💧',
                'activity_id': activity.id
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def calculate_footprint(self, days: int = 7) -> WaterFootprint:
        """
        Calculate water footprint for the specified period.
        
        Args:
            days: Number of days to calculate
        
        Returns:
            WaterFootprint object
        """
        if not self._activities:
            return self._get_empty_footprint()

        # Calculate usage per category
        category_usage = {}
        activity_details = []
        total_daily = 0.0

        for activity in self._activities:
            # Calculate daily usage
            if activity.frequency == 'daily':
                daily_usage = activity.usage_liters * activity.count
            elif activity.frequency == 'weekly':
                daily_usage = (activity.usage_liters * activity.count) / 7
            elif activity.frequency == 'monthly':
                daily_usage = (activity.usage_liters * activity.count) / 30
            else:
                daily_usage = activity.usage_liters / 30  # occasional

            # Add to category
            category = activity.category
            category_usage[category] = category_usage.get(category, 0) + daily_usage
            total_daily += daily_usage

            # Store activity details
            activity_details.append({
                'name': activity.name,
                'category': activity.category,
                'daily_usage': daily_usage,
                'weekly_usage': daily_usage * 7,
                'monthly_usage': daily_usage * 30,
                'yearly_usage': daily_usage * 365
            })

        # Calculate totals
        weekly_total = total_daily * 7
        monthly_total = total_daily * 30
        yearly_total = total_daily * 365

        # Calculate efficiency score
        efficiency_score = self._calculate_efficiency_score(total_daily)

        # Get tips
        tips = self._generate_tips(category_usage, total_daily)

        return WaterFootprint(
            total_daily_liters=total_daily,
            total_weekly_liters=weekly_total,
            total_monthly_liters=monthly_total,
            total_yearly_liters=yearly_total,
            by_category=category_usage,
            by_activity=activity_details,
            average_daily=total_daily / max(1, len(self._activities)),
            comparison_to_average=((total_daily - self.RECOMMENDED_DAILY) / self.RECOMMENDED_DAILY) * 100,
            efficiency_score=efficiency_score,
            tips=tips
        )

    def _get_empty_footprint(self) -> WaterFootprint:
        """Get empty footprint data."""
        return WaterFootprint(
            tips=["Start tracking your water usage to get personalized tips! 💧"]
        )

    def _calculate_efficiency_score(self, daily_usage: float) -> int:
        """Calculate water efficiency score."""
        if daily_usage <= 30:
            return 95
        elif daily_usage <= 50:
            return 80
        elif daily_usage <= 80:
            return 60
        elif daily_usage <= 120:
            return 40
        elif daily_usage <= 180:
            return 25
        else:
            return 10

    def _generate_tips(self, category_usage: Dict[str, float], total_daily: float) -> List[str]:
        """Generate water saving tips based on usage."""
        tips = []

        # General tips
        if total_daily > self.RECOMMENDED_DAILY:
            tips.append("💡 Your water usage is above average. Consider implementing some water-saving habits!")

        # Category-specific tips
        if category_usage.get('shower', 0) > 60:
            tips.append("🚿 Try taking shorter showers (aim for 5 minutes). Save 20L per minute!")
        
        if category_usage.get('toilet', 0) > 30:
            tips.append("🚽 Consider installing a low-flow toilet or placing a water-saving device in your tank.")
        
        if category_usage.get('washing_machine', 0) > 100:
            tips.append("👕 Only run the washing machine with full loads. Save up to 30L per load!")
        
        if category_usage.get('dishwasher', 0) > 30:
            tips.append("🍽️ Only run the dishwasher when full. Hand wash dishes in a basin to save water.")
        
        if category_usage.get('garden_watering', 0) > 100:
            tips.append("🌿 Water your garden early morning or evening to reduce evaporation. Use a watering can instead of a hose.")
        
        if category_usage.get('car_wash', 0) > 50:
            tips.append("🚗 Use a commercial car wash that recycles water, or wash your car on the lawn to water it at the same time!")
        
        if category_usage.get('pool', 0) > 50:
            tips.append("🏊 Cover your pool when not in use to reduce evaporation. Save up to 1000L per month!")

        # General conservation tips
        if len(tips) < 3:
            tips.extend([
                "💧 Fix leaky taps immediately. A dripping tap can waste 15L per day!",
                "🌧️ Collect rainwater for gardening and outdoor use.",
                "🧊 Keep a jug of water in the fridge instead of running the tap for cold water.",
                "🚿 Install water-efficient showerheads and aerators on taps."
            ])

        return tips[:5]

    def get_activity_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get all activity categories with default values."""
        return {
            'shower': {
                'name': 'Shower',
                'icon': '🚿',
                'default_usage': 45,
                'unit': 'liters per 10 min shower',
                'frequency': 'daily'
            },
            'bath': {
                'name': 'Bath',
                'icon': '🛁',
                'default_usage': 150,
                'unit': 'liters per bath',
                'frequency': 'weekly'
            },
            'toilet': {
                'name': 'Toilet',
                'icon': '🚽',
                'default_usage': 6,
                'unit': 'liters per flush',
                'frequency': 'daily'
            },
            'washing_machine': {
                'name': 'Washing Machine',
                'icon': '👕',
                'default_usage': 80,
                'unit': 'liters per load',
                'frequency': 'weekly'
            },
            'dishwasher': {
                'name': 'Dishwasher',
                'icon': '🍽️',
                'default_usage': 15,
                'unit': 'liters per cycle',
                'frequency': 'daily'
            },
            'garden_watering': {
                'name': 'Garden Watering',
                'icon': '🌿',
                'default_usage': 100,
                'unit': 'liters per session',
                'frequency': 'weekly'
            },
            'car_wash': {
                'name': 'Car Wash',
                'icon': '🚗',
                'default_usage': 150,
                'unit': 'liters per wash',
                'frequency': 'monthly'
            },
            'drinking': {
                'name': 'Drinking Water',
                'icon': '💧',
                'default_usage': 2,
                'unit': 'liters per day',
                'frequency': 'daily'
            },
            'cooking': {
                'name': 'Cooking',
                'icon': '🍳',
                'default_usage': 5,
                'unit': 'liters per day',
                'frequency': 'daily'
            },
            'cleaning': {
                'name': 'Cleaning',
                'icon': '🧹',
                'default_usage': 10,
                'unit': 'liters per day',
                'frequency': 'daily'
            }
        }

    def get_water_usage_breakdown(self, footprint: WaterFootprint) -> Dict[str, Any]:
        """Get water usage breakdown for visualization."""
        return {
            'total': footprint.total_daily_liters,
            'categories': footprint.by_category,
            'top_activities': sorted(
                footprint.by_activity,
                key=lambda x: x['daily_usage'],
                reverse=True
            )[:5]
        }

    def get_efficiency_level(self, score: int) -> Dict[str, Any]:
        """Get efficiency level based on score."""
        for level, (min_score, max_score, description) in self.EFFICIENCY_LEVELS.items():
            if min_score <= score <= max_score:
                return {
                    'level': level,
                    'score': score,
                    'description': description
                }
        return {'level': 'average', 'score': score, 'description': 'Average water usage.'}

    def get_comparison_data(self, footprint: WaterFootprint) -> Dict[str, Any]:
        """Get comparison data with averages."""
        return {
            'your_daily': footprint.total_daily_liters,
            'average_daily': self.RECOMMENDED_DAILY,
            'difference': footprint.total_daily_liters - self.RECOMMENDED_DAILY,
            'percentage': footprint.comparison_to_average,
            'status': 'above' if footprint.total_daily_liters > self.RECOMMENDED_DAILY else 'below'
        }

    def get_reduction_goal(self, current_usage: float, target_percentage: float = 20) -> Dict[str, Any]:
        """
        Get reduction goal based on current usage.
        
        Args:
            current_usage: Current daily usage in liters
            target_percentage: Target reduction percentage
        
        Returns:
            Goal data dictionary
        """
        target_usage = current_usage * (1 - target_percentage / 100)
        reduction_needed = current_usage - target_usage
        
        return {
            'current_usage': current_usage,
            'target_usage': target_usage,
            'reduction_needed': reduction_needed,
            'target_percentage': target_percentage,
            'daily_saving': reduction_needed,
            'monthly_saving': reduction_needed * 30,
            'yearly_saving': reduction_needed * 365
        }
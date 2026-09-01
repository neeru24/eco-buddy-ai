"""
Water Analytics for EcoBuddy AI
Provides analytics, trends, and insights for water usage data.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, date
import json
import logging
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)


class WaterAnalytics:
    """
    Analyzes water usage data and provides insights and trends.
    """

    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load water history data from storage."""
        # In production, this would load from database
        pass

    def analyze_trends(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze water usage trends over time.
        
        Args:
            data: List of water usage data points
        
        Returns:
            Trend analysis dictionary
        """
        if not data or len(data) < 2:
            return {
                'trend': 'stable',
                'change_percentage': 0,
                'average_usage': 0,
                'peak_usage': 0,
                'low_usage': 0,
                'volatility': 0
            }

        # Extract usage values
        values = [d.get('daily_usage', 0) for d in data]
        
        # Calculate statistics
        avg_usage = statistics.mean(values) if values else 0
        peak_usage = max(values) if values else 0
        low_usage = min(values) if values else 0
        
        # Calculate trend
        if len(values) >= 3:
            first_avg = statistics.mean(values[:len(values)//3]) if len(values) >= 3 else values[0]
            last_avg = statistics.mean(values[-len(values)//3:]) if len(values) >= 3 else values[-1]
            
            if last_avg > first_avg * 1.1:
                trend = 'increasing'
                change_percentage = ((last_avg - first_avg) / first_avg) * 100
            elif last_avg < first_avg * 0.9:
                trend = 'decreasing'
                change_percentage = ((first_avg - last_avg) / first_avg) * 100
            else:
                trend = 'stable'
                change_percentage = 0
        else:
            trend = 'stable'
            change_percentage = 0
        
        # Calculate volatility (standard deviation)
        volatility = statistics.stdev(values) if len(values) > 1 else 0

        return {
            'trend': trend,
            'change_percentage': change_percentage,
            'average_usage': avg_usage,
            'peak_usage': peak_usage,
            'low_usage': low_usage,
            'volatility': volatility,
            'data_points': len(values),
            'date_range': {
                'start': data[0].get('date', '') if data else '',
                'end': data[-1].get('date', '') if data else ''
            }
        }

    def get_weekly_pattern(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Get weekly usage pattern.
        
        Args:
            data: List of water usage data points
        
        Returns:
            Weekly pattern dictionary
        """
        if not data:
            return {}

        weekly_usage = defaultdict(list)
        
        for point in data:
            date_obj = point.get('date')
            if date_obj:
                if isinstance(date_obj, str):
                    date_obj = datetime.fromisoformat(date_obj)
                day_of_week = date_obj.weekday()
                weekly_usage[day_of_week].append(point.get('daily_usage', 0))

        # Calculate averages for each day
        pattern = {}
        for day, values in weekly_usage.items():
            pattern[day] = statistics.mean(values) if values else 0

        return pattern

    def get_monthly_pattern(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Get monthly usage pattern.
        
        Args:
            data: List of water usage data points
        
        Returns:
            Monthly pattern dictionary
        """
        if not data:
            return {}

        monthly_usage = defaultdict(list)
        
        for point in data:
            date_obj = point.get('date')
            if date_obj:
                if isinstance(date_obj, str):
                    date_obj = datetime.fromisoformat(date_obj)
                month_key = date_obj.strftime('%Y-%m')
                monthly_usage[month_key].append(point.get('daily_usage', 0))

        # Calculate averages for each month
        pattern = {}
        for month, values in monthly_usage.items():
            pattern[month] = statistics.mean(values) if values else 0

        return pattern

    def detect_anomalies(self, data: List[Dict[str, Any]], threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect anomalies in water usage.
        
        Args:
            data: List of water usage data points
            threshold: Z-score threshold for anomaly detection
        
        Returns:
            List of anomalies
        """
        if len(data) < 3:
            return []

        values = [d.get('daily_usage', 0) for d in data]
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 1

        anomalies = []
        for i, point in enumerate(data):
            value = point.get('daily_usage', 0)
            z_score = (value - mean) / std if std > 0 else 0
            
            if abs(z_score) > threshold:
                anomalies.append({
                    'index': i,
                    'date': point.get('date', ''),
                    'value': value,
                    'z_score': z_score,
                    'deviation': value - mean
                })

        return anomalies

    def get_usage_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get comprehensive usage summary.
        
        Args:
            data: List of water usage data points
        
        Returns:
            Usage summary dictionary
        """
        if not data:
            return {
                'total_days': 0,
                'average_daily': 0,
                'total_usage': 0,
                'max_daily': 0,
                'min_daily': 0,
                'categories': {}
            }

        values = [d.get('daily_usage', 0) for d in data]
        categories = defaultdict(float)
        
        for point in data:
            for cat, usage in point.get('categories', {}).items():
                categories[cat] += usage

        return {
            'total_days': len(data),
            'average_daily': statistics.mean(values) if values else 0,
            'total_usage': sum(values),
            'max_daily': max(values) if values else 0,
            'min_daily': min(values) if values else 0,
            'categories': dict(categories),
            'median': statistics.median(values) if values else 0,
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0
        }

    def get_projection(self, data: List[Dict[str, Any]], days: int = 30) -> Dict[str, Any]:
        """
        Get future usage projection.
        
        Args:
            data: List of water usage data points
            days: Number of days to project
        
        Returns:
            Projection data
        """
        if len(data) < 3:
            return {
                'projected_usage': 0,
                'confidence_low': 0,
                'confidence_high': 0,
                'trend': 'stable'
            }

        values = [d.get('daily_usage', 0) for d in data]
        trend = self.analyze_trends(data)
        
        # Simple linear projection
        if len(values) >= 3:
            recent_avg = statistics.mean(values[-7:]) if len(values) >= 7 else statistics.mean(values)
            if trend['trend'] == 'increasing':
                growth_rate = trend['change_percentage'] / 100
                projected = recent_avg * (1 + growth_rate * (days / 30))
            elif trend['trend'] == 'decreasing':
                reduction_rate = trend['change_percentage'] / 100
                projected = recent_avg * (1 - reduction_rate * (days / 30))
            else:
                projected = recent_avg
        else:
            projected = statistics.mean(values)

        # Confidence intervals
        std = statistics.stdev(values) if len(values) > 1 else projected * 0.1
        
        return {
            'projected_usage': projected,
            'confidence_low': max(0, projected - 1.96 * std),
            'confidence_high': projected + 1.96 * std,
            'trend': trend['trend'],
            'days_projected': days
        }

    def get_goal_progress(self, current: float, target: float) -> Dict[str, Any]:
        """
        Calculate progress towards water reduction goal.
        
        Args:
            current: Current daily usage
            target: Target daily usage
        
        Returns:
            Progress data
        """
        if target <= 0:
            return {'progress': 0, 'remaining': 0, 'percentage': 0}

        reduction_needed = current - target
        progress_percentage = ((current - reduction_needed) / current) * 100 if current > 0 else 0
        
        return {
            'current': current,
            'target': target,
            'reduction_needed': max(0, reduction_needed),
            'progress_percentage': min(100, max(0, progress_percentage)),
            'status': 'achieved' if current <= target else 'in_progress' if progress_percentage > 0 else 'not_started'
        }

    def get_comparison_insights(self, user_data: List[Dict[str, Any]], avg_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare user data with averages.
        
        Args:
            user_data: User's water usage data
            avg_data: Average usage data
        
        Returns:
            Comparison insights
        """
        if not user_data:
            return {}

        user_avg = statistics.mean([d.get('daily_usage', 0) for d in user_data])
        avg_usage = avg_data.get('average_daily', 50)

        difference = user_avg - avg_usage
        percentage = (difference / avg_usage) * 100 if avg_usage > 0 else 0

        return {
            'user_average': user_avg,
            'average_usage': avg_usage,
            'difference': difference,
            'percentage_difference': percentage,
            'status': 'below' if user_avg < avg_usage else 'above' if user_avg > avg_usage else 'equal',
            'insight': self._generate_comparison_insight(user_avg, avg_usage)
        }

    def _generate_comparison_insight(self, user_avg: float, avg_usage: float) -> str:
        """Generate insight from comparison."""
        if user_avg < avg_usage * 0.7:
            return "🌟 Excellent! Your water usage is significantly below average. Keep it up!"
        elif user_avg < avg_usage:
            return "🌿 Good job! You're below average water usage. Consider setting a new reduction goal."
        elif user_avg < avg_usage * 1.3:
            return "💧 Your water usage is close to average. Small changes can help you reduce further."
        else:
            return "⚠️ Your water usage is above average. Review our water-saving tips to reduce consumption."

    def get_peak_usage_times(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify peak usage times.
        
        Args:
            data: List of water usage data points
        
        Returns:
            Peak usage information
        """
        if not data:
            return {}

        hourly_usage = defaultdict(float)
        for point in data:
            date_obj = point.get('date')
            if date_obj:
                if isinstance(date_obj, str):
                    date_obj = datetime.fromisoformat(date_obj)
                hour = date_obj.hour
                hourly_usage[hour] += point.get('daily_usage', 0)

        # Find peak hours
        sorted_hours = sorted(hourly_usage.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'peak_hour': sorted_hours[0][0] if sorted_hours else 0,
            'peak_usage': sorted_hours[0][1] if sorted_hours else 0,
            'top_3_hours': sorted_hours[:3] if sorted_hours else [],
            'hourly_distribution': dict(hourly_usage)
        }
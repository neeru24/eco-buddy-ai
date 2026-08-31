"""
Sustainability Lifecycle & Long-Term Progress Management - Future Projections
Generates projections of future sustainability performance.
"""

import logging
import statistics
import math
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from lifecycle.models import FutureProjection, ProgressSnapshot

logger = logging.getLogger(__name__)


class ProjectionEngine:
    """
    Generates future projections based on historical data.
    """
    
    def __init__(self):
        """Initialize the projection engine."""
        self.projection_models = ['linear', 'exponential', 'moving_average']
        self.min_data_points = 10
        logger.info("Projection Engine initialized")
    
    def generate_projections(self, 
                            snapshots: List[ProgressSnapshot],
                            projection_days: int = 90,
                            projection_type: str = 'sustainability') -> List[FutureProjection]:
        """
        Generate future projections.
        
        Args:
            snapshots: List of progress snapshots
            projection_days: Number of days to project
            projection_type: Type of projection
        
        Returns:
            List[FutureProjection]: Future projections
        """
        if len(snapshots) < self.min_data_points:
            logger.warning(f"Insufficient data for projection: {len(snapshots)} points")
            return []
        
        sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
        
        projections = []
        
        # Generate projections for different metrics
        metrics = ['sustainability_score', 'carbon_footprint', 'energy_usage', 
                  'water_usage', 'waste_generation']
        
        for metric in metrics:
            if metric == projection_type or projection_type == 'all':
                projection = self._project_metric(sorted_snapshots, metric, projection_days)
                if projection:
                    projections.append(projection)
        
        return projections
    
    def _project_metric(self, 
                       snapshots: List[ProgressSnapshot],
                       metric: str,
                       days: int) -> Optional[FutureProjection]:
        """
        Project a single metric.
        
        Args:
            snapshots: Progress snapshots
            metric: Metric to project
            days: Projection days
        
        Returns:
            Optional[FutureProjection]: Projection result
        """
        values = [getattr(s, metric, 0.0) for s in snapshots]
        dates = [s.snapshot_date for s in snapshots]
        
        if len(values) < self.min_data_points:
            return None
        
        # Convert dates to numeric values (days since first)
        base_date = dates[0]
        x = [(d - base_date).days for d in dates]
        
        # Try different models and pick the best
        best_model = None
        best_accuracy = -float('inf')
        best_predictions = None
        
        for model in self.projection_models:
            try:
                predictions, accuracy = self._apply_model(model, x, values, days)
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_model = model
                    best_predictions = predictions
            except:
                continue
        
        if not best_predictions:
            return None
        
        # Create projection result
        projection = FutureProjection(
            user_id=snapshots[0].user_id,
            projection_type=metric,
            projection_date=datetime.now(),
            current_trend=best_accuracy,
            trend_confidence=0.7,
            data_points_used=len(values),
            projection_days_ahead=days,
            projection_period='days',
            model_used=best_model,
            model_accuracy=best_accuracy
        )
        
        # Set projection values
        if best_predictions:
            projection.projected_value = best_predictions[-1]['value']
            projection.target_date = datetime.now() + timedelta(days=days)
            
            # Calculate confidence interval
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            projection.confidence_interval = std_dev * 1.96  # 95% confidence
            projection.projected_value_lower = projection.projected_value - projection.confidence_interval
            projection.projected_value_upper = projection.projected_value + projection.confidence_interval
            
            # Add projected trend points
            for pred in best_predictions[:30]:  # Include first 30 days
                projection.projected_trend.append({
                    'date': (datetime.now() + timedelta(days=pred['x'])).isoformat(),
                    'value': pred['value']
                })
        
        # Check if projection is reliable
        projection.is_reliable = best_accuracy > 0.7 and len(values) > 15
        
        # Calculate estimated completion probability (for sustainability score)
        if metric == 'sustainability_score':
            target = 80.0  # Target score
            if values and values[-1] < target:
                days_needed = self._estimate_days_to_target(values, x, target)
                if days_needed:
                    projection.estimated_completion_date = datetime.now() + timedelta(days=days_needed)
                    projection.estimated_completion_probability = min(1.0, len(values) / 20)
        
        return projection
    
    def _apply_model(self, 
                    model: str,
                    x: List[float],
                    y: List[float],
                    days: int) -> tuple:
        """
        Apply a prediction model.
        
        Args:
            model: Model name
            x: X values (days)
            y: Y values (metric values)
            days: Days to predict
        
        Returns:
            tuple: (predictions, accuracy)
        """
        if model == 'linear':
            return self._linear_prediction(x, y, days)
        elif model == 'exponential':
            return self._exponential_prediction(x, y, days)
        elif model == 'moving_average':
            return self._moving_average_prediction(x, y, days)
        else:
            return self._linear_prediction(x, y, days)
    
    def _linear_prediction(self, x: List[float], y: List[float], days: int) -> tuple:
        """
        Linear regression prediction.
        """
        n = len(x)
        if n < 2:
            return [], 0
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return [], 0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate R-squared
        ss_total = sum((y[i] - y_mean) ** 2 for i in range(n))
        ss_residual = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
        
        # Predict future values
        predictions = []
        last_x = x[-1]
        for i in range(1, days + 1):
            pred_x = last_x + i
            pred_y = slope * pred_x + intercept
            predictions.append({
                'x': i,
                'value': max(0, pred_y)  # Values shouldn't be negative
            })
        
        return predictions, r_squared
    
    def _exponential_prediction(self, x: List[float], y: List[float], days: int) -> tuple:
        """
        Exponential prediction.
        """
        # Check if all values are positive
        if any(v <= 0 for v in y):
            return self._linear_prediction(x, y, days)
        
        # Transform to log space
        log_y = [math.log(v) for v in y]
        
        n = len(x)
        if n < 2:
            return [], 0
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(log_y)
        
        numerator = sum((x[i] - x_mean) * (log_y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return [], 0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate R-squared in original space
        predictions_original = []
        for i in range(n):
            pred = math.exp(slope * x[i] + intercept)
            predictions_original.append(pred)
        
        r_squared = 1 - (sum((y[i] - predictions_original[i]) ** 2 for i in range(n)) / 
                        sum((y[i] - statistics.mean(y)) ** 2 for i in range(n))) if sum((y[i] - statistics.mean(y)) ** 2 for i in range(n)) > 0 else 0
        
        # Predict future values
        predictions = []
        last_x = x[-1]
        for i in range(1, days + 1):
            pred_x = last_x + i
            pred_y = math.exp(slope * pred_x + intercept)
            predictions.append({
                'x': i,
                'value': max(0, pred_y)
            })
        
        return predictions, r_squared
    
    def _moving_average_prediction(self, x: List[float], y: List[float], days: int) -> tuple:
        """
        Moving average prediction.
        """
        window = min(7, len(y))
        if window < 2:
            return self._linear_prediction(x, y, days)
        
        # Calculate moving average
        ma = []
        for i in range(len(y)):
            start = max(0, i - window + 1)
            ma.append(statistics.mean(y[start:i+1]))
        
        # Use linear regression on moving average
        return self._linear_prediction(x, ma, days)
    
    def _estimate_days_to_target(self, 
                                values: List[float],
                                x: List[float],
                                target: float) -> Optional[float]:
        """
        Estimate days needed to reach a target.
        """
        if len(values) < 2:
            return None
        
        # Use linear regression
        slope, intercept = self._simple_linear_regression(x, values)
        
        if slope <= 0:
            return None
        
        # Solve for target
        days_needed = (target - intercept) / slope
        
        if days_needed < 0:
            return None
        
        return days_needed - x[-1]
    
    def _simple_linear_regression(self, x: List[float], y: List[float]) -> tuple:
        """
        Simple linear regression.
        """
        n = len(x)
        if n < 2:
            return 0, 0
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0, y_mean
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        return slope, intercept
    
    def get_projection_summary(self, 
                              projections: List[FutureProjection]) -> Dict[str, Any]:
        """
        Get summary of projections.
        
        Args:
            projections: List of projections
        
        Returns:
            Dict: Projection summary
        """
        if not projections:
            return {'message': 'No projections available'}
        
        summary = {
            'total_projections': len(projections),
            'reliable_projections': sum(1 for p in projections if p.is_reliable),
            'average_confidence': statistics.mean([p.trend_confidence for p in projections]) if projections else 0,
            'best_projection': max(projections, key=lambda p: p.model_accuracy) if projections else None,
            'projection_details': []
        }
        
        for projection in projections:
            summary['projection_details'].append({
                'metric': projection.projection_type,
                'current_trend': projection.current_trend,
                'projected_value': projection.projected_value,
                'target_date': projection.target_date.isoformat() if projection.target_date else None,
                'confidence': projection.confidence_interval,
                'is_reliable': projection.is_reliable,
                'model_used': projection.model_used,
                'model_accuracy': projection.model_accuracy
            })
        
        return summary
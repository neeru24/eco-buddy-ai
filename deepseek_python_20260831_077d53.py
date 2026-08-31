"""
Sustainability Analytics & Forecasting Engine - Anomaly Detector
Detects anomalies in sustainability data.
"""

import logging
import statistics
import math
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from analytics.models import (
    AnomalyDetection, AnomalyType, AnalyticsMetric,
    HistoricalData
)

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in sustainability data.
    """
    
    def __init__(self):
        """Initialize the anomaly detector."""
        self.z_score_threshold = 2.5
        self.context_window = 30  # Days
        self.anomaly_severity_thresholds = {
            'critical': 4.0,
            'high': 3.0,
            'medium': 2.0,
            'low': 1.5
        }
        logger.info("Anomaly Detector initialized")
    
    def detect_anomalies(self,
                        data: List[HistoricalData],
                        metric: AnalyticsMetric,
                        window_days: int = 30) -> List[AnomalyDetection]:
        """
        Detect anomalies in historical data.
        
        Args:
            data: Historical data
            metric: Metric to analyze
            window_days: Analysis window in days
        
        Returns:
            List[AnomalyDetection]: Detected anomalies
        """
        # Filter data for the metric
        metric_data = [d for d in data if d.metric == metric]
        
        if len(metric_data) < 5:
            logger.info(f"Insufficient data for anomaly detection: {len(metric_data)} points")
            return []
        
        # Sort by timestamp
        sorted_data = sorted(metric_data, key=lambda x: x.timestamp)
        
        # Filter recent data
        cutoff = datetime.now() - timedelta(days=window_days)
        recent_data = [d for d in sorted_data if d.timestamp >= cutoff]
        
        if len(recent_data) < 5:
            return []
        
        anomalies = []
        
        # Detect different types of anomalies
        anomalies.extend(self._detect_outliers(recent_data))
        anomalies.extend(self._detect_spikes_drops(recent_data))
        anomalies.extend(self._detect_trend_changes(recent_data))
        anomalies.extend(self._detect_seasonal_shifts(recent_data))
        
        return sorted(anomalies, key=lambda x: x.severity, reverse=True)
    
    def _detect_outliers(self, data: List[HistoricalData]) -> List[AnomalyDetection]:
        """
        Detect outlier anomalies.
        """
        anomalies = []
        values = [d.value for d in data]
        
        if len(values) < 5:
            return anomalies
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 1
        
        for i, point in enumerate(data):
            if std_dev > 0:
                z_score = (point.value - mean) / std_dev
                
                if abs(z_score) > self.z_score_threshold:
                    # Check if it's a spike or drop
                    anomaly_type = AnomalyType.SPIKE if point.value > mean else AnomalyType.DROP
                    
                    # Calculate context
                    context_start = max(0, i - 5)
                    context_end = min(len(data), i + 5)
                    context_values = [d.value for d in data[context_start:context_end] if d != point]
                    context_mean = statistics.mean(context_values) if context_values else mean
                    
                    anomaly = AnomalyDetection(
                        user_id=point.user_id,
                        metric=point.metric,
                        anomaly_type=anomaly_type,
                        value=point.value,
                        expected_value=context_mean,
                        deviation=point.value - context_mean,
                        deviation_percentage=((point.value - context_mean) / (context_mean + 0.001)) * 100,
                        z_score=z_score,
                        context_value=context_mean,
                        context_range=(min(context_values) if context_values else 0, 
                                      max(context_values) if context_values else 0),
                        explanation=self._generate_outlier_explanation(point, anomaly_type, context_mean),
                        severity=self._calculate_severity(z_score),
                        confidence=min(1.0, abs(z_score) / 5)
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_spikes_drops(self, data: List[HistoricalData]) -> List[AnomalyDetection]:
        """
        Detect sudden spikes and drops.
        """
        anomalies = []
        
        if len(data) < 5:
            return anomalies
        
        for i in range(2, len(data) - 2):
            current = data[i]
            prev = data[i-1]
            next_val = data[i+1]
            
            # Calculate rate of change
            change_from_prev = (current.value - prev.value) / (prev.value + 0.001)
            change_to_next = (next_val.value - current.value) / (current.value + 0.001)
            
            # Detect sudden spike
            if change_from_prev > 0.5 and change_to_next < -0.3:
                anomaly_type = AnomalyType.SPIKE
                
                # Calculate context
                context_values = [data[i-3].value, data[i-2].value, data[i+2].value, data[i+3].value]
                context_mean = statistics.mean(context_values) if context_values else current.value
                
                anomaly = AnomalyDetection(
                    user_id=current.user_id,
                    metric=current.metric,
                    anomaly_type=anomaly_type,
                    value=current.value,
                    expected_value=context_mean,
                    deviation=current.value - context_mean,
                    deviation_percentage=((current.value - context_mean) / (context_mean + 0.001)) * 100,
                    z_score=abs(change_from_prev),
                    context_value=context_mean,
                    explanation="Sudden spike detected in consumption",
                    severity="high",
                    confidence=0.8
                )
                anomalies.append(anomaly)
            
            # Detect sudden drop
            elif change_from_prev < -0.5 and change_to_next > 0.3:
                anomaly_type = AnomalyType.DROP
                
                context_values = [data[i-3].value, data[i-2].value, data[i+2].value, data[i+3].value]
                context_mean = statistics.mean(context_values) if context_values else current.value
                
                anomaly = AnomalyDetection(
                    user_id=current.user_id,
                    metric=current.metric,
                    anomaly_type=anomaly_type,
                    value=current.value,
                    expected_value=context_mean,
                    deviation=current.value - context_mean,
                    deviation_percentage=((current.value - context_mean) / (context_mean + 0.001)) * 100,
                    z_score=abs(change_from_prev),
                    context_value=context_mean,
                    explanation="Sudden drop detected in consumption",
                    severity="high",
                    confidence=0.8
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_trend_changes(self, data: List[HistoricalData]) -> List[AnomalyDetection]:
        """
        Detect sudden trend changes.
        """
        anomalies = []
        
        if len(data) < 10:
            return anomalies
        
        # Calculate trend for first half and second half
        mid = len(data) // 2
        
        first_half = data[:mid]
        second_half = data[mid:]
        
        if len(first_half) < 3 or len(second_half) < 3:
            return anomalies
        
        # Calculate slopes
        first_slope = self._calculate_slope(first_half)
        second_slope = self._calculate_slope(second_half)
        
        # Check for trend change
        if abs(second_slope - first_slope) > 0.1:
            # Determine if improvement or decline
            if second_slope > first_slope:
                anomaly_type = AnomalyType.TREND_CHANGE
                explanation = "Positive trend change detected - improvement in performance"
            else:
                anomaly_type = AnomalyType.TREND_CHANGE
                explanation = "Negative trend change detected - decline in performance"
            
            # Find the point of change
            change_point = data[mid]
            
            anomaly = AnomalyDetection(
                user_id=change_point.user_id,
                metric=change_point.metric,
                anomaly_type=anomaly_type,
                value=change_point.value,
                expected_value=statistics.mean([d.value for d in data]),
                deviation=change_point.value - statistics.mean([d.value for d in data]),
                deviation_percentage=((change_point.value - statistics.mean([d.value for d in data])) / 
                                    (statistics.mean([d.value for d in data]) + 0.001)) * 100,
                z_score=abs(second_slope - first_slope) * 10,
                context_value=statistics.mean([d.value for d in data]),
                explanation=explanation,
                severity="medium",
                confidence=0.7
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_seasonal_shifts(self, data: List[HistoricalData]) -> List[AnomalyDetection]:
        """
        Detect seasonal shifts.
        """
        anomalies = []
        
        if len(data) < 14:
            return anomalies
        
        # Compare same day of week or same period
        # Simplified: compare last 7 days with previous 7 days
        recent = data[-7:]
        previous = data[-14:-7]
        
        if len(recent) < 7 or len(previous) < 7:
            return anomalies
        
        recent_avg = statistics.mean([d.value for d in recent])
        previous_avg = statistics.mean([d.value for d in previous])
        
        # Check for significant shift
        if abs(recent_avg - previous_avg) / (previous_avg + 0.001) > 0.3:
            anomaly_type = AnomalyType.SEASONAL_SHIFT
            
            anomaly = AnomalyDetection(
                user_id=recent[0].user_id,
                metric=recent[0].metric,
                anomaly_type=anomaly_type,
                value=recent_avg,
                expected_value=previous_avg,
                deviation=recent_avg - previous_avg,
                deviation_percentage=((recent_avg - previous_avg) / (previous_avg + 0.001)) * 100,
                z_score=abs(recent_avg - previous_avg) / (statistics.stdev([d.value for d in data]) + 0.001),
                context_value=previous_avg,
                explanation=f"Seasonal shift detected: {recent_avg:.1f} vs {previous_avg:.1f}",
                severity="medium",
                confidence=0.6
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_slope(self, data: List[HistoricalData]) -> float:
        """
        Calculate slope of data points.
        """
        if len(data) < 2:
            return 0
        
        x = list(range(len(data)))
        y = [d.value for d in data]
        
        n = len(x)
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def _generate_outlier_explanation(self, point: HistoricalData, anomaly_type: AnomalyType, context_mean: float) -> str:
        """
        Generate explanation for outlier anomaly.
        """
        if anomaly_type == AnomalyType.SPIKE:
            return f"Unusually high value detected: {point.value:.1f} vs expected {context_mean:.1f}"
        else:
            return f"Unusually low value detected: {point.value:.1f} vs expected {context_mean:.1f}"
    
    def _calculate_severity(self, z_score: float) -> str:
        """
        Calculate severity based on z-score.
        """
        abs_z = abs(z_score)
        for severity, threshold in sorted(self.anomaly_severity_thresholds.items(), key=lambda x: x[1], reverse=True):
            if abs_z >= threshold:
                return severity
        return "low"
    
    def get_anomaly_summary(self, anomalies: List[AnomalyDetection]) -> Dict[str, Any]:
        """
        Get summary of anomalies.
        
        Args:
            anomalies: List of anomalies
        
        Returns:
            Dict: Anomaly summary
        """
        if not anomalies:
            return {
                'total': 0,
                'by_type': {},
                'by_severity': {},
                'unresolved': 0
            }
        
        by_type = {}
        by_severity = {}
        unresolved = 0
        
        for anomaly in anomalies:
            by_type[anomaly.anomaly_type.value] = by_type.get(anomaly.anomaly_type.value, 0) + 1
            by_severity[anomaly.severity] = by_severity.get(anomaly.severity, 0) + 1
            if not anomaly.is_resolved:
                unresolved += 1
        
        return {
            'total': len(anomalies),
            'by_type': by_type,
            'by_severity': by_severity,
            'unresolved': unresolved,
            'recent': sorted(anomalies, key=lambda x: x.detected_at, reverse=True)[:5]
        }
    
    def resolve_anomaly(self, anomaly: AnomalyDetection, notes: str = "") -> AnomalyDetection:
        """
        Mark an anomaly as resolved.
        
        Args:
            anomaly: Anomaly to resolve
            notes: Resolution notes
        
        Returns:
            AnomalyDetection: Resolved anomaly
        """
        anomaly.is_resolved = True
        anomaly.resolved_at = datetime.now()
        anomaly.notes = notes
        return anomaly
    
    def get_critical_anomalies(self, anomalies: List[AnomalyDetection]) -> List[AnomalyDetection]:
        """
        Get critical anomalies that need immediate attention.
        
        Args:
            anomalies: List of anomalies
        
        Returns:
            List[AnomalyDetection]: Critical anomalies
        """
        return [a for a in anomalies if a.severity in ['critical', 'high'] and not a.is_resolved]
"""
Smart Household Resource Optimization Engine - Member Analyzer
Analyzes individual member contributions to household resources.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from optimization.models import (
    MemberContribution, HouseholdResource, ResourceType
)

logger = logging.getLogger(__name__)


class MemberAnalyzer:
    """
    Analyzes individual member contributions to household resources.
    """
    
    def __init__(self):
        """Initialize the member analyzer."""
        self.activity_weights = self._initialize_activity_weights()
        self.contribution_levels = self._initialize_contribution_levels()
        logger.info("Member Analyzer initialized")
    
    def _initialize_activity_weights(self) -> Dict[str, float]:
        """
        Initialize weights for different activity types.
        """
        return {
            'individual_energy': 0.25,
            'shared_energy': 0.15,
            'individual_water': 0.15,
            'shared_water': 0.10,
            'individual_food': 0.10,
            'shared_food': 0.05,
            'individual_waste': 0.05,
            'shared_waste': 0.03,
            'individual_transport': 0.06,
            'shared_transport': 0.03,
            'individual_shopping': 0.02,
            'shared_shopping': 0.01
        }
    
    def _initialize_contribution_levels(self) -> Dict[str, float]:
        """
        Initialize contribution level thresholds.
        """
        return {
            'high': 25.0,
            'medium': 15.0,
            'low': 5.0
        }
    
    def analyze_member_contributions(self, 
                                    resources: List[HouseholdResource],
                                    members: List[Dict[str, Any]]) -> List[MemberContribution]:
        """
        Analyze member contributions.
        
        Args:
            resources: List of resources
            members: List of household members
        
        Returns:
            List[MemberContribution]: Member contributions
        """
        contributions = []
        
        for member in members:
            member_id = member.get('id', '')
            member_name = member.get('name', 'Unknown')
            
            contribution = MemberContribution(
                household_id=resources[0].household_id if resources else "",
                member_id=member_id,
                member_name=member_name
            )
            
            # Calculate individual contributions
            for resource in resources:
                key = resource.resource_type.value
                member_share = resource.member_contributions.get(member_id, 0)
                
                if member_share > 0:
                    individual = resource.current_usage * (member_share / 100)
                else:
                    individual = resource.current_usage / len(members) if members else 0
                
                # Assign to appropriate field
                if key == 'energy':
                    contribution.individual_energy = individual
                    contribution.shared_energy = resource.current_usage - individual
                elif key == 'water':
                    contribution.individual_water = individual
                    contribution.shared_water = resource.current_usage - individual
                elif key == 'food':
                    contribution.individual_food = individual
                    contribution.shared_food = resource.current_usage - individual
                elif key == 'waste':
                    contribution.individual_waste = individual
                    contribution.shared_waste = resource.current_usage - individual
                elif key == 'transportation':
                    contribution.individual_transport = individual
                    contribution.shared_transport = resource.current_usage - individual
                elif key == 'shopping':
                    contribution.individual_shopping = individual
                    contribution.shared_shopping = resource.current_usage - individual
            
            # Calculate totals
            contribution.total_energy = contribution.individual_energy + contribution.shared_energy
            contribution.total_water = contribution.individual_water + contribution.shared_water
            contribution.total_food = contribution.individual_food + contribution.shared_food
            contribution.total_waste = contribution.individual_waste + contribution.shared_waste
            contribution.total_transport = contribution.individual_transport + contribution.shared_transport
            contribution.total_shopping = contribution.individual_shopping + contribution.shared_shopping
            
            # Category contributions
            contribution.category_contributions = {
                'energy': contribution.total_energy,
                'water': contribution.total_water,
                'food': contribution.total_food,
                'waste': contribution.total_waste,
                'transport': contribution.total_transport,
                'shopping': contribution.total_shopping
            }
            
            # Calculate household impact percentage
            total_household = sum(r.current_usage for r in resources)
            total_member = (contribution.total_energy + contribution.total_water + 
                           contribution.total_food + contribution.total_waste + 
                           contribution.total_transport + contribution.total_shopping)
            
            if total_household > 0:
                contribution.household_impact_percentage = (total_member / total_household) * 100
            
            # Find improvement opportunities
            contribution.improvement_opportunities = self._find_improvement_opportunities(
                contribution, resources, members
            )
            
            # Determine contribution rank
            contribution.contribution_rank = self._determine_rank(contribution, members, resources)
            
            contributions.append(contribution)
        
        return contributions
    
    def _find_improvement_opportunities(self, 
                                       contribution: MemberContribution,
                                       resources: List[HouseholdResource],
                                       members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find improvement opportunities for a member.
        """
        opportunities = []
        
        # Check if member's usage is above average
        avg_usage = self._calculate_average_usage(resources, members)
        
        if contribution.total_energy > avg_usage.get('energy', 0) * 1.2:
            opportunities.append({
                'category': 'energy',
                'current': contribution.total_energy,
                'average': avg_usage.get('energy', 0),
                'potential_savings': contribution.total_energy - avg_usage.get('energy', 0),
                'recommendation': 'Reduce energy usage by turning off lights and electronics',
                'effort': 'low'
            })
        
        if contribution.total_water > avg_usage.get('water', 0) * 1.2:
            opportunities.append({
                'category': 'water',
                'current': contribution.total_water,
                'average': avg_usage.get('water', 0),
                'potential_savings': contribution.total_water - avg_usage.get('water', 0),
                'recommendation': 'Take shorter showers and fix leaks',
                'effort': 'medium'
            })
        
        if contribution.total_waste > avg_usage.get('waste', 0) * 1.2:
            opportunities.append({
                'category': 'waste',
                'current': contribution.total_waste,
                'average': avg_usage.get('waste', 0),
                'potential_savings': contribution.total_waste - avg_usage.get('waste', 0),
                'recommendation': 'Increase recycling and reduce waste',
                'effort': 'low'
            })
        
        if contribution.total_transport > avg_usage.get('transport', 0) * 1.2:
            opportunities.append({
                'category': 'transport',
                'current': contribution.total_transport,
                'average': avg_usage.get('transport', 0),
                'potential_savings': contribution.total_transport - avg_usage.get('transport', 0),
                'recommendation': 'Use public transit or carpool',
                'effort': 'medium'
            })
        
        if contribution.total_shopping > avg_usage.get('shopping', 0) * 1.2:
            opportunities.append({
                'category': 'shopping',
                'current': contribution.total_shopping,
                'average': avg_usage.get('shopping', 0),
                'potential_savings': contribution.total_shopping - avg_usage.get('shopping', 0),
                'recommendation': 'Reduce unnecessary purchases',
                'effort': 'medium'
            })
        
        return sorted(opportunities, key=lambda x: x['potential_savings'], reverse=True)
    
    def _calculate_average_usage(self, 
                                resources: List[HouseholdResource],
                                members: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate average usage per member.
        """
        avg = {}
        member_count = len(members) or 1
        
        for resource in resources:
            key = resource.resource_type.value
            avg[key] = resource.current_usage / member_count
        
        return avg
    
    def _determine_rank(self, 
                       contribution: MemberContribution,
                       members: List[Dict[str, Any]],
                       resources: List[HouseholdResource]) -> int:
        """
        Determine contribution rank.
        """
        total_contributions = []
        
        for member in members:
            member_id = member.get('id', '')
            member_total = 0
            
            for resource in resources:
                member_share = resource.member_contributions.get(member_id, 0)
                if member_share > 0:
                    member_total += resource.current_usage * (member_share / 100)
                else:
                    member_total += resource.current_usage / len(members)
            
            total_contributions.append((member_id, member_total))
        
        sorted_contributions = sorted(total_contributions, key=lambda x: x[1], reverse=True)
        
        for rank, (member_id, _) in enumerate(sorted_contributions, 1):
            if member_id == contribution.member_id:
                return rank
        
        return 0
    
    def get_member_rankings(self, 
                           contributions: List[MemberContribution],
                           category: str = 'total_energy') -> List[Dict[str, Any]]:
        """
        Get member rankings by category.
        
        Args:
            contributions: List of member contributions
            category: Category to rank by
        
        Returns:
            List[Dict]: Rankings
        """
        sorted_contributions = sorted(
            contributions,
            key=lambda x: getattr(x, category, 0),
            reverse=True
        )
        
        rankings = []
        for idx, contribution in enumerate(sorted_contributions, 1):
            rankings.append({
                'rank': idx,
                'member_name': contribution.member_name,
                'value': getattr(contribution, category, 0),
                'percentage': contribution.household_impact_percentage,
                'improvement_opportunities': contribution.improvement_opportunities[:2]
            })
        
        return rankings
    
    def get_member_summary(self, 
                          contribution: MemberContribution) -> Dict[str, Any]:
        """
        Get summary for a member.
        
        Args:
            contribution: Member contribution
        
        Returns:
            Dict: Member summary
        """
        return {
            'member_name': contribution.member_name,
            'total_energy': contribution.total_energy,
            'total_water': contribution.total_water,
            'total_food': contribution.total_food,
            'total_waste': contribution.total_waste,
            'total_transport': contribution.total_transport,
            'total_shopping': contribution.total_shopping,
            'individual_energy': contribution.individual_energy,
            'shared_energy': contribution.shared_energy,
            'household_impact': contribution.household_impact_percentage,
            'contribution_rank': contribution.contribution_rank,
            'improvement_opportunities': len(contribution.improvement_opportunities),
            'biggest_improvement': contribution.improvement_opportunities[0]['recommendation'] if contribution.improvement_opportunities else 'None',
            'category_breakdown': contribution.category_contributions,
            'contribution_level': self._get_contribution_level(contribution.household_impact_percentage)
        }
    
    def _get_contribution_level(self, percentage: float) -> str:
        """
        Get contribution level.
        """
        if percentage >= self.contribution_levels['high']:
            return 'high'
        elif percentage >= self.contribution_levels['medium']:
            return 'medium'
        elif percentage >= self.contribution_levels['low']:
            return 'low'
        else:
            return 'very_low'
    
    def get_household_breakdown(self, 
                               contributions: List[MemberContribution]) -> Dict[str, Any]:
        """
        Get household breakdown by member.
        
        Args:
            contributions: List of member contributions
        
        Returns:
            Dict: Household breakdown
        """
        total_usage = {
            'energy': 0.0,
            'water': 0.0,
            'food': 0.0,
            'waste': 0.0,
            'transport': 0.0,
            'shopping': 0.0
        }
        
        for contribution in contributions:
            total_usage['energy'] += contribution.total_energy
            total_usage['water'] += contribution.total_water
            total_usage['food'] += contribution.total_food
            total_usage['waste'] += contribution.total_waste
            total_usage['transport'] += contribution.total_transport
            total_usage['shopping'] += contribution.total_shopping
        
        member_breakdown = []
        for contribution in contributions:
            member_breakdown.append({
                'name': contribution.member_name,
                'energy_percentage': (contribution.total_energy / (total_usage['energy'] + 0.001)) * 100,
                'water_percentage': (contribution.total_water / (total_usage['water'] + 0.001)) * 100,
                'food_percentage': (contribution.total_food / (total_usage['food'] + 0.001)) * 100,
                'waste_percentage': (contribution.total_waste / (total_usage['waste'] + 0.001)) * 100,
                'transport_percentage': (contribution.total_transport / (total_usage['transport'] + 0.001)) * 100,
                'shopping_percentage': (contribution.total_shopping / (total_usage['shopping'] + 0.001)) * 100,
                'overall_percentage': contribution.household_impact_percentage,
                'rank': contribution.contribution_rank
            })
        
        return {
            'total_usage': total_usage,
            'member_breakdown': member_breakdown,
            'top_contributors': self.get_member_rankings(contributions, 'total_energy')[:3],
            'contribution_distribution': self._get_contribution_distribution(contributions)
        }
    
    def _get_contribution_distribution(self, 
                                      contributions: List[MemberContribution]) -> Dict[str, int]:
        """
        Get distribution of contribution levels.
        """
        distribution = {'high': 0, 'medium': 0, 'low': 0, 'very_low': 0}
        
        for contribution in contributions:
            level = self._get_contribution_level(contribution.household_impact_percentage)
            distribution[level] += 1
        
        return distribution
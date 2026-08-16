"""Utility functions for Assessment History advanced search."""

import pandas as pd
from typing import Dict, Any

def filter_assessments(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter and sort an assessments DataFrame based on user criteria.
    
    Args:
        df: Pandas DataFrame containing assessment records.
        filters: Dictionary containing filter criteria:
            - keyword: str (search in transport, diet, factor_version)
            - date_range: tuple of (start_date, end_date)
            - eco_score_range: tuple of (min_score, max_score)
            - sort_by: str ("Date", "Eco Score", "Carbon Footprint")
            - sort_order: str ("Ascending", "Descending")
            
    Returns:
        pd.DataFrame: A new filtered and sorted DataFrame.
    """
    if df.empty:
        return df.copy()

    filtered_df = df.copy()
    
    # 1. Keyword search (case-insensitive)
    keyword = filters.get("keyword", "").strip().lower()
    if keyword:
        # Search across transport, diet, and factor_version
        cols_to_search = ["transport", "diet", "factor_version"]
        mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        for col in cols_to_search:
            if col in filtered_df.columns:
                mask |= filtered_df[col].astype(str).str.lower().str.contains(keyword, na=False)
        filtered_df = filtered_df[mask]
        
    # 2. Date range
    date_range = filters.get("date_range")
    if date_range and len(date_range) == 2 and "date" in filtered_df.columns:
        start_date, end_date = date_range
        # Ensure 'date' column is datetime
        filtered_df['parsed_date'] = pd.to_datetime(filtered_df['date']).dt.date
        filtered_df = filtered_df[
            (filtered_df['parsed_date'] >= start_date) & 
            (filtered_df['parsed_date'] <= end_date)
        ]
        filtered_df = filtered_df.drop(columns=['parsed_date'])
        
    # 3. Eco Score range
    eco_score_range = filters.get("eco_score_range")
    if eco_score_range and len(eco_score_range) == 2 and "eco_score" in filtered_df.columns:
        min_score, max_score = eco_score_range
        # Handle cases where eco_score might be null
        mask_notna = filtered_df["eco_score"].notna()
        mask_range = (filtered_df["eco_score"] >= min_score) & (filtered_df["eco_score"] <= max_score)
        filtered_df = filtered_df[mask_notna & mask_range]
        
    # 4. Sorting
    sort_by = filters.get("sort_by", "Date")
    sort_order = filters.get("sort_order", "Descending")
    
    ascending = sort_order == "Ascending"
    
    col_map = {
        "Date": "date",
        "Eco Score": "eco_score",
        "Carbon Footprint": "footprint"
    }
    
    sort_col = col_map.get(sort_by)
    if sort_col and sort_col in filtered_df.columns:
        # Using mergesort for stability
        filtered_df = filtered_df.sort_values(by=sort_col, ascending=ascending, kind="mergesort")
        
    return filtered_df

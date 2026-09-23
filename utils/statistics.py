"""
Statistical analysis utilities for the videogame market analysis project.
"""

import numpy as np
import pandas as pd
try:
    from scipy import stats as scipy_stats
except ImportError:
    scipy_stats = None

def descriptive_stats(data) -> dict:
    """
    Computes descriptive statistics for a given dataset.
    
    Args:
        data (np.ndarray or pd.Series): The numerical data to analyze.
        
    Returns:
        dict: A dictionary containing mean, median, mode, std, variance, min, max, 
              range, q1, q3, iqr, skewness, kurtosis, cv, count, and count_nonzero.
    """
    arr = np.asarray(data)
    # Remove NaNs for calculations if any
    arr = arr[~np.isnan(arr)]
    
    count = arr.size
    if count == 0:
        return {}
    
    count_nonzero = np.count_nonzero(arr)
    mean = np.mean(arr)
    median = np.median(arr)
    std = np.std(arr, ddof=1) if count > 1 else 0.0
    variance = np.var(arr, ddof=1) if count > 1 else 0.0
    minimum = np.min(arr)
    maximum = np.max(arr)
    data_range = maximum - minimum
    
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1
    
    cv = (std / mean) if mean != 0 else np.nan
    
    if scipy_stats is not None:
        mode_res = scipy_stats.mode(arr, keepdims=False)
        mode = mode_res.mode
        skewness = scipy_stats.skew(arr)
        kurtosis = scipy_stats.kurtosis(arr)
    else:
        # Manual mode
        vals, counts = np.unique(arr, return_counts=True)
        mode = vals[np.argmax(counts)]
        
        # Manual skewness and kurtosis
        if std > 0:
            skewness = np.mean(((arr - mean) / std) ** 3)
            kurtosis = np.mean(((arr - mean) / std) ** 4) - 3
        else:
            skewness = np.nan
            kurtosis = np.nan
            
    return {
        'mean': mean,
        'median': median,
        'mode': mode,
        'std': std,
        'variance': variance,
        'min': minimum,
        'max': maximum,
        'range': data_range,
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'skewness': skewness,
        'kurtosis': kurtosis,
        'cv': cv,
        'count': count,
        'count_nonzero': count_nonzero
    }

def correlation_analysis(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Calculates the Pearson correlation matrix for specified columns.
    
    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        columns (list): A list of column names to include in the correlation matrix.
        
    Returns:
        pd.DataFrame: A correlation matrix for the specified columns.
    """
    return df[columns].corr(method='pearson')

def top_correlations(corr_matrix: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Extracts the top N strongest correlations (by absolute value) from a correlation matrix.
    
    Args:
        corr_matrix (pd.DataFrame): The correlation matrix.
        n (int): The number of top correlations to return.
        
    Returns:
        pd.DataFrame: A DataFrame with columns ['variable_1', 'variable_2', 'correlation'].
    """
    # Get the upper triangle of the correlation matrix without the diagonal
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Stack the matrix to get a Series with a MultiIndex
    stacked = upper_tri.stack().reset_index()
    stacked.columns = ['variable_1', 'variable_2', 'correlation']
    
    # Calculate absolute correlation for sorting
    stacked['abs_corr'] = stacked['correlation'].abs()
    
    # Sort by absolute correlation in descending order and take top n
    top_n = stacked.sort_values(by='abs_corr', ascending=False).head(n)
    
    # Drop the absolute correlation column
    return top_n.drop(columns=['abs_corr']).reset_index(drop=True)

def outlier_detection(data, method: str = 'iqr') -> np.ndarray:
    """
    Detects outliers in a dataset using the specified method.
    
    Args:
        data (np.ndarray or pd.Series): The numerical data to analyze.
        method (str): The method to use for detection ('iqr' or 'zscore').
        
    Returns:
        np.ndarray: A boolean array where True indicates an outlier.
    """
    arr = np.asarray(data)
    
    if method == 'iqr':
        q1 = np.nanpercentile(arr, 25)
        q3 = np.nanpercentile(arr, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = (arr < lower_bound) | (arr > upper_bound)
    elif method == 'zscore':
        mean = np.nanmean(arr)
        std = np.nanstd(arr, ddof=1)
        if std == 0:
            outliers = np.zeros_like(arr, dtype=bool)
        else:
            z_scores = np.abs((arr - mean) / std)
            outliers = z_scores > 3
    else:
        raise ValueError("Method must be 'iqr' or 'zscore'")
        
    return outliers

def regional_dominance(na_sales, jp_sales, pal_sales, other_sales) -> str:
    """
    Determines which region has the highest sales for a game.
    
    Args:
        na_sales (float): Sales in North America.
        jp_sales (float): Sales in Japan.
        pal_sales (float): Sales in PAL regions.
        other_sales (float): Sales in other regions.
        
    Returns:
        str: The region with the highest sales ('NA', 'JP', 'PAL', or 'Other').
    """
    sales = {
        'NA': na_sales if not pd.isna(na_sales) else 0,
        'JP': jp_sales if not pd.isna(jp_sales) else 0,
        'PAL': pal_sales if not pd.isna(pal_sales) else 0,
        'Other': other_sales if not pd.isna(other_sales) else 0
    }
    
    if all(v == 0 for v in sales.values()):
        return 'Unknown'
        
    return max(sales, key=sales.get)

def normalize_minmax(data: np.ndarray) -> np.ndarray:
    """
    Performs Min-Max normalization on a dataset.
    
    Args:
        data (np.ndarray): The numerical data to normalize.
        
    Returns:
        np.ndarray: The normalized data scaled between 0 and 1.
    """
    arr = np.asarray(data)
    minimum = np.nanmin(arr)
    maximum = np.nanmax(arr)
    
    if minimum == maximum:
        return np.zeros_like(arr, dtype=float)
        
    return (arr - minimum) / (maximum - minimum)

def calculate_success_score(owners: float, review_ratio: float, pct_positive: float, peak_ccu: float, weights: dict = None) -> float:
    """
    Calculates a composite success index based on normalized metrics.
    
    Args:
        owners (float): Normalized estimated owners (0-1).
        review_ratio (float): Normalized review ratio (0-1).
        pct_positive (float): Normalized percentage of positive reviews (0-1).
        peak_ccu (float): Normalized peak concurrent users (0-1).
        weights (dict, optional): Custom weights for each metric. Defaults to None.
        
    Returns:
        float: The calculated composite success score.
    """
    if weights is None:
        weights = {
            'owners': 0.4,
            'review_ratio': 0.2,
            'pct_positive': 0.2,
            'peak_ccu': 0.2
        }
        
    score = (
        owners * weights.get('owners', 0) +
        review_ratio * weights.get('review_ratio', 0) +
        pct_positive * weights.get('pct_positive', 0) +
        peak_ccu * weights.get('peak_ccu', 0)
    )
    
    return score

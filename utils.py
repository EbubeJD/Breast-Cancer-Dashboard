"""Shared utilities for METABRIC dashboard."""

from typing import Tuple, Optional, List, Dict, Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go


# ============= Style Constants =============

COLORS = {
    "primary": "#1f77b4",
    "success": "#2ca02c",
    "warning": "#ff7f0e",
    "danger": "#d62728",
    "gray_light": "#f5f5f5",
    "gray_dark": "#555",
    "text_secondary": "#666",
    "border": "#ddd",
    "shadow": "0 1px 2px rgba(0,0,0,0.08)",
}

CARD_STYLE = {
    "backgroundColor": "white",
    "padding": "15px 20px",
    "borderRadius": "8px",
    "boxShadow": COLORS["shadow"],
    "minWidth": "180px",
}

CONTAINER_STYLE = {
    "padding": "25px",
}

CHART_CONTAINER = {
    "backgroundColor": "white",
    "padding": "10px",
    "borderRadius": "8px",
    "boxShadow": COLORS["shadow"],
}

LAYOUT_MARGINS = dict(l=60, r=20, t=60, b=60)
LAYOUT_MARGINS_TALL = dict(l=80, r=20, t=80, b=80)


# ============= Data Processing =============

def parse_mutation_status(df: pd.DataFrame, mut_col: str, sentinel_values: set) -> pd.Series:
    """
    Convert mutation column to binary (mutated=True, not mutated=False).

    Args:
        df: DataFrame containing mutation column
        mut_col: Column name
        sentinel_values: Set of values representing "not mutated" (e.g., {"0", "nan", ""})

    Returns:
        Boolean Series where True = mutated
    """
    if mut_col not in df.columns:
        return pd.Series([False] * len(df), index=df.index)

    col_str = df[mut_col].astype(str).str.strip()
    return ~col_str.isin(sentinel_values)


def compute_mutation_statistics(
    df: pd.DataFrame,
    mut_col: str,
    sentinel_values: set,
    filter_col: Optional[str] = None,
    filter_values: Optional[list] = None,
) -> Tuple[int, int, float]:
    """
    Compute mutation statistics for a given column with optional filtering.

    Returns:
        (n_mutated, n_total, percentage)
    """
    sub_df = df.copy()

    # Apply filter if provided
    if filter_col and filter_values and filter_col in sub_df.columns:
        sub_df = sub_df[sub_df[filter_col].isin(filter_values)]

    mutated_mask = parse_mutation_status(sub_df, mut_col, sentinel_values)
    n_total = len(sub_df)
    n_mutated = mutated_mask.sum()
    pct = (n_mutated / n_total * 100) if n_total > 0 else 0

    return n_mutated, n_total, pct


def get_figure_y_max(fig: go.Figure) -> Optional[float]:
    """Extract max y value from Plotly figure traces."""
    max_y = None

    for trace in fig.data:
        y = getattr(trace, "y", None)
        if y is None:
            continue

        try:
            this_max = max(y)
            max_y = this_max if max_y is None else max(max_y, this_max)
        except Exception:
            continue

    return max_y


def set_figure_y_axis(fig: go.Figure, scale_factor: float = 1.25) -> go.Figure:
    """
    Auto-scale y-axis with padding above max value.

    Args:
        fig: Plotly figure
        scale_factor: Multiplier for padding (1.25 = 25% above max)

    Returns:
        Modified figure
    """
    max_y = get_figure_y_max(fig)
    if max_y is not None:
        fig.update_yaxes(range=[0, max_y * scale_factor])
    return fig


def compute_percentages(groupby_result: pd.DataFrame, count_col: str = "count") -> pd.DataFrame:
    """
    Compute percentages from grouped data.

    Expected input: DataFrame with 'sum' and 'count' columns (from agg).
    """
    if "sum" in groupby_result.columns and count_col in groupby_result.columns:
        groupby_result["pct"] = (
            groupby_result["sum"] / groupby_result[count_col] * 100
        ).round(1)
    return groupby_result


# ============= Validation =============

def validate_column_exists(df: pd.DataFrame, col: str, context: str = "") -> bool:
    """
    Validate that column exists. Log warning if not.

    Args:
        df: DataFrame
        col: Column name to check
        context: Description of what was being attempted

    Returns:
        True if column exists, False otherwise
    """
    if col not in df.columns:
        if context:
            print(f"WARNING: Column '{col}' not found ({context})")
        else:
            print(f"WARNING: Column '{col}' not found")
        return False
    return True


def validate_non_empty(df: pd.DataFrame, context: str = "") -> bool:
    """Check if DataFrame is non-empty."""
    is_empty = df.empty
    if is_empty and context:
        print(f"WARNING: DataFrame is empty ({context})")
    return not is_empty


def safe_copy(df: pd.DataFrame) -> pd.DataFrame:
    """Create safe copy of DataFrame (modifying won't affect original)."""
    return df.copy()


# ============= Empty Figure Helpers =============

def empty_figure(title: str, height: int = 320) -> go.Figure:
    """Create empty placeholder figure."""
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=height,
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


# ============= Event Mapping =============

def map_cancer_event(value: Any) -> int:
    """
    Map cancer event column to binary (1=death from cancer, 0=other/unknown).

    Args:
        value: Value from death_from_cancer column

    Returns:
        1 if death from cancer, 0 otherwise
    """
    v = str(value).strip().lower()

    if v in ("", "nan", "none"):
        return 0

    # Numeric values
    if v in {"1", "yes", "y", "true"}:
        return 1
    if v in {"0", "no", "n", "false"}:
        return 0

    # Textual descriptions
    if "died" in v and "disease" in v:
        return 1  # Died of disease -> cancer-specific
    if "died" in v:
        return 0  # Died of other causes
    if "living" in v or "alive" in v:
        return 0

    return 0


# ============= Data Type Conversions =============

def to_numeric_safe(df: pd.DataFrame, cols: List[str], fill_method: str = "median") -> pd.DataFrame:
    """
    Safely convert columns to numeric, handle missing values.

    Args:
        df: Input DataFrame
        cols: Columns to convert
        fill_method: How to fill NaNs ("median", "mean", "drop")

    Returns:
        DataFrame with numeric columns
    """
    result = df.copy()
    result[cols] = result[cols].apply(pd.to_numeric, errors="coerce")

    if fill_method == "median":
        result[cols] = result[cols].fillna(result[cols].median())
    elif fill_method == "mean":
        result[cols] = result[cols].fillna(result[cols].mean())
    elif fill_method == "drop":
        result = result.dropna(subset=cols)

    return result

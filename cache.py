"""Caching layer for expensive computations."""

from functools import lru_cache, wraps
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any, Callable
import time
import warnings

warnings.filterwarnings("ignore", message="DataFrame is highly fragmented")

# Global cache storage
_cache_store: Dict[str, Any] = {}
_cache_stats: Dict[str, Dict[str, int]] = {}


class CacheStats:
    """Track cache hit/miss statistics."""

    def __init__(self, name: str):
        self.name = name
        self.hits = 0
        self.misses = 0
        self.total_time_saved = 0.0

    def record_hit(self, duration: float):
        """Record a cache hit and time saved."""
        self.hits += 1
        self.total_time_saved += duration

    def record_miss(self):
        """Record a cache miss."""
        self.misses += 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate (0-1)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

    def __repr__(self):
        total = self.hits + self.misses
        rate = self.hit_rate * 100
        return (f"CacheStats({self.name}): {self.hits}/{total} hits "
                f"({rate:.1f}%), {self.total_time_saved:.2f}s saved")


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments.
    Handles DataFrames, numpy arrays, and primitives.
    """
    key_parts = []

    # Process positional args
    for arg in args:
        if isinstance(arg, pd.DataFrame):
            # Use hash of dataframe structure + shape (not content for speed)
            key_parts.append(f"df_{id(arg)}")
        elif isinstance(arg, np.ndarray):
            key_parts.append(f"arr_{arg.shape}_{arg.dtype}")
        elif isinstance(arg, (list, tuple)):
            key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        else:
            key_parts.append(str(arg))

    # Process kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, pd.DataFrame):
            key_parts.append(f"{k}=df_{id(v)}")
        else:
            key_parts.append(f"{k}={v}")

    full_key = "|".join(key_parts)
    return hashlib.md5(full_key.encode()).hexdigest()[:16]


def cached(name: str, ttl: int = None):
    """
    Decorator for caching function results.

    Args:
        name: Cache name (for statistics)
        ttl: Time-to-live in seconds (None = no expiration)

    Usage:
        @cached("mutation_matrix")
        def get_mutation_matrix(df, sentinel_values):
            return expensive_computation(df, sentinel_values)
    """
    def decorator(func: Callable) -> Callable:
        stats = CacheStats(name)
        _cache_stats[name] = stats

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = cache_key(*args, **kwargs)
            cache_entry = key in _cache_store

            if cache_entry:
                start_time = time.time()
                result = _cache_store[key]
                duration = time.time() - start_time
                stats.record_hit(duration)
                return result

            # Cache miss - compute result
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            _cache_store[key] = result
            stats.record_miss()

            return result

        wrapper.cache_stats = stats
        wrapper.clear_cache = lambda: _cache_store.clear()
        return wrapper

    return decorator


def clear_cache():
    """Clear all cached data."""
    global _cache_store
    _cache_store.clear()


def clear_cache_for(name: str):
    """Clear cache entries for a specific function."""
    # Find and remove entries (simplified - in production use better key management)
    clear_cache()


def get_cache_stats():
    """Get all cache statistics."""
    return _cache_stats.copy()


def print_cache_stats():
    """Pretty-print cache statistics."""
    print("\n" + "="*60)
    print("CACHE STATISTICS")
    print("="*60)
    for name, stats in _cache_stats.items():
        print(f"{stats}")
    print("="*60 + "\n")


# ============= Cached Computations =============

@cached("mutation_binary_matrix", ttl=3600)
def get_mutation_binary_matrix(
    df: pd.DataFrame,
    mutation_cols: list,
    sentinel_values: set
) -> pd.DataFrame:
    """
    Cache binary mutation matrix (mutated=1, not mutated=0).

    This is expensive because it:
    - Converts all columns to strings
    - Strips whitespace
    - Compares against sentinel values

    Expensive: ~500-1000ms for large datasets
    """
    from utils import parse_mutation_status

    cols_data = {}
    for col in mutation_cols:
        cols_data[col] = parse_mutation_status(df, col, sentinel_values)
    return pd.DataFrame(cols_data, index=df.index).astype(int)


@cached("correlation_matrix", ttl=1800)
def get_correlation_matrix(
    df: pd.DataFrame,
    cols: list,
    method: str = "pearson"
) -> pd.DataFrame:
    """
    Cache correlation matrix.

    Expensive: ~200-500ms for many columns
    """
    numeric_df = df[cols].apply(pd.to_numeric, errors="coerce")
    numeric_df = numeric_df.dropna(axis=1, how="all")
    numeric_df = numeric_df.fillna(numeric_df.median())
    return numeric_df.corr(method=method)


@cached("numeric_matrix", ttl=1800)
def get_numeric_matrix(
    df: pd.DataFrame,
    cols: list
) -> pd.DataFrame:
    """
    Cache numeric conversion and preprocessing.

    Expensive: ~100-200ms for many columns
    """
    numeric_df = df[cols].apply(pd.to_numeric, errors="coerce")
    numeric_df = numeric_df.dropna(axis=1, how="all")
    numeric_df = numeric_df.fillna(numeric_df.median())
    return numeric_df


@cached("pca_results", ttl=1800)
def get_pca_results(
    X_scaled: np.ndarray,
    n_components: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Cache PCA results (transformation + variance).

    Expensive: ~300-800ms for large matrices
    """
    from sklearn.decomposition import PCA

    pca = PCA(n_components=n_components, random_state=0)
    X_pca = pca.fit_transform(X_scaled)
    return X_pca, pca.explained_variance_ratio_


@cached("kmeans_results", ttl=1800)
def get_kmeans_results(
    X_pca: np.ndarray,
    k: int,
    n_dims: int
) -> Tuple[np.ndarray, float]:
    """
    Cache KMeans clustering results.

    Expensive: ~200-500ms for large datasets
    """
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    kmeans = KMeans(n_clusters=k, n_init=10, random_state=0)
    cluster_labels = kmeans.fit_predict(X_pca[:, :n_dims])

    try:
        sil_score = silhouette_score(X_pca[:, :n_dims], cluster_labels)
    except Exception:
        sil_score = np.nan

    return cluster_labels, sil_score


# ============= Cache Management =============

class CacheManager:
    """Intelligent cache manager with dependency tracking."""

    def __init__(self):
        self.dependencies: Dict[str, set] = {}
        self.cache_enabled = True

    def enable(self):
        """Enable caching."""
        self.cache_enabled = True

    def disable(self):
        """Disable caching (useful for testing)."""
        self.cache_enabled = False
        clear_cache()

    def invalidate_dependent(self, source_cache: str):
        """Invalidate all caches that depend on a source cache."""
        if source_cache in self.dependencies:
            dependent_caches = self.dependencies[source_cache]
            for cache_name in dependent_caches:
                clear_cache_for(cache_name)

    def add_dependency(self, source: str, dependent: str):
        """Register that 'dependent' depends on 'source'."""
        if source not in self.dependencies:
            self.dependencies[source] = set()
        self.dependencies[source].add(dependent)


# Global cache manager
cache_manager = CacheManager()

# Register dependencies
cache_manager.add_dependency("mutation_binary_matrix", "correlation_matrix")
cache_manager.add_dependency("numeric_matrix", "pca_results")
cache_manager.add_dependency("numeric_matrix", "kmeans_results")

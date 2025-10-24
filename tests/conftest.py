"""
Pytest configuration for vectorbt-workspace tests

Adds the workspace root directory to sys.path so tests can import
modules from utils/, core/, data/, etc.

Fixtures:
- data_5min: Fetches SPY 5-minute data for January 2024 (shared across tests)
- data_daily: Fetches SPY daily data for January 2024 (shared across tests)
"""

import sys
from pathlib import Path
import pytest

# Add workspace root to Python path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))


@pytest.fixture(scope="session")
def data_5min():
    """
    Fetch SPY 5-minute data for January 2024.

    Uses session scope to fetch data once and reuse across all tests.
    This reduces API calls and speeds up test execution.

    Returns:
        pd.DataFrame: 5-minute OHLCV data with DatetimeIndex
    """
    from strategies.orb import ORBStrategy, ORBConfig

    config = ORBConfig(
        name="ORB Test",
        symbol='SPY',
        start_date='2024-01-01',
        end_date='2024-01-31'  # Single month for fast testing
    )

    strategy = ORBStrategy(config)
    data_5min, data_daily = strategy.fetch_data()

    return data_5min


@pytest.fixture(scope="session")
def data_daily():
    """
    Fetch SPY daily data for January 2024.

    Uses session scope to fetch data once and reuse across all tests.

    Returns:
        pd.DataFrame: Daily OHLCV data with DatetimeIndex
    """
    from strategies.orb import ORBStrategy, ORBConfig

    config = ORBConfig(
        name="ORB Test",
        symbol='SPY',
        start_date='2024-01-01',
        end_date='2024-01-31'
    )

    strategy = ORBStrategy(config)
    data_5min, data_daily = strategy.fetch_data()

    return data_daily

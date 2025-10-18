# VectorBT PRO

> VectorBT PRO is a next-generation, proprietary Python engine that implements SOTA data-science and acceleration tools to make backtesting, algorithmic trading, and quantitative analysis both lightning-fast and easy-to-use.
> A high-performance successor to the open-source vectorbt package, it represents every trading setup as multidimensional arrays, letting you sweep millions of parameter combinations at C speed while analyzing results with familiar Python tools.
> The library breaks a strategy into modular "Lego-like" components--data, indicators, signals, allocations, portfolios--so you can examine each piece, plug in ML models at any stage, and run CV with ease, while features such as chunking keep even massive studies RAM-efficient.

## Getting started

- [Introduction](/index.md): Learn how to install VectorBT PRO, grasp its design and workflow, follow recommended learning steps, access exclusive resources and community Discord server, and navigate tutorials, features, and API.
- [Installation Guide](https://vectorbt.pro/pvt_41531c19/getting-started/installation.md): Install VectorBT PRO via pip, Git, or Docker, with authentication setup, environment configuration, OS-specific tips, and troubleshooting advice.

## Features

- [Feature Overview](https://vectorbt.pro/pvt_41531c19/features/overview.md): Explore VectorBT PRO enhancements with links to detailed sections.
- [Analysis Tools](https://vectorbt.pro/pvt_41531c19/features/analysis.md): Utilize advanced tools such as trade-range simulation, expanding trade metrics, trade signal plotting, edge ratio, trade history inspection, pattern detection, projection analysis, MAE/MFE evaluation, OHLC handling, and benchmark setting.
- [Data Handling](https://vectorbt.pro/pvt_41531c19/features/data.md): Access, transform, merge, and save market data from diverse sources (synthetic data generation, local files, remote APIs, databases), including parallel fetching and SQL querying, and run indicators on it.
- [Indicators](https://vectorbt.pro/pvt_41531c19/features/indicators.md): Apply advanced indicators such as Hurst exponent, Smart Money Concepts, signal unraveling, pivot and Renko detection, rolling regressions, multi-timeframe TA-Lib functions, indicator expressions, WorldQuant Alphas, and robust crossovers.
- [Optimization](https://vectorbt.pro/pvt_41531c19/features/optimization.md): Optimize strategies with purged CV, parameter handling and filtering, random search, batch parameter processing, portfolio optimization, and advanced splitters.
- [Performance Optimization](https://vectorbt.pro/pvt_41531c19/features/performance.md): Accelerate computations through chunk caching, accumulators, chunking for distributed execution, Numba parallelization, multithreading, multiprocessing, jitting, caching management, and hyperfast rolling metrics.
- [Portfolio Management](https://vectorbt.pro/pvt_41531c19/features/portfolio.md): Manage portfolios with asset weighting, leverage, position views, flexible stop orders, order delays, dynamic callbacks, cash handling, in-place simulation outputs, and performance optimizations.
- [Productivity Tools](https://vectorbt.pro/pvt_41531c19/features/productivity.md): Boost productivity via source refinement, fast offline search, interactive chat, task execution, progress bars, data operations, serialization, resampling, annotations, profiling, and templated function extension.

## Tutorials

- [Tutorial Overview](https://vectorbt.pro/pvt_41531c19/tutorials/overview.md): Explore VectorBT PRO tutorials with links to detailed sections.
- [Basic RSI Strategy](https://vectorbt.pro/pvt_41531c19/tutorials/basic-rsi.md): Backtest a basic RSI strategy in VectorBT PRO, covering data loading, indicator computation, signal generation, portfolio modeling, and parameter optimization.
- [Stop Signals](https://vectorbt.pro/pvt_41531c19/tutorials/stop-signals.md): Compare stop-loss, trailing stop, take-profit, random exit, and holding strategies across cryptocurrencies using large-scale backtesting and interactive dashboards.
- [Pairs Trading](https://vectorbt.pro/pvt_41531c19/tutorials/pairs-trading.md): Develop and optimize statistical arbitrage pairs trades using cointegration screening, z-score signals, and fast parameter sweeps for improved speed and memory efficiency.
- [Additional Resources](https://vectorbt.pro/pvt_41531c19/tutorials/more-tutorials.md): Explore partner tutorials, videos, newsletters, and research on quantitative analytics, machine learning, and strategy development.

## Tutorials > SuperFast SuperTrend

- [SuperTrend Indicator](https://vectorbt.pro/pvt_41531c19/tutorials/superfast-supertrend/index.md): Build and optimize a high-performance SuperTrend indicator in Python with Pandas, NumPy, Numba, and TA-Lib, then visualize and backtest it.
- [SuperTrend Streaming](https://vectorbt.pro/pvt_41531c19/tutorials/superfast-supertrend/streaming.md): Implement a single-pass streaming SuperTrend indicator using accumulators for real-time, memory-efficient computation.
- [SuperTrend Multithreading](https://vectorbt.pro/pvt_41531c19/tutorials/superfast-supertrend/multithreading.md): Accelerate Numba-compiled SuperTrend runs via Dask multithreading while explaining GIL constraints and multiprocessing contrasts.
- [SuperTrend Pipelines](https://vectorbt.pro/pvt_41531c19/tutorials/superfast-supertrend/pipelines.md): Design modular, chunked, Numba-compiled backtesting pipelines for SuperTrend with custom simulators and maximum speed.

## Tutorials > Signal Development

- [Signal Generation](https://vectorbt.pro/pvt_41531c19/tutorials/signal-development/generation.md): Generate trading signals using boolean masks, crossovers, shifting, rolling windows, parameter combinations, and custom iterative or preset generators.
- [Signal Pre-Analysis](https://vectorbt.pro/pvt_41531c19/tutorials/signal-development/pre-analysis.md): Rank, clean, and analyze signal distributions and durations to detect issues before simulation.

## Tutorials > MTF Analysis

- [MTF Analysis](https://vectorbt.pro/pvt_41531c19/tutorials/mtf-analysis/index.md): Perform multi-time-frame analysis by resampling OHLCV data to reveal broader trends and key patterns.
- [MTF Alignment](https://vectorbt.pro/pvt_41531c19/tutorials/mtf-analysis/alignment.md): Realign resampled OHLC data across time frames to avoid look-ahead bias and build synchronized multi-time-frame strategies.
- [MTF Aggregation](https://vectorbt.pro/pvt_41531c19/tutorials/mtf-analysis/aggregation.md): Aggregate and resample time series with advanced alignment, bounds handling, and meta methods for metrics like drawdown.

## Tutorials > Portfolio Optimization

- [Portfolio Optimization](https://vectorbt.pro/pvt_41531c19/tutorials/portfolio-optimization/index.md): Construct and optimize multi-asset portfolios with diverse allocation methods, templates, parameter groups, and high-performance simulations.
- [Portfolio Optimization Integrations](https://vectorbt.pro/pvt_41531c19/tutorials/portfolio-optimization/integrations.md): Integrate PyPortfolioOpt, Riskfolio-Lib, and Universal Portfolios for automated argument parsing, custom objectives, constraints, and periodic rebalancing.
- [Dynamic Portfolio Optimization](https://vectorbt.pro/pvt_41531c19/tutorials/portfolio-optimization/dynamic.md): Implement threshold rebalancing, periodic mean-variance optimization, and chunked simulations for dynamic portfolio evaluation.

## Tutorials > Patterns and Projections

- [Pattern Matching](https://vectorbt.pro/pvt_41531c19/tutorials/patterns-and-projections/patterns.md): Identify and match price patterns via interpolation, similarity measures, rolling searches, and composite techniques.
- [Pattern Projections](https://vectorbt.pro/pvt_41531c19/tutorials/patterns-and-projections/projections.md): Extract and visualize post-pattern price projections to assess statistical impacts without full backtests.

## Tutorials > Cross-Validation

- [Cross-Validation Overview](https://vectorbt.pro/pvt_41531c19/tutorials/cross-validation/index.md): Split historical data into training and validation periods, optimize in-sample, and evaluate out-of-sample performance to prevent overfitting.
- [Cross-Validation Splitter](https://vectorbt.pro/pvt_41531c19/tutorials/cross-validation/splitter.md): Generate, validate, and refine rolling, expanding, anchored, random, and scikit-learn-style time-series splits.
- [Cross-Validation Applications](https://vectorbt.pro/pvt_41531c19/tutorials/cross-validation/applications.md): Apply splitters to slice data, run parameterized strategies, bootstrap results, integrate ML, and automate workflows.

## Documentation

- [Documentation Overview](https://vectorbt.pro/pvt_41531c19/documentation/overview.md): Explore VectorBT PRO documentation with links to detailed sections.
- [Fundamentals](https://vectorbt.pro/pvt_41531c19/documentation/fundamentals.md): Understand vectorized backtesting foundations--NumPy, Pandas accessors, Numba, multidimensional arrays, hierarchical columns, broadcasting, and flexible indexing.
- [Building Blocks](https://vectorbt.pro/pvt_41531c19/documentation/building-blocks.md): Learn configuration, pickling, data wrapping, indexing, grouping, analysis, and templating concepts that enable extensible high-performance classes, with a custom example focused on correlation statistics.

## Documentation > Data

- [Data Management](https://vectorbt.pro/pvt_41531c19/documentation/data/index.md): Manage multi-symbol financial time-series by fetching, updating, aligning, transforming, resampling, and plotting data from diverse sources.
- [Local Data](https://vectorbt.pro/pvt_41531c19/documentation/data/local.md): Store and update datasets locally in formats such as Pickle, CSV, HDF, Feather, Parquet, SQL, and DuckDB using partitioning and chunking.
- [Remote Data](https://vectorbt.pro/pvt_41531c19/documentation/data/remote.md): Fetch and cache remote financial data via API clients with authentication, rate limiting, batching, timeframe selection, and cloud or URL sources.
- [Synthetic Data](https://vectorbt.pro/pvt_41531c19/documentation/data/synthetic.md): Generate realistic synthetic price and return series using customizable statistical generators like Lévy alpha-stable distributions.
- [Data Scheduling](https://vectorbt.pro/pvt_41531c19/documentation/data/scheduling.md): Automate periodic data fetching and incremental saving with real-time visualization, duplicate handling, resuming interrupted saving processes, and custom destinations.

## Documentation > Indicators

- [Indicators](https://vectorbt.pro/pvt_41531c19/documentation/indicators/index.md): Build parameterizable, analyzable indicators with pipelines and factories, broadcasted parameter grids, and built-in analysis tools.
- [Indicator Development](https://vectorbt.pro/pvt_41531c19/documentation/indicators/development.md): Develop custom indicators with advanced parameter handling, broadcasting, caching, stacking, and performance optimizations.
- [Indicator Analysis](https://vectorbt.pro/pvt_41531c19/documentation/indicators/analysis.md): Analyze indicators by combining signals, selecting by parameters or time, computing metrics, plotting subplots, and extending methods.
- [Indicator Parsers](https://vectorbt.pro/pvt_41531c19/documentation/indicators/parsers.md): Create indicators via TA-Lib, Pandas TA, expressions, and advanced parser features including resampling, custom functions, and stacking.

## Documentation > Portfolio

- [Portfolio Simulation](https://vectorbt.pro/pvt_41531c19/documentation/portfolio/index.md): Simulate and analyze portfolios with low-level API, including flexible order commands, long-short support, leverage, grouping, context managers, and optimized pipelines.
- [Order-Based Portfolios](https://vectorbt.pro/pvt_41531c19/documentation/portfolio/from-orders.md): Backtest portfolios from predefined order arrays with grouping, cash sharing, initial states, processing control, and jit-enabled performance.
- [Signal-Based Portfolios](https://vectorbt.pro/pvt_41531c19/documentation/portfolio/from-signals.md): Backtest portfolios driven by dynamic signals with limit/stop orders, accumulation, size types, execution options, grouping, and custom behavior.

## Cookbook

- [Cookbook Overview](https://vectorbt.pro/pvt_41531c19/cookbook/overview.md): Explore VectorBT PRO cookbook with links to detailed sections.
- [Array Operations](https://vectorbt.pro/pvt_41531c19/cookbook/arrays.md): Manipulate arrays and DataFrames--convert between NumPy and Pandas, create shape-matched empties, and cross-join multiple frames.
- [Benchmarking](https://vectorbt.pro/pvt_41531c19/cookbook/benchmarking.md): Measure execution time and peak memory of code blocks with single-run or multi-run profiling.
- [Caching](https://vectorbt.pro/pvt_41531c19/cookbook/caching.md): Control caching--clear caches, view stats, toggle globally or in scopes, and manage object-level settings.
- [Compilation](https://vectorbt.pro/pvt_41531c19/cookbook/compilation.md): Toggle Numba compilation via environment variables or config and verify its status.
- [Configuration](https://vectorbt.pro/pvt_41531c19/cookbook/configuration.md): Configure objects--copy, modify, save, load, and override nested settings through files or environment variables.
- [Cross-Validation](https://vectorbt.pro/pvt_41531c19/cookbook/cross-validation.md): Perform time-series cross-validation with flexible windows, gaps, buffers, grid search, and metric-based selection.
- [Data Management](https://vectorbt.pro/pvt_41531c19/cookbook/data.md): Manage financial data--list, fetch, save, update, manipulate, and extract datasets from multiple sources.
- [Datetime Operations](https://vectorbt.pro/pvt_41531c19/cookbook/datetime.md): Create and manipulate timezone-aware timestamps, spans, and calendar offsets using human-readable strings.
- [Discovery Tools](https://vectorbt.pro/pvt_41531c19/cookbook/discovery.md): Inspect Python objects--view arguments, list attributes, pretty-print contents, and open online references.
- [Indexing Methods](https://vectorbt.pro/pvt_41531c19/cookbook/indexing.md): Select and modify data using label, positional, date-range, and compound indexing with VectorBT PRO helpers.
- [Indicators](https://vectorbt.pro/pvt_41531c19/cookbook/indicators.md): Manage technical indicators--list, retrieve, run, parallelize, and register custom or built-in indicators.
- [Knowledge Management](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge.md): Work with knowledge assets--load, query, aggregate, format, browse, search, chat with LLMs, and build RAG pipelines.
- [Optimization](https://vectorbt.pro/pvt_41531c19/cookbook/optimization.md): Optimize functions and pipelines with parameter grids, chunking, parallel execution, and dynamic skipping for efficiency.
- [Persistence](https://vectorbt.pro/pvt_41531c19/cookbook/persistence.md): Serialize Python objects to compressed pickle files and reload them with version-safe reconstruction.
- [Plotting](https://vectorbt.pro/pvt_41531c19/cookbook/plotting.md): Visualize data--build diverse plots, style figures, handle gaps, manage subplots, set themes, and export interactively or statically.
- [Portfolio Simulation](https://vectorbt.pro/pvt_41531c19/cookbook/portfolio.md): Simulate and analyze portfolios from OHLC data, signals, or multiple strategies with customizable execution, stops, sizing, and parallelization.
- [Signal Processing](https://vectorbt.pro/pvt_41531c19/cookbook/signals.md): Clean multiple signal arrays simultaneously using performance-optimized custom functions.

## API

- [API Index](https://vectorbt.pro/pvt_41531c19/api/index.md): Package-level index summarizing core components, default imports, inspection helpers, and links to subpackages and modules.
- [Settings](https://vectorbt.pro/pvt_41531c19/api/_settings.md): Global settings object governing default behavior and customization across VectorBT PRO.
- [Optional Dependencies](https://vectorbt.pro/pvt_41531c19/api/_opt_deps.md): Configuration mapping of optional third-party packages with sources, version constraints, and distribution names.
- [Data Types](https://vectorbt.pro/pvt_41531c19/api/_dtypes.md): Collection of default float and integer data types with helper methods for precise numeric computation.
- [Root Accessors](https://vectorbt.pro/pvt_41531c19/api/accessors.md): Pandas accessor namespaces providing signal, returns, OHLCV, and Plotly Express utilities.

## API > Base

- [Base Index](https://vectorbt.pro/pvt_41531c19/api/base/index.md): Index of subpackages and modules for Pandas broadcasting, alignment, and other base operations.
- [Base Accessors](https://vectorbt.pro/pvt_41531c19/api/base/accessors.md): Custom Pandas accessors for alignment, broadcasting, combining, and stacking on Series, DataFrames, and Indexes.
- [Chunking](https://vectorbt.pro/pvt_41531c19/api/base/chunking.md): Extensions for flexibly slicing, mapping, and sizing array and group chunks using chunk metadata.
- [Combining](https://vectorbt.pro/pvt_41531c19/api/base/combining.md): Functions for merging and concatenating NumPy arrays with custom or JIT-compiled combiners.
- [Class Decorators](https://vectorbt.pro/pvt_41531c19/api/base/decorators.md): Class decorators that inject or modify argument configurations for base preparer subclasses.
- [Flexible Indexing](https://vectorbt.pro/pvt_41531c19/api/base/flex_indexing.md): Functions enabling flexible element and subarray selection in 1D/2D arrays using broadcasting and rotational strategies.
- [Indexes](https://vectorbt.pro/pvt_41531c19/api/base/indexes.md): Tools for manipulating, aligning, stacking, combining, and cleaning Pandas Index and MultiIndex levels.
- [Indexing](https://vectorbt.pro/pvt_41531c19/api/base/indexing.md): Classes and functions resolving labels, positions, datetime parts, ranges, and masks to flexible indexers for arrays and DataFrames.
- [Merging](https://vectorbt.pro/pvt_41531c19/api/base/merging.md): Functions for concatenating and stacking array-like objects into unified structures.
- [Preparing](https://vectorbt.pro/pvt_41531c19/api/base/preparing.md): Classes and helpers for configuring target functions, broadcasting arguments, and processing datetimes.
- [Reshaping](https://vectorbt.pro/pvt_41531c19/api/base/reshaping.md): Functions and classes for broadcasting, dimensional conversion, index alignment, and unstacking of arrays and Pandas objects.
- [Wrapping](https://vectorbt.pro/pvt_41531c19/api/base/wrapping.md): Utilities for wrapping NumPy arrays into Pandas objects with metadata handling for indexing, grouping, stacking, and reshaping.

## API > Base > Grouping

- [Grouping Index](https://vectorbt.pro/pvt_41531c19/api/base/grouping/index.md): Index of subpackages and modules for grouping functionality.
- [Grouping Base](https://vectorbt.pro/pvt_41531c19/api/base/grouping/base.md): Base classes and utilities for creating, modifying, and querying Pandas group metadata.
- [Numba Functions](https://vectorbt.pro/pvt_41531c19/api/base/grouping/nb.md): Numba-compiled functions for group sizing, mapping, splitting, and selection on arrays.

## API > Base > Resampling

- [Resampling Index](https://vectorbt.pro/pvt_41531c19/api/base/resampling/index.md): Index of subpackages and modules for resampling functionality.
- [Resampling Base](https://vectorbt.pro/pvt_41531c19/api/base/resampling/base.md): Foundational class with methods for converting and mapping between source and target time indices.
- [Numba Functions](https://vectorbt.pro/pvt_41531c19/api/base/resampling/nb.md): Numba-compiled functions for generating date ranges, index mapping, and mask alignment during datetime resampling.

## API > Data

- [Data Index](https://vectorbt.pro/pvt_41531c19/api/data/index.md): Index of subpackages and modules for data management.
- [Data Base](https://vectorbt.pro/pvt_41531c19/api/data/base.md): Base classes and dictionaries for fetching, updating, transforming, aligning, and plotting feature- and symbol-oriented financial data.
- [Class Decorators](https://vectorbt.pro/pvt_41531c19/api/data/decorators.md): Class decorators that add symbol-dictionary management methods to data subclasses.
- [Numba Functions](https://vectorbt.pro/pvt_41531c19/api/data/nb.md): Numba-compiled functions for synthesizing financial data via cumulative returns and Geometric Brownian Motion.
- [Data Saver](https://vectorbt.pro/pvt_41531c19/api/data/saver.md): Classes for scheduling and executing data exports to CSV, HDF, SQL, DuckDB, and more.
- [Data Updater](https://vectorbt.pro/pvt_41531c19/api/data/updater.md): Utilities for scheduling and executing periodic data updates.

## API > Data > Custom

- [Custom Data Index](https://vectorbt.pro/pvt_41531c19/api/data/custom/index.md): Index of subpackages and modules with custom data classes.
- [Alpaca Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/alpaca.md): Class to fetch Alpaca market data--symbol lists, client resolution across asset types, and stock, crypto, and options retrieval.
- [Alpha Vantage Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/av.md): Class to query Alpha Vantage for financial and economic data with dynamic request construction.
- [Databento Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/bento.md): Class to access Databento data--symbol metadata, cost estimates, and customizable client connections.
- [Binance Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/binance.md): Class to fetch Binance cryptocurrency data--symbol lists and historical prices with configurable options.
- [CCXT Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/ccxt.md): Class wrapper around CCXT for exchange configuration, symbol retrieval, and earliest timestamp discovery.
- [CSV Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/csv.md): Class to validate, resolve keys, and read CSV or TSV files.
- [Custom Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/custom.md): Class providing access to user-defined datasets via the custom settings path.
- [Database Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/db.md): Class to retrieve and manipulate database-stored data within VectorBT PRO.
- [DuckDB Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/duckdb.md): Class to query DuckDB databases--table pulls, SQL execution, and file import.
- [Feather Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/feather.md): Class to load Feather-format datasets through PyArrow.
- [File System Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/file.md): Class to fetch files from local storage.
- [Finpy Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/finpy.md): Class to obtain financial data via findatapy--symbol listing, filtering, and market/source configuration.
- [GBM Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/gbm.md): Class to generate geometric Brownian motion series with configurable start value, drift, volatility, and time step.
- [Synthetic OHLC Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/gbm_ohlc.md): Class to create synthetic OHLC prices from GBM with adjustable drift, volatility, and seed.
- [HDF Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/hdf.md): Class to work with HDF files via PyTables--retrieve, update, and validate objects by feature or symbol.
- [Local Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/local.md): Class to access and manage locally stored datasets through a uniform interface.
- [Nasdaq Data Link Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/ndl.md): Class to fetch datasets and datatables from Nasdaq Data Link with symbol, date, and format options.
- [Parquet Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/parquet.md): Class to read Parquet files via PyArrow or FastParquet.
- [Polygon Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/polygon.md): Class to access Polygon API for symbols and historical data across stocks, crypto, and FX with timeframe and date filters.
- [Random Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/random.md): Class to generate random dataframes with custom index, columns, statistics, and seed.
- [Random OHLC Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/random_ohlc.md): Class to generate randomized OHLC series with controllable start value, drift, volatility, and randomness.
- [Remote Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/remote.md): Class to fetch structured data from remote sources.
- [SQL Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/sql.md): Class to interact with SQL databases via SQLAlchemy--engine management, schema/table access, and CRUD by feature or symbol.
- [Synthetic Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/synthetic.md): Class framework to create and update synthetic datasets for features and symbols.
- [TradingView Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/tv.md): Client and data classes for TradingView authentication, search, scanning, and historical market data via web or WebSocket.
- [Yahoo Finance Data](https://vectorbt.pro/pvt_41531c19/api/data/custom/yf.md): Class to retrieve Yahoo Finance market data--prices, volume, dividends, and splits.

## API > Generic

- [Generic Index](https://vectorbt.pro/pvt_41531c19/api/generic/index.md): Index of subpackages and modules for generic time-series manipulation and analysis.
- [Generic Accessors](https://vectorbt.pro/pvt_41531c19/api/generic/accessors.md): Pandas Series/DataFrame accessors adding generic manipulation, statistical, and plotting methods.
- [Analyzable](https://vectorbt.pro/pvt_41531c19/api/generic/analyzable.md): Array-wrapper class for computing and visualizing data attributes.
- [Class Decorators](https://vectorbt.pro/pvt_41531c19/api/generic/decorators.md): Decorators that inject generic transformation and optimized computation methods into accessor classes.
- [Drawdown Records](https://vectorbt.pro/pvt_41531c19/api/generic/drawdowns.md): Tools for capturing, analyzing, filtering, and plotting drawdown intervals in time series.
- [Generic Enums](https://vectorbt.pro/pvt_41531c19/api/generic/enums.md): Named tuples and enums defining error types, interpolation modes, rolling states, and pattern statuses.
- [Plots Builder](https://vectorbt.pro/pvt_41531c19/api/generic/plots_builder.md): Mixin for assembling multi-subplot figures and configuring their components.
- [Plotting](https://vectorbt.pro/pvt_41531c19/api/generic/plotting.md): Core Plotly helpers for bar, box, gauge, heatmap, histogram, scatter, and volume charts in Jupyter.
- [Price Records](https://vectorbt.pro/pvt_41531c19/api/generic/price_records.md): Base class for handling and analyzing OHLC price records.
- [Range Records](https://vectorbt.pro/pvt_41531c19/api/generic/ranges.md): Utilities for creating, manipulating, analyzing, and visualizing interval records such as ranges and pattern matches.
- [Stats Builder](https://vectorbt.pro/pvt_41531c19/api/generic/stats_builder.md): Mixin for computing, filtering, grouping, and aggregating performance metrics.
- [Simulation Range](https://vectorbt.pro/pvt_41531c19/api/generic/sim_range.md): Mixin for resolving, indexing, resampling, and combining simulation start and end positions.

## API > Generic > Numba

- [Generic Numba Index](https://vectorbt.pro/pvt_41531c19/api/generic/nb/index.md): Index of subpackages and modules with Numba-compiled functions for generic data processing in backtests and indicators.
- [Apply-Reduce Functions](https://vectorbt.pro/pvt_41531c19/api/generic/nb/apply_reduce.md): Numba-compiled kernels for apply, map, and reduce operations with group-by, rolling, and frequency support.
- [Base Functions](https://vectorbt.pro/pvt_41531c19/api/generic/nb/base.md): Numba-compiled utilities for filling, shifting, ranking, cumulative stats, crossing detection, and other array operations.
- [Iterative Functions](https://vectorbt.pro/pvt_41531c19/api/generic/nb/iter_.md): Numba-compiled routines for detecting iterative relationships between two-dimensional array values.
- [Patterns](https://vectorbt.pro/pvt_41531c19/api/generic/nb/patterns.md): Numba-compiled functions for resizing, interpolating, fitting, and comparing one-dimensional numerical patterns.
- [Records](https://vectorbt.pro/pvt_41531c19/api/generic/nb/records.md): Numba-compiled helpers for handling and analyzing range, drawdown, and pattern-match records.
- [Rolling Functions](https://vectorbt.pro/pvt_41531c19/api/generic/nb/rolling.md): Numba-compiled implementations of rolling and expanding window statistics, correlations, regressions, and pattern similarity.
- [Simulation Range](https://vectorbt.pro/pvt_41531c19/api/generic/nb/sim_range.md): Numba-compiled routines for preparing and resolving grouped or ungrouped simulation ranges.

## API > Generic > Splitting

- [Splitting Index](https://vectorbt.pro/pvt_41531c19/api/generic/splitting/index.md): Index of subpackages and modules for splitting data.
- [Splitting Base](https://vectorbt.pro/pvt_41531c19/api/generic/splitting/base.md): Core classes for defining ranges, managing split collections, applying functions, and generating splits.
- [Splitting Decorators](https://vectorbt.pro/pvt_41531c19/api/generic/splitting/decorators.md): Decorators that perform data splitting with cross-validation and parameterized execution.
- [Numba Functions](https://vectorbt.pro/pvt_41531c19/api/generic/splitting/nb.md): Numba-compiled functions for overlap matrices and mask-based range splitting in multidimensional arrays.
- [Purged CV](https://vectorbt.pro/pvt_41531c19/api/generic/splitting/purged.md): Classes implementing purged time-series cross-validation to prevent leakage.
- [Sklearn CV](https://vectorbt.pro/pvt_41531c19/api/generic/splitting/sklearn_.md): Scikit-learn compatible cross-validator for configurable data splitting and grouping.

## API > Indicators

- [Indicator Index](https://vectorbt.pro/pvt_41531c19/api/indicators/index.md): Index of subpackages and modules for building and executing technical indicators.
- [Indicator Configurations](https://vectorbt.pro/pvt_41531c19/api/indicators/configs.md): Configuration objects for column-wise, element-wise, and row-wise indicator parameters.
- [Indicator Enums](https://vectorbt.pro/pvt_41531c19/api/indicators/enums.md): Named tuples and enums for trend directions, pivot points, Hurst methods, and Super Trend states.
- [Indicator Expressions](https://vectorbt.pro/pvt_41531c19/api/indicators/expr.md): Functions for evaluating time-series expressions, cross-sectional operations, and predefined alpha formulas.
- [Indicator Factory](https://vectorbt.pro/pvt_41531c19/api/indicators/factory.md): Tools for creating indicator classes from functions, expressions, and external libraries.
- [Numba Indicators](https://vectorbt.pro/pvt_41531c19/api/indicators/nb.md): Numba-compiled kernels for computing custom indicators and statistics on price and volume arrays.
- [TA-Lib Integration](https://vectorbt.pro/pvt_41531c19/api/indicators/talib_.md): Helpers for applying TA-Lib indicators and generating their plots.

## API > Indicators > Custom

- [Custom Indicator Index](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/index.md): Index of subpackages and modules with custom indicators built with the indicator factory.
- [ADX](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/adx.md): Class computing Average Directional Index to quantify trend strength.
- [ATR](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/atr.md): Class computing Average True Range to measure price volatility.
- [Bollinger Bands](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/bbands.md): Class generating Bollinger Bands volatility envelopes.
- [Hurst Exponent](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/hurst.md): Class computing rolling Hurst exponent for long-term memory assessment.
- [Moving Average](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/ma.md): Class computing moving average with comparison, statistics, and plotting utilities.
- [MACD](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/macd.md): Class computing Moving Average Convergence Divergence for momentum analysis.
- [Mean Squared Deviation](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/msd.md): Class computing rolling mean squared deviation as a volatility metric with analysis helpers.
- [OBV](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/obv.md): Class computing On-Balance Volume accumulation with comparison, statistics, and plotting.
- [OLS Regression](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/ols.md): Class performing rolling OLS regression to track evolving linear relationships.
- [Pattern Similarity](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/patsim.md): Class computing rolling pattern similarity to compare templates against series.
- [Pivot Info](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/pivotinfo.md): Class extracting confirmed and last pivot points with customizable metrics.
- [RSI](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/rsi.md): Class computing Relative Strength Index to gauge overbought or oversold momentum.
- [Signal Detection](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/sigdet.md): Class detecting peaks via a robust z-score algorithm with dynamic thresholds and visualization.
- [Stochastic Oscillator](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/stoch.md): Class computing Stochastic Oscillator to compare close price to recent range.
- [Supertrend](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/supertrend.md): Class computing Supertrend overlay delivering volatility-adjusted buy/sell signals.
- [VWAP](https://vectorbt.pro/pvt_41531c19/api/indicators/custom/vwap.md): Class computing resettable Volume-Weighted Average Price for intraday price-volume analysis.

## API > Knowledge

- [Knowledge Utility Index](https://vectorbt.pro/pvt_41531c19/api/knowledge/index.md): Index of subpackages and modules for building and managing knowledge assets.
- [Asset Pipelines](https://vectorbt.pro/pvt_41531c19/api/knowledge/asset_pipelines.md): Classes for composing and executing knowledge-asset processing pipelines from simple chains to nested expressions.
- [Base Asset Functions](https://vectorbt.pro/pvt_41531c19/api/knowledge/base_asset_funcs.md): Abstract classes enabling retrieval, modification, search, transformation, and aggregation operations on knowledge assets.
- [Base Assets](https://vectorbt.pro/pvt_41531c19/api/knowledge/base_assets.md): Foundational classes for caching, querying, transforming, and embedding knowledge-asset collections.
- [Completions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions.md): Classes and utilities for generating chat completions across backends with streaming, token-aware context templating, thought-tag processing, MCP/function calling, message history handling, and formatter integration.
- [Custom Asset Functions](https://vectorbt.pro/pvt_41531c19/api/knowledge/custom_asset_funcs.md): Specialized aggregators and converters that merge messages, threads, blocks, or channels and output Markdown or HTML.
- [Custom Assets](https://vectorbt.pro/pvt_41531c19/api/knowledge/custom_assets.md): Handlers for website pages, APIs, Discord messages, and code samples that support search, ranking, aggregation, browsing, and chat-based queries.
- [Document Ranking & Embedding](https://vectorbt.pro/pvt_41531c19/api/knowledge/doc_ranking.md): Classes and helpers to embed and rank documents using embeddings, BM25, or hybrid RRF; with chunking, cached stores, configurable scoring, top‑k/cutoff selection, and chat-aware mixins.
- [Document Storing](https://vectorbt.pro/pvt_41531c19/api/knowledge/doc_storing.md): Classes and utilities for representing documents and embeddings and managing object stores (dict, in-memory, file, LMDB, cached) with templating, text splitting, patch-based persistence, mirroring, and commit/close semantics.
- [Embeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings.md): Abstract base classes and utilities for obtaining text embeddings from various providers with batch support, automatic provider resolution, and unified API.
- [Formatting Tools](https://vectorbt.pro/pvt_41531c19/api/knowledge/formatting.md): Utilities to convert between Markdown and HTML, render in IPython, and generate static HTML files.
- [Text Splitting](https://vectorbt.pro/pvt_41531c19/api/knowledge/text_splitting.md): Classes and utilities for configurable document chunking by tokens, segments, or structured sources (code/Markdown), with overlap control, templating, and pluggable backends.
- [Tokenization Utilities](https://vectorbt.pro/pvt_41531c19/api/knowledge/tokenization.md): Abstract and concrete classes, along with helper functions, for tokenizing and detokenizing text, supporting multiple tokenization backends.

## API > Labels

- [Label Index](https://vectorbt.pro/pvt_41531c19/api/labels/index.md): Index of subpackages and modules for trend label generation.
- [Label Enums](https://vectorbt.pro/pvt_41531c19/api/labels/enums.md): Named tuples and enums defining modes for trend label generation.
- [Numba Generators](https://vectorbt.pro/pvt_41531c19/api/labels/nb.md): Numba-compiled functions that create trend and breakout labels from 1D/2D price data with configurable thresholds.

## API > Labels > Generators

- [Label Generator Index](https://vectorbt.pro/pvt_41531c19/api/labels/generators/index.md): Index of subpackages and modules with basic look-ahead indicators and label generators built with the indicator factory.
- [Breakout Labels](https://vectorbt.pro/pvt_41531c19/api/labels/generators/bolb.md): Class that computes and analyzes breakout labels from future high-low price moves.
- [Fixed Labels](https://vectorbt.pro/pvt_41531c19/api/labels/generators/fixlb.md): Class that produces fixed look-ahead labels from future price changes with analytics and plotting.
- [Future Maximum](https://vectorbt.pro/pvt_41531c19/api/labels/generators/fmax.md): Class that yields future maximum close prices with comparison, statistics, and plotting utilities.
- [Future Mean](https://vectorbt.pro/pvt_41531c19/api/labels/generators/fmean.md): Class that calculates future mean values with parameter sweeps, stats, and plots.
- [Future Minimum](https://vectorbt.pro/pvt_41531c19/api/labels/generators/fmin.md): Class that derives future rolling minima with comparison and analysis tools.
- [Future Std Dev](https://vectorbt.pro/pvt_41531c19/api/labels/generators/fstd.md): Class that measures future standard deviation to assess upcoming volatility.
- [Pivot Labels](https://vectorbt.pro/pvt_41531c19/api/labels/generators/pivotlb.md): Class that detects future pivot points from high-low thresholds.
- [Mean Labels](https://vectorbt.pro/pvt_41531c19/api/labels/generators/meanlb.md): Class that assigns look-ahead mean-change labels with compute, compare, and plot methods.
- [Trend Labels](https://vectorbt.pro/pvt_41531c19/api/labels/generators/trendlb.md): Class that labels future trends via threshold-based high-low analysis across multiple modes.

## API > OHLCV

- [OHLCV Index](https://vectorbt.pro/pvt_41531c19/api/ohlcv/index.md): Index of subpackages and modules for OHLC(V) data management.
- [OHLCV Accessors](https://vectorbt.pro/pvt_41531c19/api/ohlcv/accessors.md): Pandas accessors for resampling, summarizing, and plotting OHLC(V) data.
- [OHLCV Enums](https://vectorbt.pro/pvt_41531c19/api/ohlcv/enums.md): Named tuples and enums representing OHLC(V) price features.
- [Numba Functions](https://vectorbt.pro/pvt_41531c19/api/ohlcv/nb.md): Numba-compiled utilities for aggregating and transforming 1D/2D OHLCV arrays.

## API > Portfolio

- [Portfolio Index](https://vectorbt.pro/pvt_41531c19/api/portfolio/index.md): Index of subpackages and modules for portfolio simulation and management.
- [Portfolio Base](https://vectorbt.pro/pvt_41531c19/api/portfolio/base.md): Base class for constructing, analyzing, and visualizing simulated portfolios.
- [Call Sequence](https://vectorbt.pro/pvt_41531c19/api/portfolio/call_seq.md): Functions that create and manipulate grouped call-sequence arrays.
- [Portfolio Chunking](https://vectorbt.pro/pvt_41531c19/api/portfolio/chunking.md): Functions that merge portfolio simulation outputs across chunks.
- [Class Decorators](https://vectorbt.pro/pvt_41531c19/api/portfolio/decorators.md): Decorators adding specialized methods to portfolio classes.
- [Portfolio Enums](https://vectorbt.pro/pvt_41531c19/api/portfolio/enums.md): Named tuples and enums for orders, trades, positions, and simulation states.
- [Log Records](https://vectorbt.pro/pvt_41531c19/api/portfolio/logs.md): Accessors for portfolio simulation logs with statistics and filtering.
- [Order Records](https://vectorbt.pro/pvt_41531c19/api/portfolio/orders.md): Tools for accessing, analyzing, and plotting filled order records.
- [Preparing Simulation](https://vectorbt.pro/pvt_41531c19/api/portfolio/preparing.md): Classes that configure and preprocess portfolio simulation parameters.
- [Trade Records](https://vectorbt.pro/pvt_41531c19/api/portfolio/trades.md): Utilities for working with trade and position records and their metrics.

## API > Portfolio > Numba

- [Portfolio Numba Index](https://vectorbt.pro/pvt_41531c19/api/portfolio/nb/index.md): Index of subpackages and modules with Numba-compiled functions for array-based portfolio simulation.
- [Analysis](https://vectorbt.pro/pvt_41531c19/api/portfolio/nb/analysis.md): Numba-compiled functions computing asset values, returns, exposures, and profits.
- [Core](https://vectorbt.pro/pvt_41531c19/api/portfolio/nb/core.md): Numba-compiled core for executing orders, managing positions, and computing trade stats.
- [Context Helpers](https://vectorbt.pro/pvt_41531c19/api/portfolio/nb/ctx_helpers.md): Numba-compiled helpers for querying portfolio simulation context and state.
- [Order-Func-Based Simulation](https://vectorbt.pro/pvt_41531c19/api/portfolio/nb/from_order_func.md): Numba-compiled routines for simulations driven by custom order functions.
- [Order-Based Simulation](https://vectorbt.pro/pvt_41531c19/api/portfolio/nb/from_orders.md): Numba-compiled functions for simulating portfolios from explicit order arrays.
- [Signal-Based Simulation](https://vectorbt.pro/pvt_41531c19/api/portfolio/nb/from_signals.md): Numba-compiled functions that simulate trading based on entry and exit signals.
- [Iterative Functions](https://vectorbt.pro/pvt_41531c19/api/portfolio/nb/iter_.md): Numba-compiled utilities for iterative value selection within simulations.
- [Records](https://vectorbt.pro/pvt_41531c19/api/portfolio/nb/records.md): Numba-compiled functions for computing trade metrics and aggregating orders into positions.

## API > Portfolio > Optimization

- [Optimization Index](https://vectorbt.pro/pvt_41531c19/api/portfolio/pfopt/index.md): Index of subpackages and modules for portfolio optimization.
- [Optimization Base](https://vectorbt.pro/pvt_41531c19/api/portfolio/pfopt/base.md): Functions and class for preparing data and generating allocations via PyPortfolioOpt or Riskfolio-Lib.
- [Numba Functions](https://vectorbt.pro/pvt_41531c19/api/portfolio/pfopt/nb.md): Numba-compiled utilities for efficient allocation generation and scaling.
- [Allocation Records](https://vectorbt.pro/pvt_41531c19/api/portfolio/pfopt/records.md): Classes for handling allocation point and range records.

## API > Plotly Express

- [Plotly Express Index](https://vectorbt.pro/pvt_41531c19/api/px/index.md): Index of subpackages and modules for Plotly Express visualization.
- [Plotly Express Accessors](https://vectorbt.pro/pvt_41531c19/api/px/accessors.md): Pandas accessors enabling Plotly Express plots in VectorBT PRO.
- [Class Decorators](https://vectorbt.pro/pvt_41531c19/api/px/decorators.md): Decorators that inject Plotly Express plotting methods into classes.

## API > Records

- [Record Index](https://vectorbt.pro/pvt_41531c19/api/records/index.md): Index of subpackages and modules for sparse record arrays.
- [Record Base](https://vectorbt.pro/pvt_41531c19/api/records/base.md): Base utilities for structured record arrays enabling mapping, grouping, filtering, resampling, stacking, format conversion, and time-series alignment.
- [Record Chunking](https://vectorbt.pro/pvt_41531c19/api/records/chunking.md): Utilities for adjusting and merging chunked record arrays using chunk metadata.
- [Column Mapper](https://vectorbt.pro/pvt_41531c19/api/records/col_mapper.md): Column array mapping utilities for stacking, selecting, and grouping columns with metadata management.
- [Class Decorators](https://vectorbt.pro/pvt_41531c19/api/records/decorators.md): Decorators that add field properties, override configurations, and inject shortcuts into record classes.
- [Mapped Array](https://vectorbt.pro/pvt_41531c19/api/records/mapped_array.md): Array wrapper mapping values to columns and indices for per-column processing, stats, plotting, conflict resolution, arithmetic, and tabular export without DataFrames.
- [Numba Functions](https://vectorbt.pro/pvt_41531c19/api/records/nb.md): Numba-compiled helpers for column-wise selection, reduction, reshaping, and other record or mapped-array operations.

## API > Registries

- [Registry Index](https://vectorbt.pro/pvt_41531c19/api/registries/index.md): Index of subpackages and modules with global registries used across VectorBT PRO.
- [Caching Registry](https://vectorbt.pro/pvt_41531c19/api/registries/ca_registry.md): Global registry managing caching-enabled functions, hierarchies, and metrics.
- [Chunking Registry](https://vectorbt.pro/pvt_41531c19/api/registries/ch_registry.md): Registry for functions supporting chunked processing with decorators, retrieval, and resolution tools.
- [JIT Registry](https://vectorbt.pro/pvt_41531c19/api/registries/jit_registry.md): Registry for jittable functions managing multiple implementations, caching, and compilation options.
- [Progress Bar Registry](https://vectorbt.pro/pvt_41531c19/api/registries/pbar_registry.md): Registry for creating, tracking, and managing progress bar instances by ID.

## API > Returns

- [Return Index](https://vectorbt.pro/pvt_41531c19/api/returns/index.md): Index of subpackages and modules for return analysis.
- [Return Accessors](https://vectorbt.pro/pvt_41531c19/api/returns/accessors.md): Pandas accessors providing performance metrics, risk measures, ratios, and visualizations for return series.
- [Return Enums](https://vectorbt.pro/pvt_41531c19/api/returns/enums.md): Named tuples and enums representing return parameters such as rolling Sharpe modes.
- [Numba Functions](https://vectorbt.pro/pvt_41531c19/api/returns/nb.md): Numba-compiled routines computing returns, portfolio metrics, annualized and rolling stats, and risk/return ratios.
- [QuantStats Adapter](https://vectorbt.pro/pvt_41531c19/api/returns/qs_adapter.md): Adapter exposing QuantStats performance and risk functions on return series.

## API > Signals

- [Signal Index](https://vectorbt.pro/pvt_41531c19/api/signals/index.md): Index of subpackages and modules for signal analysis.
- [Signal Accessors](https://vectorbt.pro/pvt_41531c19/api/signals/accessors.md): Pandas accessors for signal computations, stats, range building, plotting, and generation on boolean data.
- [Signal Enums](https://vectorbt.pro/pvt_41531c19/api/signals/enums.md): Named tuples and enums for modes, relations, stop types, and contexts in signal processing.
- [Signal Factory](https://vectorbt.pro/pvt_41531c19/api/signals/factory.md): Factory for building customizable trading-signal generator classes from placement functions.
- [Numba Functions](https://vectorbt.pro/pvt_41531c19/api/signals/nb.md): Numba-compiled functions for creating, cleaning, ranking, and analyzing entry/exit signal masks and ranges.

## API > Signals > Generators

- [Signal Generator Index](https://vectorbt.pro/pvt_41531c19/api/signals/generators/index.md): Index of subpackages and modules with custom signal generators built with the signal factory.
- [OHLC Stop Chained Exits](https://vectorbt.pro/pvt_41531c19/api/signals/generators/ohlcstcx.md): Chained-exit signal generator using OHLC data and stop thresholds to derive new entries and exits.
- [OHLC Stop Exits](https://vectorbt.pro/pvt_41531c19/api/signals/generators/ohlcstx.md): Exit-stop signal generator based on OHLC prices with configurable stop-loss and take-profit parameters.
- [Random Entries](https://vectorbt.pro/pvt_41531c19/api/signals/generators/rand.md): Random-entry signal generator driven by entry probability and count settings.
- [Random Entries & Exits](https://vectorbt.pro/pvt_41531c19/api/signals/generators/randnx.md): Random entry-and-exit signal generator with independently tunable parameters.
- [Random Exits](https://vectorbt.pro/pvt_41531c19/api/signals/generators/randx.md): Random-exit signal generator using probability-based placement and post-processing utilities.
- [Probabilistic Entries](https://vectorbt.pro/pvt_41531c19/api/signals/generators/rprob.md): Probability-weighted entry signal generator supporting parameter grids.
- [Probabilistic Chained Exits](https://vectorbt.pro/pvt_41531c19/api/signals/generators/rprobcx.md): Probability-weighted chained-exit generator that derives new exit sequences from given entries.
- [Probabilistic Entry & Exits](https://vectorbt.pro/pvt_41531c19/api/signals/generators/rprobnx.md): Probability-based entry-and-exit signal generator for backtesting scenarios.
- [Probabilistic Exits](https://vectorbt.pro/pvt_41531c19/api/signals/generators/rprobx.md): Probability-weighted exit signal generator for stochastic strategy design.
- [Stop Chained Exits](https://vectorbt.pro/pvt_41531c19/api/signals/generators/stcx.md): Chained stop-exit signal generator that builds exit sequences from supplied entries.
- [Stop Exits](https://vectorbt.pro/pvt_41531c19/api/signals/generators/stx.md): Stop-exit signal generator producing exit signals from static stop values with plotting and stats helpers.

## API > Utilities

- [Utility Index](https://vectorbt.pro/pvt_41531c19/api/utils/index.md): Index of subpackages and modules with utilities and helper tools used across VectorBT PRO.
- [Annotations](https://vectorbt.pro/pvt_41531c19/api/utils/annotations.md): Functions for inspecting, modifying, and validating Python type annotations, including var-args and unions.
- [Array Operations](https://vectorbt.pro/pvt_41531c19/api/utils/array_.md): Functions for array rescaling, NaN handling, property checks, precision casting, row hashing, and uniform random partitioning.
- [Attribute Access](https://vectorbt.pro/pvt_41531c19/api/utils/attr_.md): Helpers for cached attribute retrieval, shortcut resolution, and class attribute field management.
- [Base Class](https://vectorbt.pro/pvt_41531c19/api/utils/base.md): Foundation class with helper methods for accessing related API pages, messages, and examples.
- [Caching](https://vectorbt.pro/pvt_41531c19/api/utils/caching.md): Tools for clearing Python caches and managing cacheable properties and methods.
- [Chaining Functions](https://vectorbt.pro/pvt_41531c19/api/utils/chaining.md): Fluent interface for sequentially chaining and executing functions or tasks.
- [Validation Checks](https://vectorbt.pro/pvt_41531c19/api/utils/checks.md): Runtime validation and type-checking utilities for arrays, collections, functions, dtypes, and Pandas structures.
- [Chunking Inputs](https://vectorbt.pro/pvt_41531c19/api/utils/chunking.md): Framework for splitting inputs into chunks, executing functions per chunk, and merging results with customizable segmentation.
- [Colors](https://vectorbt.pro/pvt_41531c19/api/utils/colors.md): Functions for color conversion, lightness and opacity adjustment, colormap mapping, and RGB(A) parsing.
- [Configuration](https://vectorbt.pro/pvt_41531c19/api/utils/config.md): Classes for hierarchical configuration management, including updating, merging, freezing, resetting, and atomic path handling.
- [Datetime](https://vectorbt.pro/pvt_41531c19/api/utils/datetime_.md): Helpers for parsing, converting, formatting, and manipulating timezone-aware or naive datetimes and frequencies.
- [Datetime Numba](https://vectorbt.pro/pvt_41531c19/api/utils/datetime_nb.md): Numba-compiled datetime functions for extracting components, determining ranges, and checking component statuses.
- [Decorators](https://vectorbt.pro/pvt_41531c19/api/utils/decorators.md): Decorators for caching, metadata attachment, and custom behavior of functions, methods, and properties.
- [Enumeration](https://vectorbt.pro/pvt_41531c19/api/utils/enum_.md): Utilities for converting between enum fields and values with support for unknown types.
- [Expression Evaluation](https://vectorbt.pro/pvt_41531c19/api/utils/eval_.md): Functions for executing and compiling Python code, analyzing free variables, and identifying evaluable objects.
- [Execution Engines](https://vectorbt.pro/pvt_41531c19/api/utils/execution.md): Concurrent or sequential execution engines with task chunking, caching, and result merging.
- [Plotly Figures](https://vectorbt.pro/pvt_41531c19/api/utils/figure.md): Helpers for building, customizing, and displaying interactive Plotly figures, subplots, widgets, and resampling features.
- [Formatting Tools](https://vectorbt.pro/pvt_41531c19/api/utils/formatting.md): Functions for naming-style conversion, array and function formatting, and multi-engine serialization.
- [Hashing](https://vectorbt.pro/pvt_41531c19/api/utils/hashing.md): Utilities for computing customizable hash values for functions and objects, including unhashable arguments.
- [Image Processing](https://vectorbt.pro/pvt_41531c19/api/utils/image_.md): Functions to combine images and save animations from iterable plots with white background fill.
- [JIT Compilation](https://vectorbt.pro/pvt_41531c19/api/utils/jitting.md): Tools for resolving, configuring, and applying JIT compilation strategies to functions.
- [Magic Decorators](https://vectorbt.pro/pvt_41531c19/api/utils/magic_decorators.md): Class decorators that add unary and binary magic methods via configurable operator mappings.
- [Value Mapping](https://vectorbt.pro/pvt_41531c19/api/utils/mapping.md): Rule-based transformers for mapping values within Python data structures.
- [Math Operations](https://vectorbt.pro/pvt_41531c19/api/utils/math_.md): Tolerance-based float comparison and arithmetic helpers.
- [Merging Functions](https://vectorbt.pro/pvt_41531c19/api/utils/merging.md): Helpers for applying merging functions with template substitution and evaluation identifiers.
- [Modules](https://vectorbt.pro/pvt_41531c19/api/utils/module_.md): Functions for importing, resolving, and inspecting modules, objects, reference names, and packages.
- [Paths](https://vectorbt.pro/pvt_41531c19/api/utils/path_.md): Helpers for file and directory paths including existence checks, creation, deletion, listing, sizing, and visualization.
- [Parameterization](https://vectorbt.pro/pvt_41531c19/api/utils/params.md): Tools for combining and parameterizing function inputs and configurations into structured execution grids.
- [Parsing](https://vectorbt.pro/pvt_41531c19/api/utils/parsing.md): Functions for parsing arguments, extracting variable names, matching annotated arguments, and managing output suppression.
- [Progress Bars](https://vectorbt.pro/pvt_41531c19/api/utils/pbar.md): Context managers to globally show, hide, and manage progress bars.
- [Pickling](https://vectorbt.pro/pvt_41531c19/api/utils/pickling.md): Functions for compressed serialization, deserialization, instance reconstruction, and path handling.
- [Profiling Tools](https://vectorbt.pro/pvt_41531c19/api/utils/profiling.md): Timing and memory profiling utilities for Python functions.
- [Random Numbers](https://vectorbt.pro/pvt_41531c19/api/utils/random_.md): Utilities for deterministic random number generation and global seed setting.
- [HTTP Requests](https://vectorbt.pro/pvt_41531c19/api/utils/requests_.md): Session creators with retry logic and GIF URL generation via Giphy.
- [Job Scheduling](https://vectorbt.pro/pvt_41531c19/api/utils/schedule_.md): Asynchronous job scheduler for periodic execution, management, and control.
- [Object Searching](https://vectorbt.pro/pvt_41531c19/api/utils/search_.md): Path-like search, replace, and traversal utilities for nested objects.
- [Item Selection](https://vectorbt.pro/pvt_41531c19/api/utils/selection.md): Helpers for selecting items by label or position.
- [Source Code Manipulation](https://vectorbt.pro/pvt_41531c19/api/utils/source.md): Functions for extracting annotated sections, refining code, splitting chunks, and managing imports.
- [Tagging](https://vectorbt.pro/pvt_41531c19/api/utils/tagging.md): Utilities to evaluate tag matching and boolean tag expressions.
- [Telegram Integration](https://vectorbt.pro/pvt_41531c19/api/utils/telegram.md): Wrappers around python-telegram-bot for messaging, animations, and command handling.
- [Templates](https://vectorbt.pro/pvt_41531c19/api/utils/template.md): Functions to detect and substitute template instances within objects and classes.
- [Warnings](https://vectorbt.pro/pvt_41531c19/api/utils/warnings_.md): Helpers for custom warning formatting, emission, suppression, and global filtering.

## Optional

- [Latest Changelog](https://vectorbt.pro/pvt_41531c19/getting-started/release-notes/index.md): Review all changes introduced recently.
- [2024 Changelog](https://vectorbt.pro/pvt_41531c19/getting-started/release-notes/2024.md): Review all changes introduced in 2024.
- [2023 Changelog](https://vectorbt.pro/pvt_41531c19/getting-started/release-notes/2023.md): Review all changes introduced in 2023.
- [2022 Changelog](https://vectorbt.pro/pvt_41531c19/getting-started/release-notes/2022.md): Review all changes introduced in 2022.
- [2021 Changelog](https://vectorbt.pro/pvt_41531c19/getting-started/release-notes/2021.md): Review all changes introduced in 2021, including first ever major refactors and enhancements.
- [Terms of Use](https://vectorbt.pro/pvt_41531c19/terms/terms-of-use.md): Review legal agreement detailing responsibilities, IP rights, payments, cancellations, prohibited activities, and dispute resolution for VectorBT PRO software and services.
- [Software License](https://vectorbt.pro/pvt_41531c19/terms/software-license.md): Read licensing terms specifying permitted non-commercial use, modification, distribution, trademark usage, termination, and liability limitations for the software.
- [Repository Remarks](https://vectorbt.pro/pvt_41531c19/terms/remarks.md): See rules governing access, modification, and distribution of the private repository's source code.
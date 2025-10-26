# ATLAS - Adaptive Trading with Layered Asset System

A professional quantitative trading system implementing portfolio-level risk management across multiple uncorrelated strategies.

## Overview

ATLAS is a multi-strategy algorithmic trading platform designed for institutional-grade portfolio management. The system implements five uncorrelated strategies with comprehensive risk controls, walk-forward validation, and professional position sizing.

### Core Philosophy

- **Expectancy over win rate**: Focus on mathematical edge rather than prediction accuracy
- **Portfolio-level orchestration**: Coordinated risk management across all strategies
- **Professional risk controls**: Multiple risk layers (position sizing, portfolio heat, circuit breakers)
- **Validation-first development**: No strategy deploys without walk-forward validation

### Architecture

```
Portfolio Manager (Orchestration)
    |
    +-- Strategy 1: GMM Regime Detection
    +-- Strategy 2: Five-Day Washout Mean Reversion
    +-- Strategy 3: Opening Range Breakout
    +-- Strategy 4: Pairs Trading
    +-- Strategy 5: Semi-Volatility Momentum Portfolio
    |
Risk Management Layer
    +-- Position Sizing (ATR-based with capital constraints)
    +-- Portfolio Heat Management (6-8% exposure limit)
    +-- Circuit Breakers (drawdown limits)
    |
Data Management
    +-- Multi-Timeframe Alignment
    +-- Market Hours Filtering
    +-- Data Quality Validation
```

## Current Implementation Status

### Completed (Phase 0)
- Position sizing with capital constraints (Gate 1 validated)
- Opening Range Breakout strategy implementation
- VectorBT Pro integration for backtesting
- OpenAI API integration for advanced analytics
- Comprehensive research documentation

### In Progress (Phase 1)
- BaseStrategy abstract class implementation
- RiskManager with portfolio heat management
- ORB strategy refactor to inherit BaseStrategy

### Planned (Phase 2-3)
- GMM Regime Detection (highest priority)
- Five-Day Washout Mean Reversion
- Portfolio Manager for multi-strategy coordination
- Walk-forward validation framework

## Technology Stack

### Core Framework
- **VectorBT Pro**: Backtesting engine with vectorized operations
- **Alpaca API**: Market data and paper trading execution
- **Python 3.12+**: Modern Python with type hints
- **UV**: Fast dependency management

### Analytics & ML
- **TA-Lib**: Technical indicators (150+ functions)
- **scikit-learn**: Machine learning (GMM, StandardScaler)
- **statsmodels**: Statistical analysis (cointegration for pairs trading)
- **OpenAI API**: Advanced analytics and embeddings

### Development Tools
- **pytest**: Comprehensive testing framework
- **ruff**: Fast Python linter and formatter
- **mypy**: Static type checking
- **pandas-market-calendars**: Market hours validation
- **OpenMemory**: Semantic memory system for queryable development context (MCP integration)

## Key Features

### Position Sizing
- ATR-based stop losses with capital constraints
- Proven mathematical formula (Gate 1 validated)
- Never exceeds 100% of available capital
- VectorBT Pro compatible return formats

### Portfolio Heat Management
- Tracks total exposure across all strategies
- Hard limit of 6-8% portfolio heat
- Rejects signals when at exposure limit
- Multi-position risk aggregation

### Regime Detection
- Gaussian Mixture Model classification
- Yang-Zhang volatility + SMA crossover features
- Walk-forward training (refit quarterly)
- Reduces drawdown by 50%+ in validation

### Opening Range Breakout
- 30-minute opening range with volume confirmation (2.0x threshold)
- ATR-based stops (2.5x multiplier)
- Directional bias filter (close > open)
- Target Sharpe >2.0, R:R >3:1

## Project Structure

```
atlas-trading-system/
├── strategies/              # Strategy implementations
│   ├── base_strategy.py    # Abstract base class (pending)
│   └── orb.py              # Opening Range Breakout
├── core/                    # Core system components
│   ├── risk_manager.py     # Portfolio heat (pending)
│   └── portfolio_manager.py # Multi-strategy coordination (pending)
├── utils/                   # Utility functions
│   └── position_sizing.py  # Position sizing (complete)
├── data/                    # Data management
│   ├── alpaca.py           # Alpaca API integration
│   └── mtf_manager.py      # Multi-timeframe alignment
├── tests/                   # Test suite
│   ├── test_gate1_position_sizing.py  # Position sizing tests (passing)
│   └── test_orb_quick.py              # ORB strategy tests
├── docs/                    # Documentation
│   ├── System_Architecture_Reference.md  # Complete architecture
│   ├── HANDOFF.md                        # Current status
│   └── CLAUDE.md                         # Development standards
└── pyproject.toml           # Dependencies and configuration
```

## Installation

### Prerequisites
- Python 3.12 or higher
- UV package manager
- Alpaca Markets account (paper trading)
- OpenAI API key (for advanced features)
- OpenMemory server (optional, for development context management)

### Setup

```bash
# Clone the repository
git clone https://github.com/sheehyct/ATLAS-Algorithmic-Trading-System-V1.git
cd ATLAS-Algorithmic-Trading-System-V1

# Install dependencies with UV
uv sync

# Create .env file from template
cp .env.template .env

# Add your API keys to .env
# ALPACA_API_KEY=your_key_here
# ALPACA_SECRET_KEY=your_secret_here
# OPENAI_API_KEY=your_key_here

# Run tests to verify installation
uv run pytest tests/test_gate1_position_sizing.py -v
```

### Optional: OpenMemory Setup

OpenMemory provides semantic search over development context (research findings, validation results, architectural decisions).

**Installation:**
```bash
# Clone OpenMemory repository
git clone https://github.com/CaviraOSS/OpenMemory.git C:/Dev/openmemory
cd C:/Dev/openmemory

# Install dependencies (requires Node.js and Bun)
cd backend
npm install --legacy-peer-deps

# Configure environment
cp .env.example .env
# Edit .env to set OPENAI_API_KEY for embeddings

# Start server
npm run dev
```

**Claude Code Integration:**

OpenMemory integrates via MCP (Model Context Protocol) for seamless access from Claude Code.

See `docs/OPENMEMORY_PROCEDURES.md` for complete setup and daily operations guide.
See `docs/OpenMemory_Integration_Guide.md` for detailed installation and configuration.
```

## Development Standards

### Git Commit Messages
- Follow conventional commits format (feat:, fix:, docs:, test:, refactor:)
- Professional tone (no emojis, no AI signatures)
- Explain WHAT changed and WHY
- Reference documentation where applicable

### Code Quality
- Type hints required for all functions
- Docstrings for all public methods
- Unit tests required before merge
- Code coverage minimum 80%

### Testing Requirements
- Unit tests for all components
- Integration tests for strategy interactions
- Walk-forward validation before deployment
- Paper trading minimum 6 months before live

### Documentation
- Update HANDOFF.md with progress
- Document architectural decisions
- Provide code examples
- Cite research sources

## Performance Targets

### Individual Strategy Targets
| Strategy | Win Rate | Sharpe | Max DD | CAGR |
|----------|----------|--------|--------|------|
| GMM Regime | 55-65% | 0.8-1.0 | -15% | 8-12% |
| Mean Reversion | 65-75% | 0.6-0.9 | -12% | 5-8% |
| ORB | 15-25% | 1.5-2.5 | -25% | 15-25% |
| Pairs Trading | 70-80% | 1.0-1.4 | -10% | 6-10% |
| Momentum | 50-60% | 1.0-1.5 | -20% | 12-20% |

### Portfolio Targets (Equal Allocation)
- Sharpe Ratio: >1.0 (excellent: >1.5)
- Max Drawdown: <25% (excellent: <20%)
- CAGR: 10-15% (excellent: >18%)
- Profit Factor: >1.5 (excellent: >2.0)

## Critical Success Criteria

Before live trading deployment:
1. Data quality validated (no NaN, proper adjustments)
2. Position sizing constraints enforced (Gate 1 passed)
3. Portfolio heat never exceeds 8% (Gate 2 pending)
4. Walk-forward validation within 30% degradation
5. All unit tests passing (100% pass rate)
6. Paper trading 6+ months with 100+ trades
7. Paper performance matches backtest expectations

## Documentation

- **System Architecture**: See `docs/System_Architecture_Reference.md`
- **Current Status**: See `docs/HANDOFF.md`
- **Development Guide**: See `docs/CLAUDE.md`
- **Research Findings**: See `docs/research/Medium_Articles_Research_Findings.md`
- **VectorBT Pro Docs**: See `VectorBT Pro Official Documentation/`

## Support and Contributing

This is a professional quantitative trading system under active development. For questions, issues, or contributions:

1. Review existing documentation in `docs/`
2. Check System_Architecture_Reference.md for design decisions
3. Follow development standards in CLAUDE.md
4. Submit issues with detailed reproduction steps
5. Pull requests must include tests and documentation

## License

See LICENSE file for details.

## Disclaimer

This software is for educational and research purposes. Algorithmic trading involves substantial risk of loss. Past performance does not guarantee future results. No warranty is provided for the accuracy or profitability of this system. Use at your own risk.

---

**ATLAS Algorithmic Trading System**
Version: 1.0 (Foundation Phase)
Last Updated: October 2025
Status: Active Development - Phase 1 (Foundation Implementation)

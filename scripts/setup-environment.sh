#!/bin/bash
# ============================================================================
# STRAT Trading System - Environment Setup Script
# ============================================================================
# Initial environment setup for production deployment
# Creates necessary directories, configures secrets, and validates setup
# ============================================================================

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

create_directories() {
    log "Creating necessary directories..."
    
    local directories=(
        "$PROJECT_ROOT/docker/volumes/logs"
        "$PROJECT_ROOT/docker/volumes/data"
        "$PROJECT_ROOT/docker/volumes/results"
        "$PROJECT_ROOT/docker/volumes/cache"
        "$PROJECT_ROOT/docker/prometheus"
        "$PROJECT_ROOT/docker/grafana/provisioning/datasources"
        "$PROJECT_ROOT/docker/grafana/provisioning/dashboards"
        "$PROJECT_ROOT/docker/grafana/dashboards"
        "$PROJECT_ROOT/docker/postgres/init"
        "$PROJECT_ROOT/docker/fluent-bit"
        "$PROJECT_ROOT/backups"
        "$PROJECT_ROOT/certs"
        "$PROJECT_ROOT/secrets"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
    
    # Set appropriate permissions
    chmod 755 "$PROJECT_ROOT/docker/volumes"
    chmod 755 "$PROJECT_ROOT/docker/volumes/logs"
    chmod 755 "$PROJECT_ROOT/docker/volumes/data"
    chmod 755 "$PROJECT_ROOT/docker/volumes/results"
    chmod 700 "$PROJECT_ROOT/secrets"
    chmod 700 "$PROJECT_ROOT/certs"
    
    log_success "Directories created successfully"
}

setup_environment_file() {
    log "Setting up environment configuration..."
    
    local env_file="$PROJECT_ROOT/.env"
    local template_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    
    if [[ ! -f "$template_file" ]]; then
        log_error "Environment template not found: $template_file"
        exit 1
    fi
    
    if [[ -f "$env_file" ]]; then
        log_warning "Environment file already exists: $env_file"
        read -p "Overwrite existing .env file? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Keeping existing .env file"
            return 0
        fi
    fi
    
    cp "$template_file" "$env_file"
    log "Copied template: $template_file -> $env_file"
    
    # Generate secure random values for secrets
    generate_secure_secrets "$env_file"
    
    log_warning "IMPORTANT: Review and update the .env file with your actual API keys and credentials"
    log "File location: $env_file"
    
    log_success "Environment file setup completed"
}

generate_secure_secrets() {
    local env_file="$1"
    
    log "Generating secure random secrets..."
    
    # Generate random secrets
    local postgres_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local grafana_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local grafana_secret=$(openssl rand -hex 16)
    local strat_secret_key=$(openssl rand -hex 32)
    local jwt_secret=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-32)
    local encryption_key=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    
    # Replace placeholder values in environment file
    if command -v sed &> /dev/null; then
        sed -i.bak \
            -e "s/REPLACE_WITH_SECURE_PASSWORD/$postgres_password/g" \
            -e "s/REPLACE_WITH_SECURE_GRAFANA_PASSWORD/$grafana_password/g" \
            -e "s/REPLACE_WITH_SECURE_GRAFANA_SECRET_KEY/$grafana_secret/g" \
            -e "s/REPLACE_WITH_SECURE_SECRET_KEY/$strat_secret_key/g" \
            -e "s/REPLACE_WITH_SECURE_JWT_SECRET/$jwt_secret/g" \
            -e "s/REPLACE_WITH_SECURE_ENCRYPTION_KEY/$encryption_key/g" \
            "$env_file"
        rm -f "$env_file.bak"
    else
        log_warning "sed command not available, secrets not automatically generated"
        return 1
    fi
    
    log_success "Secure secrets generated"
}

setup_docker_directories() {
    log "Setting up Docker-specific directories and files..."
    
    # Create fluent-bit configuration
    cat > "$PROJECT_ROOT/docker/fluent-bit/fluent-bit.conf" << 'EOF'
[SERVICE]
    Flush         1
    Log_Level     info
    Daemon        off
    Parsers_File  parsers.conf
    HTTP_Server   On
    HTTP_Listen   0.0.0.0
    HTTP_Port     2020

[INPUT]
    Name              tail
    Path              /app/logs/*.log
    Parser            json
    Tag               strat.*
    Refresh_Interval  5

[OUTPUT]
    Name  stdout
    Match strat.*
    Format json_lines
EOF
    
    # Create parsers configuration
    cat > "$PROJECT_ROOT/docker/fluent-bit/parsers.conf" << 'EOF'
[PARSER]
    Name        json
    Format      json
    Time_Key    timestamp
    Time_Format %Y-%m-%d %H:%M:%S
    Time_Keep   On
EOF
    
    # Create PostgreSQL initialization script
    cat > "$PROJECT_ROOT/docker/postgres/init/01-init.sql" << 'EOF'
-- STRAT Trading System Database Initialization
-- Creates necessary database structure for the trading system

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create application schema
CREATE SCHEMA IF NOT EXISTS strat_trading;

-- Create application user (if not exists)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'strat_app') THEN

      CREATE ROLE strat_app LOGIN PASSWORD 'app_password_123';
   END IF;
END
$do$;

-- Grant permissions
GRANT USAGE ON SCHEMA strat_trading TO strat_app;
GRANT CREATE ON SCHEMA strat_trading TO strat_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA strat_trading TO strat_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA strat_trading TO strat_app;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA strat_trading GRANT ALL ON TABLES TO strat_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA strat_trading GRANT ALL ON SEQUENCES TO strat_app;

-- Create basic tables for the trading system
CREATE TABLE IF NOT EXISTS strat_trading.trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    entry_price DECIMAL(10,4) NOT NULL,
    exit_price DECIMAL(10,4),
    quantity INTEGER NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    profit_loss DECIMAL(12,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS strat_trading.backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    total_pnl DECIMAL(12,2),
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON strat_trading.trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON strat_trading.trades(entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_strategy ON strat_trading.trades(strategy);
CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON strat_trading.backtest_results(strategy_name);
CREATE INDEX IF NOT EXISTS idx_backtest_results_symbol ON strat_trading.backtest_results(symbol);
EOF
    
    log_success "Docker directories and files setup completed"
}

setup_kubernetes_secrets() {
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        log_warning "Environment file not found, skipping Kubernetes secrets setup"
        return 0
    fi
    
    log "Setting up Kubernetes secrets template..."
    
    # Source environment variables
    source "$PROJECT_ROOT/.env"
    
    # Create secrets with base64 encoding
    local secrets_file="$PROJECT_ROOT/k8s/secrets-generated.yaml"
    
    cat > "$secrets_file" << EOF
# ============================================================================
# STRAT Trading System - Generated Kubernetes Secrets
# ============================================================================
# Auto-generated secrets file - DO NOT COMMIT TO VERSION CONTROL
# Generated on: $(date)
# ============================================================================

apiVersion: v1
kind: Secret
metadata:
  name: strat-app-secrets
  namespace: strat-trading
  labels:
    app: strat-trading
    component: secrets
type: Opaque
data:
  ALPACA_API_KEY: $(echo -n "${ALPACA_API_KEY:-}" | base64 -w 0)
  ALPACA_API_SECRET: $(echo -n "${ALPACA_API_SECRET:-}" | base64 -w 0)
  ALPHAVANTAGE_API_KEY: $(echo -n "${ALPHAVANTAGE_API_KEY:-}" | base64 -w 0)

---
apiVersion: v1
kind: Secret
metadata:
  name: strat-database-secrets
  namespace: strat-trading
  labels:
    app: strat-trading
    component: database
type: Opaque
data:
  POSTGRES_PASSWORD: $(echo -n "${POSTGRES_PASSWORD:-}" | base64 -w 0)

---
apiVersion: v1
kind: Secret
metadata:
  name: strat-monitoring-secrets
  namespace: strat-trading
  labels:
    app: strat-trading
    component: monitoring
type: Opaque
data:
  GF_SECURITY_ADMIN_PASSWORD: $(echo -n "${GRAFANA_ADMIN_PASSWORD:-}" | base64 -w 0)
  GF_SECURITY_SECRET_KEY: $(echo -n "${GRAFANA_SECRET_KEY:-}" | base64 -w 0)
EOF
    
    chmod 600 "$secrets_file"
    log_success "Kubernetes secrets template created: $secrets_file"
    log_warning "Remember to apply secrets: kubectl apply -f $secrets_file"
}

validate_setup() {
    log "Validating environment setup..."
    
    local validation_errors=0
    
    # Check required files
    local required_files=(
        "$PROJECT_ROOT/.env"
        "$PROJECT_ROOT/Dockerfile"
        "$PROJECT_ROOT/docker-compose.yml"
        "$PROJECT_ROOT/pyproject.toml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file missing: $file"
            ((validation_errors++))
        fi
    done
    
    # Check required directories
    local required_dirs=(
        "$PROJECT_ROOT/docker/volumes"
        "$PROJECT_ROOT/k8s"
        "$PROJECT_ROOT/scripts"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_error "Required directory missing: $dir"
            ((validation_errors++))
        fi
    done
    
    # Check environment variables in .env
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        source "$PROJECT_ROOT/.env"
        
        local required_vars=(
            "STRAT_ENVIRONMENT"
            "POSTGRES_PASSWORD"
            "GRAFANA_ADMIN_PASSWORD"
        )
        
        for var in "${required_vars[@]}"; do
            if [[ -z "${!var:-}" ]]; then
                log_error "Required environment variable not set: $var"
                ((validation_errors++))
            fi
        done
    fi
    
    # Check script permissions
    local scripts=(
        "$PROJECT_ROOT/scripts/build.sh"
        "$PROJECT_ROOT/scripts/deploy.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]] && [[ ! -x "$script" ]]; then
            chmod +x "$script"
            log "Made script executable: $script"
        fi
    done
    
    if [[ $validation_errors -eq 0 ]]; then
        log_success "Environment validation passed"
        return 0
    else
        log_error "Environment validation failed with $validation_errors errors"
        return 1
    fi
}

show_next_steps() {
    log "Environment Setup Complete!"
    echo ""
    echo "NEXT STEPS:"
    echo "==========="
    echo ""
    echo "1. Update API credentials in .env file:"
    echo "   - ALPACA_API_KEY and ALPACA_API_SECRET"
    echo "   - ALPHAVANTAGE_API_KEY"
    echo ""
    echo "2. Review and adjust configuration in .env file"
    echo ""
    echo "3. Build the container image:"
    echo "   ./scripts/build.sh"
    echo ""
    echo "4. Deploy the system:"
    echo "   # For Docker Compose:"
    echo "   ./scripts/deploy.sh --type docker-compose"
    echo ""
    echo "   # For Kubernetes:"
    echo "   ./scripts/deploy.sh --type kubernetes"
    echo ""
    echo "5. Access the system:"
    echo "   - Main application: http://localhost:8000"
    echo "   - Dashboard: http://localhost:8501"
    echo "   - Monitoring: http://localhost:3000 (Grafana)"
    echo ""
    echo "IMPORTANT SECURITY NOTES:"
    echo "========================"
    echo "- Never commit .env files to version control"
    echo "- Review and update default passwords"
    echo "- Configure SSL/TLS certificates for production"
    echo "- Set up proper network security and firewalls"
    echo ""
}

show_usage() {
    cat << EOF
STRAT Trading System - Environment Setup Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV   Environment to setup (production|development|staging) [default: production]
    --skip-secrets         Skip Kubernetes secrets generation
    --skip-validation      Skip environment validation
    -h, --help             Show this help message

EXAMPLES:
    # Setup production environment
    $0 --environment production

    # Setup development environment
    $0 --environment development

ENVIRONMENT VARIABLES:
    ENVIRONMENT            Environment name [default: production]
EOF
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local skip_secrets=false
    local skip_validation=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --skip-secrets)
                skip_secrets=true
                shift
                ;;
            --skip-validation)
                skip_validation=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    log "Starting STRAT Trading System environment setup"
    log "Environment: $ENVIRONMENT"
    log "Project root: $PROJECT_ROOT"
    
    # Execute setup steps
    create_directories
    setup_environment_file
    setup_docker_directories
    
    if [[ "$skip_secrets" != "true" ]]; then
        setup_kubernetes_secrets
    fi
    
    if [[ "$skip_validation" != "true" ]]; then
        if ! validate_setup; then
            log_error "Environment setup validation failed"
            exit 1
        fi
    fi
    
    show_next_steps
    log_success "Environment setup completed successfully!"
}

# Execute main function with all arguments
main "$@"
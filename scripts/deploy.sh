#!/bin/bash
# ============================================================================
# STRAT Trading System - Deployment Script
# ============================================================================
# Production deployment with zero-downtime rolling updates
# Health checks, rollback capabilities, and monitoring integration
# ============================================================================

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# Deployment configuration
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-kubernetes}"  # kubernetes|docker-compose
ENVIRONMENT="${ENVIRONMENT:-production}"
NAMESPACE="${NAMESPACE:-strat-trading}"
VERSION="${VERSION:-latest}"
IMAGE_NAME="${IMAGE_NAME:-strat-trading}"
REGISTRY="${REGISTRY:-}"

# Deployment options
DRY_RUN="${DRY_RUN:-false}"
SKIP_HEALTH_CHECK="${SKIP_HEALTH_CHECK:-false}"
ROLLBACK_ON_FAILURE="${ROLLBACK_ON_FAILURE:-true}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-600}"  # 10 minutes
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-30}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-10}"

# Paths
K8S_MANIFESTS_DIR="$PROJECT_ROOT/k8s"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

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

check_requirements() {
    log "Checking deployment requirements for $DEPLOYMENT_TYPE..."
    
    case "$DEPLOYMENT_TYPE" in
        "kubernetes")
            if ! command -v kubectl &> /dev/null; then
                log_error "kubectl is not installed or not in PATH"
                exit 1
            fi
            
            # Check cluster connectivity
            if ! kubectl cluster-info &> /dev/null; then
                log_error "Cannot connect to Kubernetes cluster"
                exit 1
            fi
            
            log "Connected to Kubernetes cluster: $(kubectl config current-context)"
            ;;
            
        "docker-compose")
            if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
                log_error "docker-compose is not installed or not in PATH"
                exit 1
            fi
            
            if ! docker info &> /dev/null; then
                log_error "Docker daemon is not running"
                exit 1
            fi
            ;;
            
        *)
            log_error "Unknown deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
    
    log_success "Requirements check completed"
}

validate_configuration() {
    log "Validating deployment configuration..."
    
    case "$DEPLOYMENT_TYPE" in
        "kubernetes")
            # Check if namespace exists
            if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
                log "Creating namespace: $NAMESPACE"
                kubectl apply -f "$K8S_MANIFESTS_DIR/namespace.yaml"
            fi
            
            # Check if manifests exist
            local required_manifests=("deployment.yaml" "service.yaml" "configmap.yaml")
            for manifest in "${required_manifests[@]}"; do
                if [[ ! -f "$K8S_MANIFESTS_DIR/$manifest" ]]; then
                    log_error "Required manifest not found: $manifest"
                    exit 1
                fi
            done
            ;;
            
        "docker-compose")
            if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
                log_error "docker-compose.yml not found at $DOCKER_COMPOSE_FILE"
                exit 1
            fi
            ;;
    esac
    
    # Check if image exists
    local full_image_name="${REGISTRY:+$REGISTRY/}${IMAGE_NAME}:${VERSION}"
    if ! docker image inspect "$full_image_name" &> /dev/null; then
        log_warning "Image not found locally: $full_image_name"
        log "Attempting to pull image..."
        if ! docker pull "$full_image_name"; then
            log_error "Failed to pull image: $full_image_name"
            exit 1
        fi
    fi
    
    log_success "Configuration validation completed"
}

create_backup() {
    log "Creating deployment backup..."
    
    local backup_dir="$PROJECT_ROOT/backups/deployment-$(date +'%Y%m%d-%H%M%S')"
    mkdir -p "$backup_dir"
    
    case "$DEPLOYMENT_TYPE" in
        "kubernetes")
            # Backup current deployment state
            kubectl get all -n "$NAMESPACE" -o yaml > "$backup_dir/current-state.yaml" 2>/dev/null || true
            kubectl get configmaps -n "$NAMESPACE" -o yaml > "$backup_dir/configmaps.yaml" 2>/dev/null || true
            kubectl get secrets -n "$NAMESPACE" -o yaml > "$backup_dir/secrets.yaml" 2>/dev/null || true
            kubectl get pvc -n "$NAMESPACE" -o yaml > "$backup_dir/pvc.yaml" 2>/dev/null || true
            ;;
            
        "docker-compose")
            # Backup docker-compose state
            docker-compose -f "$DOCKER_COMPOSE_FILE" config > "$backup_dir/docker-compose-resolved.yml" 2>/dev/null || true
            docker-compose -f "$DOCKER_COMPOSE_FILE" ps --format json > "$backup_dir/containers-state.json" 2>/dev/null || true
            ;;
    esac
    
    echo "$backup_dir" > /tmp/strat-deployment-backup-path
    log_success "Backup created at: $backup_dir"
}

deploy_kubernetes() {
    log "Deploying to Kubernetes cluster..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would apply the following resources:"
        kubectl apply -f "$K8S_MANIFESTS_DIR/" --namespace="$NAMESPACE" --dry-run=client
        return 0
    fi
    
    # Apply configuration and secrets first
    log "Applying ConfigMaps and Secrets..."
    kubectl apply -f "$K8S_MANIFESTS_DIR/configmap.yaml" --namespace="$NAMESPACE"
    
    # Apply secrets if they exist and are not templates
    if [[ -f "$K8S_MANIFESTS_DIR/secrets.yaml" ]]; then
        if ! grep -q "REPLACE_WITH" "$K8S_MANIFESTS_DIR/secrets.yaml"; then
            kubectl apply -f "$K8S_MANIFESTS_DIR/secrets.yaml" --namespace="$NAMESPACE"
        else
            log_warning "Secrets template detected - skipping secrets.yaml (configure secrets manually)"
        fi
    fi
    
    # Apply PVCs
    log "Applying Persistent Volume Claims..."
    kubectl apply -f "$K8S_MANIFESTS_DIR/pvc.yaml" --namespace="$NAMESPACE"
    
    # Apply services
    log "Applying Services..."
    kubectl apply -f "$K8S_MANIFESTS_DIR/service.yaml" --namespace="$NAMESPACE"
    
    # Apply deployments with rolling update
    log "Applying Deployments..."
    kubectl apply -f "$K8S_MANIFESTS_DIR/deployment.yaml" --namespace="$NAMESPACE"
    
    # Apply HPA and other resources
    if [[ -f "$K8S_MANIFESTS_DIR/hpa.yaml" ]]; then
        log "Applying Horizontal Pod Autoscaler..."
        kubectl apply -f "$K8S_MANIFESTS_DIR/hpa.yaml" --namespace="$NAMESPACE"
    fi
    
    if [[ -f "$K8S_MANIFESTS_DIR/ingress.yaml" ]]; then
        log "Applying Ingress..."
        kubectl apply -f "$K8S_MANIFESTS_DIR/ingress.yaml" --namespace="$NAMESPACE"
    fi
    
    log_success "Kubernetes resources applied"
}

deploy_docker_compose() {
    log "Deploying with Docker Compose..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would deploy the following services:"
        docker-compose -f "$DOCKER_COMPOSE_FILE" config --services
        return 0
    fi
    
    # Set environment variables
    export VERSION="$VERSION"
    export BUILD_DATE="$DEPLOY_DATE"
    export REGISTRY="$REGISTRY"
    export STRAT_ENVIRONMENT="$ENVIRONMENT"
    
    # Deploy services
    log "Starting services with docker-compose..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --remove-orphans
    
    log_success "Docker Compose deployment completed"
}

wait_for_deployment() {
    if [[ "$SKIP_HEALTH_CHECK" == "true" ]]; then
        log "Skipping health checks"
        return 0
    fi
    
    log "Waiting for deployment to be ready..."
    
    case "$DEPLOYMENT_TYPE" in
        "kubernetes")
            # Wait for deployments to be ready
            log "Waiting for deployments to roll out..."
            kubectl rollout status deployment/strat-app --namespace="$NAMESPACE" --timeout="${WAIT_TIMEOUT}s"
            kubectl rollout status deployment/strat-dashboard --namespace="$NAMESPACE" --timeout="${WAIT_TIMEOUT}s" || true
            
            # Wait for pods to be ready
            log "Waiting for pods to be ready..."
            kubectl wait --for=condition=ready pod -l app=strat-trading --namespace="$NAMESPACE" --timeout="${WAIT_TIMEOUT}s"
            ;;
            
        "docker-compose")
            # Wait for containers to be healthy
            local services=($(docker-compose -f "$DOCKER_COMPOSE_FILE" config --services))
            for service in "${services[@]}"; do
                log "Waiting for $service to be healthy..."
                local retries=0
                while [[ $retries -lt $HEALTH_CHECK_RETRIES ]]; do
                    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up (healthy)"; then
                        break
                    fi
                    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Exit"; then
                        log_error "Service $service failed to start"
                        return 1
                    fi
                    sleep "$HEALTH_CHECK_INTERVAL"
                    ((retries++))
                done
                
                if [[ $retries -eq $HEALTH_CHECK_RETRIES ]]; then
                    log_error "Timeout waiting for $service to be healthy"
                    return 1
                fi
            done
            ;;
    esac
    
    log_success "Deployment is ready"
}

perform_health_checks() {
    log "Performing comprehensive health checks..."
    
    local health_endpoints=()
    
    case "$DEPLOYMENT_TYPE" in
        "kubernetes")
            # Get service endpoints
            local app_endpoint=$(kubectl get service strat-app --namespace="$NAMESPACE" -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}' 2>/dev/null || echo "")
            local dashboard_endpoint=$(kubectl get service strat-dashboard --namespace="$NAMESPACE" -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}' 2>/dev/null || echo "")
            
            if [[ -n "$app_endpoint" ]]; then
                health_endpoints+=("http://$app_endpoint/health")
            fi
            if [[ -n "$dashboard_endpoint" ]]; then
                health_endpoints+=("http://$dashboard_endpoint/healthz")
            fi
            ;;
            
        "docker-compose")
            health_endpoints+=(
                "http://localhost:${STRAT_APP_PORT:-8000}/health"
                "http://localhost:${STRAT_DASHBOARD_PORT:-8501}/healthz"
            )
            ;;
    esac
    
    # Test each health endpoint
    for endpoint in "${health_endpoints[@]}"; do
        log "Testing health endpoint: $endpoint"
        local retries=0
        local success=false
        
        while [[ $retries -lt $HEALTH_CHECK_RETRIES ]]; do
            if curl -f -s --max-time 10 "$endpoint" > /dev/null; then
                success=true
                break
            fi
            sleep "$HEALTH_CHECK_INTERVAL"
            ((retries++))
        done
        
        if [[ "$success" == "true" ]]; then
            log_success "Health check passed: $endpoint"
        else
            log_warning "Health check failed: $endpoint"
        fi
    done
    
    log_success "Health checks completed"
}

rollback_deployment() {
    log_error "Deployment failed, initiating rollback..."
    
    local backup_path
    if [[ -f /tmp/strat-deployment-backup-path ]]; then
        backup_path=$(cat /tmp/strat-deployment-backup-path)
    else
        log_error "No backup path found, cannot rollback automatically"
        return 1
    fi
    
    case "$DEPLOYMENT_TYPE" in
        "kubernetes")
            log "Rolling back Kubernetes deployment..."
            kubectl rollout undo deployment/strat-app --namespace="$NAMESPACE" || true
            kubectl rollout undo deployment/strat-dashboard --namespace="$NAMESPACE" || true
            ;;
            
        "docker-compose")
            log "Rolling back Docker Compose deployment..."
            if [[ -f "$backup_path/docker-compose-resolved.yml" ]]; then
                docker-compose -f "$backup_path/docker-compose-resolved.yml" up -d --remove-orphans
            else
                log_error "Cannot find backup compose file for rollback"
                return 1
            fi
            ;;
    esac
    
    log_success "Rollback initiated"
}

show_deployment_status() {
    log "Deployment Status Summary"
    echo "=========================="
    
    case "$DEPLOYMENT_TYPE" in
        "kubernetes")
            echo "Namespace: $NAMESPACE"
            echo "Deployments:"
            kubectl get deployments --namespace="$NAMESPACE" 2>/dev/null || echo "No deployments found"
            echo ""
            echo "Pods:"
            kubectl get pods --namespace="$NAMESPACE" 2>/dev/null || echo "No pods found"
            echo ""
            echo "Services:"
            kubectl get services --namespace="$NAMESPACE" 2>/dev/null || echo "No services found"
            ;;
            
        "docker-compose")
            echo "Docker Compose Services:"
            docker-compose -f "$DOCKER_COMPOSE_FILE" ps 2>/dev/null || echo "No services found"
            ;;
    esac
    
    echo ""
    log_success "Deployment completed successfully at $DEPLOY_DATE"
}

cleanup() {
    log "Performing post-deployment cleanup..."
    
    # Remove temporary files
    rm -f /tmp/strat-deployment-backup-path
    
    # Clean up old images if requested
    if [[ "${CLEAN_OLD_IMAGES:-false}" == "true" ]]; then
        log "Cleaning up old images..."
        docker image prune -f &> /dev/null || true
    fi
    
    log_success "Cleanup completed"
}

show_usage() {
    cat << EOF
STRAT Trading System - Deployment Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -t, --type TYPE         Deployment type (kubernetes|docker-compose) [default: kubernetes]
    -e, --environment ENV   Environment (production|staging|development) [default: production]
    -n, --namespace NS      Kubernetes namespace [default: strat-trading]
    -v, --version VERSION   Image version to deploy [default: latest]
    -r, --registry REGISTRY Container registry URL
    --dry-run              Show what would be deployed without making changes
    --skip-health-check    Skip health checks after deployment
    --no-rollback          Disable automatic rollback on failure
    --timeout SECONDS      Deployment timeout in seconds [default: 600]
    --clean-images         Clean up old images after deployment
    -h, --help             Show this help message

EXAMPLES:
    # Deploy to Kubernetes production
    $0 --type kubernetes --environment production --version v1.0.0

    # Deploy to Docker Compose for staging
    $0 --type docker-compose --environment staging

    # Dry run deployment
    $0 --dry-run

ENVIRONMENT VARIABLES:
    DEPLOYMENT_TYPE         Deployment type [default: kubernetes]
    ENVIRONMENT            Environment name [default: production]
    NAMESPACE              Kubernetes namespace [default: strat-trading]
    VERSION                Image version [default: latest]
    REGISTRY               Container registry URL
    DRY_RUN                Dry run mode [default: false]
    SKIP_HEALTH_CHECK      Skip health checks [default: false]
    ROLLBACK_ON_FAILURE    Enable rollback [default: true]
    WAIT_TIMEOUT           Timeout in seconds [default: 600]
EOF
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --skip-health-check)
                SKIP_HEALTH_CHECK="true"
                shift
                ;;
            --no-rollback)
                ROLLBACK_ON_FAILURE="false"
                shift
                ;;
            --timeout)
                WAIT_TIMEOUT="$2"
                shift 2
                ;;
            --clean-images)
                CLEAN_OLD_IMAGES="true"
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
    
    # Execute deployment pipeline
    log "Starting STRAT Trading System deployment"
    log "Type: $DEPLOYMENT_TYPE"
    log "Environment: $ENVIRONMENT"
    log "Version: $VERSION"
    log "Namespace: $NAMESPACE"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi
    
    check_requirements
    validate_configuration
    
    if [[ "$DRY_RUN" != "true" ]]; then
        create_backup
    fi
    
    # Deploy based on type
    case "$DEPLOYMENT_TYPE" in
        "kubernetes")
            deploy_kubernetes
            ;;
        "docker-compose")
            deploy_docker_compose
            ;;
    esac
    
    if [[ "$DRY_RUN" != "true" ]]; then
        if wait_for_deployment && perform_health_checks; then
            show_deployment_status
            cleanup
            log_success "Deployment completed successfully!"
        else
            if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
                rollback_deployment
            fi
            exit 1
        fi
    else
        log_success "Dry run completed successfully!"
    fi
}

# Execute main function with all arguments
main "$@"
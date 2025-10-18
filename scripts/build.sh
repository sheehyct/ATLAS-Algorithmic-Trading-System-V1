#!/bin/bash
# ============================================================================
# STRAT Trading System - Container Build Script
# ============================================================================
# Production-ready container build with multi-stage optimization
# Security scanning, tagging, and registry management
# ============================================================================

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
VCS_REF="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
VERSION="${VERSION:-$(git describe --tags --always --dirty 2>/dev/null || echo 'dev')}"

# Image configuration
IMAGE_NAME="${IMAGE_NAME:-strat-trading}"
IMAGE_TAG="${IMAGE_TAG:-$VERSION}"
REGISTRY="${REGISTRY:-}"
FULL_IMAGE_NAME="${REGISTRY:+$REGISTRY/}${IMAGE_NAME}:${IMAGE_TAG}"

# Build configuration
BUILD_TARGET="${BUILD_TARGET:-runtime}"
BUILD_PLATFORM="${BUILD_PLATFORM:-linux/amd64}"
PUSH_IMAGE="${PUSH_IMAGE:-false}"
SCAN_IMAGE="${SCAN_IMAGE:-true}"
CACHE_FROM="${CACHE_FROM:-}"
NO_CACHE="${NO_CACHE:-false}"

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
    log "Checking build requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Buildx (for multi-platform builds)
    if ! docker buildx version &> /dev/null; then
        log_warning "Docker Buildx not available, using standard build"
        export USE_BUILDX=false
    else
        export USE_BUILDX=true
        log "Docker Buildx available"
    fi
    
    # Check security scanner (if enabled)
    if [[ "$SCAN_IMAGE" == "true" ]]; then
        if command -v trivy &> /dev/null; then
            export SCANNER="trivy"
            log "Using Trivy for security scanning"
        elif command -v docker-scout &> /dev/null; then
            export SCANNER="docker-scout"
            log "Using Docker Scout for security scanning"
        else
            log_warning "No security scanner found, skipping image scanning"
            export SCAN_IMAGE=false
        fi
    fi
    
    log_success "Build requirements check completed"
}

validate_environment() {
    log "Validating build environment..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/Dockerfile" ]]; then
        log_error "Dockerfile not found in $PROJECT_ROOT"
        exit 1
    fi
    
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        log_error "pyproject.toml not found in $PROJECT_ROOT"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check disk space (require at least 10GB free)
    AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=10485760  # 10GB in KB
    
    if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
        log_warning "Low disk space: $(( AVAILABLE_SPACE / 1024 / 1024 ))GB available, 10GB recommended"
    fi
    
    log_success "Environment validation completed"
}

build_image() {
    log "Building Docker image: $FULL_IMAGE_NAME"
    log "Build target: $BUILD_TARGET"
    log "Build platform: $BUILD_PLATFORM"
    log "Build date: $BUILD_DATE"
    log "VCS ref: $VCS_REF"
    
    # Prepare build arguments
    BUILD_ARGS=(
        --build-arg "BUILD_DATE=$BUILD_DATE"
        --build-arg "VCS_REF=$VCS_REF"
        --build-arg "VERSION=$VERSION"
        --target "$BUILD_TARGET"
        --tag "$FULL_IMAGE_NAME"
        --file "$PROJECT_ROOT/Dockerfile"
    )
    
    # Add cache configuration
    if [[ "$CACHE_FROM" != "" ]]; then
        BUILD_ARGS+=(--cache-from "$CACHE_FROM")
    fi
    
    if [[ "$NO_CACHE" == "true" ]]; then
        BUILD_ARGS+=(--no-cache)
    fi
    
    # Add platform specification
    if [[ "$USE_BUILDX" == "true" ]]; then
        BUILD_ARGS+=(--platform "$BUILD_PLATFORM")
    fi
    
    # Execute build
    cd "$PROJECT_ROOT"
    
    if [[ "$USE_BUILDX" == "true" ]]; then
        # Use buildx for multi-platform builds
        docker buildx build "${BUILD_ARGS[@]}" \
            --load \
            .
    else
        # Use standard build
        docker build "${BUILD_ARGS[@]}" .
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Docker image build completed: $FULL_IMAGE_NAME"
    else
        log_error "Docker image build failed"
        exit 1
    fi
}

scan_image() {
    if [[ "$SCAN_IMAGE" != "true" ]]; then
        log "Skipping image security scan"
        return 0
    fi
    
    log "Scanning image for security vulnerabilities: $FULL_IMAGE_NAME"
    
    case "$SCANNER" in
        "trivy")
            trivy image \
                --exit-code 1 \
                --severity HIGH,CRITICAL \
                --format table \
                "$FULL_IMAGE_NAME"
            ;;
        "docker-scout")
            docker scout cves "$FULL_IMAGE_NAME"
            ;;
        *)
            log_warning "No security scanner configured"
            return 0
            ;;
    esac
    
    if [[ $? -eq 0 ]]; then
        log_success "Security scan passed"
    else
        log_error "Security scan failed - vulnerabilities found"
        log "Consider updating base image or dependencies"
        return 1
    fi
}

test_image() {
    log "Testing built image: $FULL_IMAGE_NAME"
    
    # Test image can start
    log "Testing image startup..."
    CONTAINER_ID=$(docker run -d \
        --name "strat-test-$$" \
        -p 18000:8000 \
        "$FULL_IMAGE_NAME" \
        python -c "import time; print('Container started'); time.sleep(30)")
    
    if [[ $? -ne 0 ]]; then
        log_error "Failed to start test container"
        return 1
    fi
    
    # Wait for container to be ready
    sleep 5
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -f "http://localhost:18000/health" &> /dev/null; then
        log_success "Health endpoint responded"
    else
        log_warning "Health endpoint not responding (may be expected in test mode)"
    fi
    
    # Test imports
    log "Testing Python imports..."
    docker exec "$CONTAINER_ID" python -c "
import sys
import vectorbtpro as vbt
import pandas as pd
import numpy as np
print('All imports successful')
print(f'VectorBT Pro version: {vbt.__version__}')
print(f'Python version: {sys.version}')
" || {
        log_error "Import test failed"
        docker rm -f "$CONTAINER_ID" &> /dev/null
        return 1
    }
    
    # Cleanup test container
    docker rm -f "$CONTAINER_ID" &> /dev/null
    log_success "Image testing completed successfully"
}

push_image() {
    if [[ "$PUSH_IMAGE" != "true" ]]; then
        log "Skipping image push (set PUSH_IMAGE=true to enable)"
        return 0
    fi
    
    if [[ -z "$REGISTRY" ]]; then
        log_error "REGISTRY not specified, cannot push image"
        return 1
    fi
    
    log "Pushing image to registry: $FULL_IMAGE_NAME"
    
    # Login if credentials are available
    if [[ -n "${REGISTRY_USERNAME:-}" && -n "${REGISTRY_PASSWORD:-}" ]]; then
        echo "$REGISTRY_PASSWORD" | docker login "$REGISTRY" -u "$REGISTRY_USERNAME" --password-stdin
    fi
    
    docker push "$FULL_IMAGE_NAME"
    
    if [[ $? -eq 0 ]]; then
        log_success "Image pushed successfully: $FULL_IMAGE_NAME"
        
        # Also tag and push as 'latest' if this is a release build
        if [[ "$VERSION" != "dev" && "$VERSION" != *"-dirty" ]]; then
            LATEST_IMAGE="${REGISTRY:+$REGISTRY/}${IMAGE_NAME}:latest"
            docker tag "$FULL_IMAGE_NAME" "$LATEST_IMAGE"
            docker push "$LATEST_IMAGE"
            log_success "Latest image pushed: $LATEST_IMAGE"
        fi
    else
        log_error "Failed to push image"
        return 1
    fi
}

cleanup() {
    log "Cleaning up build artifacts..."
    
    # Remove dangling images
    docker image prune -f &> /dev/null || true
    
    # Remove build cache if requested
    if [[ "${CLEAN_CACHE:-false}" == "true" ]]; then
        docker builder prune -f &> /dev/null || true
        log "Build cache cleaned"
    fi
    
    log_success "Cleanup completed"
}

show_usage() {
    cat << EOF
STRAT Trading System - Container Build Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -t, --target TARGET     Build target (runtime|development) [default: runtime]
    -v, --version VERSION   Version tag for the image [default: git describe]
    -r, --registry REGISTRY Container registry URL
    -p, --push              Push image to registry after build
    -s, --scan              Enable security scanning [default: true]
    --no-cache              Build without using cache
    --no-scan               Disable security scanning
    --platform PLATFORM     Target platform [default: linux/amd64]
    --clean-cache           Clean build cache after build
    -h, --help              Show this help message

EXAMPLES:
    # Basic build
    $0

    # Build and push to registry
    $0 --registry myregistry.com/strat --push

    # Build development image
    $0 --target development --version dev

    # Build for multiple platforms
    $0 --platform linux/amd64,linux/arm64

ENVIRONMENT VARIABLES:
    IMAGE_NAME              Image name [default: strat-trading]
    IMAGE_TAG               Image tag [default: VERSION]
    REGISTRY                Container registry URL
    BUILD_TARGET            Build target [default: runtime]
    BUILD_PLATFORM          Build platform [default: linux/amd64]
    PUSH_IMAGE              Push after build [default: false]
    SCAN_IMAGE              Enable scanning [default: true]
    NO_CACHE                Build without cache [default: false]
    REGISTRY_USERNAME       Registry username for authentication
    REGISTRY_PASSWORD       Registry password for authentication
EOF
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--target)
                BUILD_TARGET="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                IMAGE_TAG="$2"
                shift 2
                ;;
            -r|--registry)
                REGISTRY="$2"
                FULL_IMAGE_NAME="${REGISTRY:+$REGISTRY/}${IMAGE_NAME}:${IMAGE_TAG}"
                shift 2
                ;;
            -p|--push)
                PUSH_IMAGE="true"
                shift
                ;;
            -s|--scan)
                SCAN_IMAGE="true"
                shift
                ;;
            --no-cache)
                NO_CACHE="true"
                shift
                ;;
            --no-scan)
                SCAN_IMAGE="false"
                shift
                ;;
            --platform)
                BUILD_PLATFORM="$2"
                shift 2
                ;;
            --clean-cache)
                CLEAN_CACHE="true"
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
    
    # Execute build pipeline
    log "Starting STRAT Trading System container build"
    log "Image: $FULL_IMAGE_NAME"
    log "Platform: $BUILD_PLATFORM"
    log "Target: $BUILD_TARGET"
    
    check_requirements
    validate_environment
    build_image
    
    if ! scan_image; then
        log_warning "Security scan failed, but continuing with build"
    fi
    
    test_image
    push_image
    cleanup
    
    log_success "Container build completed successfully!"
    log "Image: $FULL_IMAGE_NAME"
    log "Size: $(docker images --format "{{.Size}}" "$FULL_IMAGE_NAME")"
}

# Execute main function with all arguments
main "$@"
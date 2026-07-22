#!/usr/bin/env bash
# =============================================================================
# Finalat - Database Migration Deployment Script
# =============================================================================
# Runs Alembic migrations against the target database during deployment.
# This script is executed by CI/CD before the new backend code becomes active.
#
# Usage:
#   ./infrastructure/scripts/deploy-migrations.sh [--check] [--rollback <revision>]
#
# Options:
#   --check      Verify pending migrations without applying them
#   --rollback   Roll back to a specific revision
#
# Required environment variables:
#   DATABASE_URL  - PostgreSQL connection string
#                   Format: postgresql+asyncpg://user:password@host:5432/finalat
#
# Optional environment variables:
#   ALEMBIC_CONFIG - Path to alembic.ini (default: backend/alembic.ini)
#   MAX_RETRIES    - Max connection retries (default: 5)
#   RETRY_DELAY    - Seconds between retries (default: 3)
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
ALEMBIC_CONFIG="${ALEMBIC_CONFIG:-${BACKEND_DIR}/alembic.ini}"
MAX_RETRIES="${MAX_RETRIES:-5}"
RETRY_DELAY="${RETRY_DELAY:-3}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate required environment variables
validate_env() {
    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL environment variable is not set."
        log_error "Expected format: postgresql+asyncpg://user:password@host:5432/finalat"
        exit 1
    fi

    # Convert asyncpg URL to psycopg2 format for Alembic (sync driver)
    # Alembic needs a synchronous driver
    SYNC_DATABASE_URL="${DATABASE_URL//postgresql+asyncpg/postgresql+psycopg2}"
    SYNC_DATABASE_URL="${SYNC_DATABASE_URL//postgresql+aiosqlite/sqlite}"
    export SYNC_DATABASE_URL

    log_info "Database URL validated (connection details hidden for security)."
}

# Wait for database to be available
wait_for_database() {
    log_info "Checking database connectivity..."

    local retries=0
    local db_host
    local db_port

    # Extract host and port from DATABASE_URL
    db_host=$(echo "${DATABASE_URL}" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    db_port=$(echo "${DATABASE_URL}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

    if [ -z "${db_host}" ] || [ -z "${db_port}" ]; then
        log_warn "Could not parse host/port from DATABASE_URL. Skipping connectivity check."
        return 0
    fi

    while [ ${retries} -lt ${MAX_RETRIES} ]; do
        if nc -z -w 5 "${db_host}" "${db_port}" 2>/dev/null; then
            log_info "Database is reachable at ${db_host}:${db_port}."
            return 0
        fi

        retries=$((retries + 1))
        log_warn "Database not reachable (attempt ${retries}/${MAX_RETRIES}). Retrying in ${RETRY_DELAY}s..."
        sleep "${RETRY_DELAY}"
    done

    log_error "Could not connect to database at ${db_host}:${db_port} after ${MAX_RETRIES} attempts."
    exit 1
}

# Check current migration status
check_status() {
    log_info "Checking current migration status..."
    cd "${BACKEND_DIR}"
    alembic -c "${ALEMBIC_CONFIG}" current
}

# Show pending migrations
show_pending() {
    log_info "Checking for pending migrations..."
    cd "${BACKEND_DIR}"

    local current
    current=$(alembic -c "${ALEMBIC_CONFIG}" current 2>&1 | grep -oP '[a-f0-9]+' | head -1 || echo "none")

    local head
    head=$(alembic -c "${ALEMBIC_CONFIG}" heads 2>&1 | grep -oP '[a-f0-9]+' | head -1 || echo "none")

    if [ "${current}" = "${head}" ]; then
        log_info "Database is up to date. No pending migrations."
        return 1
    else
        log_info "Current revision: ${current}"
        log_info "Head revision: ${head}"
        log_info "Pending migrations exist."
        return 0
    fi
}

# Run migrations
run_migrations() {
    log_info "Running database migrations..."
    cd "${BACKEND_DIR}"

    # Create a backup reference point
    local current_rev
    current_rev=$(alembic -c "${ALEMBIC_CONFIG}" current 2>&1 | grep -oP '[a-f0-9]+' | head -1 || echo "none")
    log_info "Pre-migration revision: ${current_rev}"

    # Run upgrade to head
    if alembic -c "${ALEMBIC_CONFIG}" upgrade head; then
        log_info "Migrations completed successfully."
        local new_rev
        new_rev=$(alembic -c "${ALEMBIC_CONFIG}" current 2>&1 | grep -oP '[a-f0-9]+' | head -1 || echo "none")
        log_info "Post-migration revision: ${new_rev}"
    else
        log_error "Migration failed!"
        log_error "Pre-migration revision was: ${current_rev}"
        log_error "You may need to manually roll back: alembic downgrade ${current_rev}"
        exit 1
    fi
}

# Rollback to a specific revision
rollback_migration() {
    local target_revision="$1"
    log_warn "Rolling back to revision: ${target_revision}"
    cd "${BACKEND_DIR}"

    if alembic -c "${ALEMBIC_CONFIG}" downgrade "${target_revision}"; then
        log_info "Rollback to ${target_revision} completed successfully."
    else
        log_error "Rollback failed!"
        exit 1
    fi
}

# Main execution
main() {
    log_info "=== Finalat Database Migration Deployment ==="
    log_info "Project root: ${PROJECT_ROOT}"
    log_info "Alembic config: ${ALEMBIC_CONFIG}"

    validate_env

    # Parse arguments
    local mode="deploy"
    local rollback_target=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --check)
                mode="check"
                shift
                ;;
            --rollback)
                mode="rollback"
                rollback_target="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Usage: $0 [--check] [--rollback <revision>]"
                exit 1
                ;;
        esac
    done

    # Wait for database connectivity
    wait_for_database

    case "${mode}" in
        check)
            check_status
            show_pending || true
            ;;
        rollback)
            if [ -z "${rollback_target}" ]; then
                log_error "Rollback target revision is required."
                exit 1
            fi
            rollback_migration "${rollback_target}"
            ;;
        deploy)
            check_status
            if show_pending; then
                run_migrations
            fi
            ;;
    esac

    log_info "=== Migration deployment complete ==="
}

main "$@"

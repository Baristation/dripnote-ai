#!/bin/bash

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-$(dirname "$0")/compose.blue-green.yml}"
NGINX_CONF="${NGINX_CONF:-$(dirname "$0")/../nginx/nginx.conf}"

HEALTH_CHECK_ATTEMPTS="${HEALTH_CHECK_ATTEMPTS:-12}"
HEALTH_CHECK_DELAY="${HEALTH_CHECK_DELAY:-5}"
BEFORE_HEALTH_CHECK_DELAY="${BEFORE_HEALTH_CHECK_DELAY:-15}"

log_section() {
    local title="$1"

    echo ""
    echo "========== ${title} =========="
}

get_runtime_upstream() {
    docker exec nginx nginx -T 2>/dev/null | grep -oE 'ai-api-(blue|green):8000' | head -n 1 || true
}

log_runtime_state() {
    local label="$1"

    log_section "${label}"
    echo "Compose file: ${COMPOSE_FILE}"
    echo "Deploy script nginx config: ${NGINX_CONF}"

    echo "Deploy script nginx config upstream:"
    grep -E 'ai-api-(blue|green):8000' "${NGINX_CONF}" || true

    echo "Runtime nginx upstream:"
    get_runtime_upstream

    echo "App containers:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -E 'NAMES|ai-api-' || true
}

assert_runtime_upstream() {
    local expected_color="$1"
    local runtime_upstream

    runtime_upstream="$(get_runtime_upstream)"
    if [ "${runtime_upstream}" != "ai-api-${expected_color}:8000" ]; then
        echo "Runtime nginx upstream mismatch"
        echo "Expected: ai-api-${expected_color}:8000"
        echo "Actual: ${runtime_upstream:-<empty>}"
        log_runtime_state "Runtime state after upstream mismatch"
        exit 1
    fi
}

opposite_color() {
    local color="$1"

    if [ "${color}" = "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

get_nginx_upstream_color() {
    if grep -q 'ai-api-blue:8000' "${NGINX_CONF}"; then
        echo "blue"
        return 0
    fi

    if grep -q 'ai-api-green:8000' "${NGINX_CONF}"; then
        echo "green"
        return 0
    fi

    return 1
}

is_container_running() {
    local container="$1"

    docker ps --format '{{.Names}}' | grep -qx "${container}"
}

quick_health_check() {
    local container="$1"
    local response

    response=$(docker exec "${container}" curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
    [ "${response}" = "200" ]
}

health_check() {
    local container="$1"

    echo "Performing health check for ${container}"

    for attempt in $(seq 1 "${HEALTH_CHECK_ATTEMPTS}"); do
        local response
        response=$(docker exec "${container}" curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")

        if [ "${response}" = "200" ]; then
            echo "Health check passed (${attempt}/${HEALTH_CHECK_ATTEMPTS})"
            return 0
        fi

        echo "Health check failed (${attempt}/${HEALTH_CHECK_ATTEMPTS}), response=${response}"
        sleep "${HEALTH_CHECK_DELAY}"
    done

    return 1
}

set_nginx_upstream() {
    local color="$1"

    if ! grep -qE 'ai-api-(blue|green):8000' "${NGINX_CONF}"; then
        echo "Cannot find blue/green upstream in ${NGINX_CONF}"
        exit 1
    fi

    sed -i -E "s/ai-api-(blue|green):8000/ai-api-${color}:8000/g" "${NGINX_CONF}"
    docker exec nginx nginx -t
    docker exec nginx nginx -s reload
    assert_runtime_upstream "${color}"
}

find_healthy_running_color() {
    for color in blue green; do
        local container="ai-api-${color}"
        if is_container_running "${container}" && quick_health_check "${container}"; then
            echo "${color}"
            return 0
        fi
    done

    return 1
}

switch_container() {
    local current="$1"
    local next="$2"

    log_runtime_state "Before starting ai-api-${next}"

    echo "Starting ai-api-${next}"
    docker compose -f "${COMPOSE_FILE}" up -d "ai-api-${next}"

    echo "Waiting ${BEFORE_HEALTH_CHECK_DELAY}s before health check"
    sleep "${BEFORE_HEALTH_CHECK_DELAY}"

    if ! health_check "ai-api-${next}"; then
        echo "Health check failed for ai-api-${next}, rolling back"
        docker stop "ai-api-${next}" 2>/dev/null || true
        docker rm "ai-api-${next}" 2>/dev/null || true
        if is_container_running "ai-api-${current}" && quick_health_check "ai-api-${current}"; then
            echo "Restoring nginx upstream to ai-api-${current}"
            set_nginx_upstream "${current}"
        fi
        exit 1
    fi

    echo "Switching nginx upstream: ${current} -> ${next}"
    set_nginx_upstream "${next}"
    log_runtime_state "After switching nginx upstream to ai-api-${next}"

    echo "Stopping ai-api-${current}"
    docker stop "ai-api-${current}" 2>/dev/null || true
    docker rm "ai-api-${current}" 2>/dev/null || true
    log_runtime_state "After stopping ai-api-${current}"
}

log_runtime_state "Initial runtime state"

current="$(get_nginx_upstream_color || true)"

if [ -z "${current}" ]; then
    echo "Cannot determine current nginx upstream from ${NGINX_CONF}"
    exit 1
fi

if ! is_container_running "ai-api-${current}"; then
    fallback="$(find_healthy_running_color || true)"
    if [ -n "${fallback}" ]; then
        echo "Nginx points to ai-api-${current}, but only ai-api-${fallback} is healthy. Restoring nginx upstream."
        set_nginx_upstream "${fallback}"
        current="${fallback}"
    else
        echo "No healthy current container found. Proceeding with initial deploy from configured upstream: ${current}"
    fi
fi

next="$(opposite_color "${current}")"

if [ "${current}" = "green" ]; then
    echo "### GREEN -> BLUE ###"
else
    echo "### BLUE -> GREEN ###"
fi

switch_container "${current}" "${next}"

log_runtime_state "Final runtime state"
echo "Deployment completed successfully"

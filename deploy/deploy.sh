#!/bin/bash

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-$(dirname "$0")/compose.blue-green.yml}"
NGINX_CONF="${NGINX_CONF:-$(dirname "$0")/../nginx/nginx.conf}"

HEALTH_CHECK_ATTEMPTS="${HEALTH_CHECK_ATTEMPTS:-12}"
HEALTH_CHECK_DELAY="${HEALTH_CHECK_DELAY:-5}"
BEFORE_HEALTH_CHECK_DELAY="${BEFORE_HEALTH_CHECK_DELAY:-15}"

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

switch_container() {
    local current="$1"
    local next="$2"

    echo "Starting ai-api-${next}"
    docker compose -f "${COMPOSE_FILE}" up -d "ai-api-${next}"

    echo "Waiting ${BEFORE_HEALTH_CHECK_DELAY}s before health check"
    sleep "${BEFORE_HEALTH_CHECK_DELAY}"

    if ! health_check "ai-api-${next}"; then
        echo "Health check failed for ai-api-${next}, rolling back"
        docker stop "ai-api-${next}" 2>/dev/null || true
        docker rm "ai-api-${next}" 2>/dev/null || true
        exit 1
    fi

    echo "Switching nginx upstream: ${current} -> ${next}"
    sed -i "s/set \$upstream \"ai-api-${current}:8000\"/set \$upstream \"ai-api-${next}:8000\"/" "${NGINX_CONF}"
    docker exec nginx nginx -s reload

    echo "Stopping ai-api-${current}"
    docker stop "ai-api-${current}" 2>/dev/null || true
    docker rm "ai-api-${current}" 2>/dev/null || true
}

if docker ps --format '{{.Names}}' | grep -qx 'ai-api-green'; then
    echo "### GREEN -> BLUE ###"
    switch_container "green" "blue"
else
    echo "### BLUE -> GREEN ###"
    switch_container "blue" "green"
fi

echo "Deployment completed successfully"

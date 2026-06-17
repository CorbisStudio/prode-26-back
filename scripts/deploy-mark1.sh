#!/usr/bin/env bash
set -euo pipefail

# Deploy de prode-back a mark1 (MicroK8s). Correr SIEMPRE desde mark1.
# El registry localhost:32000 es HTTP-only e interno: buildear/pushear desde el server.

ENV="${1:-prod}"
IMAGEN="localhost:32000/prode-back"
NAMESPACE="prode-prod"
BRANCH="${2:-master}"

echo "==> Deploy prode-back → $ENV (rama $BRANCH)"

echo "--- git pull"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "--- docker build"
docker build -t "${IMAGEN}:${ENV}" .

echo "--- docker push"
docker push "${IMAGEN}:${ENV}"

echo "--- rollout restart (web + worker + beat)"
microk8s kubectl -n "$NAMESPACE" rollout restart deployment/prode-back deployment/prode-back-worker deployment/prode-back-beat

echo "--- esperando rollout web..."
microk8s kubectl -n "$NAMESPACE" rollout status deployment/prode-back --timeout=240s

echo "==> Deploy completado"
microk8s kubectl -n "$NAMESPACE" get pods

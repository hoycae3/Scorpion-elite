#!/bin/bash
# Script de prueba de Supabase - lee credenciales de variables de entorno o .env

# Cargar .env si existe
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs) 2>/dev/null
fi

SUPABASE_URL="${SUPABASE_URL:-https://jjtifureeygvygxtpuku.supabase.co}"
SUPABASE_KEY="${SUPABASE_KEY:-$SUPABASE_ANON_KEY}"

if [ -z "$SUPABASE_KEY" ]; then
  echo "ERROR: SUPABASE_KEY (o SUPABASE_ANON_KEY) no configurada."
  echo "Definela en .env o como variable de entorno."
  exit 1
fi

API_BASE="${SUPABASE_URL}/rest/v1"

echo "=== PASO 1: Ver tablas Supabase ==="
curl -s "${API_BASE}/partidos?select=fixture_id,liga&limit=3" \
  -H "apikey: ${SUPABASE_KEY}"

echo ""
echo "=== PASO 2: Probar INSERT ==="
curl -X POST "${API_BASE}/partidos" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d '[{"fixture_id": 99999999, "fecha": "2026-08-01", "hora": "18:00", "liga": "TEST", "equipo_local": "Test Local", "equipo_visitante": "Test Visita"}]'

echo ""
echo "=== PASO 3: Verificar INSERT ==="
curl -s "${API_BASE}/partidos?fixture_id=eq.99999999" \
  -H "apikey: ${SUPABASE_KEY}"

echo ""
echo "=== PASO 4: Probar UPSERT ==="
curl -X POST "${API_BASE}/partidos" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d '[{"fixture_id": 99999999, "fecha": "2026-08-02", "hora": "19:00", "liga": "TEST UPDATED"}]'

echo ""
echo "=== PASO 5: Verificar UPSERT ==="
curl -s "${API_BASE}/partidos?fixture_id=eq.99999999" \
  -H "apikey: ${SUPABASE_KEY}"

echo ""
echo "=== PASO 6: Verificar equipos_stats ==="
curl -s "${API_BASE}/equipos_stats?select=equipo&limit=3" \
  -H "apikey: ${SUPABASE_KEY}"

echo ""
echo "=== FIN PRUEBA ==="

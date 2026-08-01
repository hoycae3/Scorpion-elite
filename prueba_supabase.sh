#!/bin/bash

echo "=== PASO 1: Ver tablas Supabase ==="
curl -s "https://jjtifureeygvygxtpuku.supabase.co/rest/v1/partidos?select=fixture_id,liga&limit=3" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJleWV5Z3Z5Z3h0cHVrdSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjUxNjI0MTYwfQ.MjkSD5xjFyOyTVdV3F0KZG_t5gk27F9xBRcaL2VEuB4c"

echo ""
echo "=== PASO 2: Probar INSERT ==="
curl -X POST "https://jjtifureeygvygxtpuku.supabase.co/rest/v1/partidos" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJleWV5Z3Z5Z3h0cHVrdSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjUxNjI0MTYwfQ.MjkSD5xjFyOyTVdV3F0KZG_t5gk27F9xBRcaL2VEuB4c" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d '[{"fixture_id": 99999999, "fecha": "2026-08-01", "hora": "18:00", "liga": "TEST", "equipo_local": "Test Local", "equipo_visitante": "Test Visita"}]'

echo ""
echo "=== PASO 3: Verificar INSERT ==="
curl -s "https://jjtifureeygvygxtpuku.supabase.co/rest/v1/partidos?fixture_id=eq.99999999" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJleWV5Z3Z5Z3h0cHVrdSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjUxNjI0MTYwfQ.MjkSD5xjFyOyTVdV3F0KZG_t5gk27F9xBRcaL2VEuB4c"

echo ""
echo "=== PASO 4: Probar UPSERT ==="
curl -X POST "https://jjtifureeygvygxtpuku.supabase.co/rest/v1/partidos" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJleWV5Z3Z5Z3h0cHVrdSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjUxNjI0MTYwfQ.MjkSD5xjFyOyTVdV3F0KZG_t5gk27F9xBRcaL2VEuB4c" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d '[{"fixture_id": 99999999, "fecha": "2026-08-02", "hora": "19:00", "liga": "TEST UPDATED"}]'

echo ""
echo "=== PASO 5: Verificar UPSERT ==="
curl -s "https://jjtifureeygvygxtpuku.supabase.co/rest/v1/partidos?fixture_id=eq.99999999" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJleWV5Z3Z5Z3h0cHVrdSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjUxNjI0MTYwfQ.MjkSD5xjFyOyTVdV3F0KZG_t5gk27F9xBRcaL2VEuB4c"

echo ""
echo "=== PASO 6: Verificar equipos_stats ==="
curl -s "https://jjtifureeygvygxtpuku.supabase.co/rest/v1/equipos_stats?select=equipo&limit=3" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJleWV5Z3Z5Z3h0cHVrdSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjUxNjI0MTYwfQ.MjkSD5xjFyOyTVdV3F0KZG_t5gk27F9xBRcaL2VEuB4c"

echo ""
echo "=== FIN PRUEBA ==="

import dash
from dash import dcc, html, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import requests
import os

# ══════════════════════════════════════════════════════════
# CONFIG - Usar variables de entorno
# ══════════════════════════════════════════════════════════
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")

# ══════════════════════════════════════════════════════════
# INICIALIZACIÓN DASH
# ══════════════════════════════════════════════════════════
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True
)
app.title = "SCORPION ELITE - Dashboard"

# ══════════════════════════════════════════════════════════
# ESTILOS
# ══════════════════════════════════════════════════════════
SIDEBAR_STYLE = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0,
    "width": "16rem", "padding": "1rem 1rem",
    "background-color": "#0d1117", "border-right": "1px solid #30363d"
}

CONTENT_STYLE = {
    "margin-left": "17rem", "margin-right": "1rem",
    "padding": "1rem 1rem", "background-color": "#090d12"
}

CARD_STYLE = {
    "background-color": "#161b22", "border": "1px solid #30363d",
    "border-radius": "8px", "padding": "15px", "margin-bottom": "15px"
}

# ══════════════════════════════════════════════════════════
# FUNCIONES API
# ══════════════════════════════════════════════════════════
def buscar_equipos(nombre):
    """Busca equipos en Football-Data."""
    resultados = []
    if not nombre or len(nombre) < 2 or not FOOTBALL_DATA_KEY:
        return resultados
    
    try:
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        leagues = [
            ("PD", "La Liga"), ("PL", "Premier League"),
            ("BL1", "Bundesliga"), ("SA", "Serie A"),
            ("FL1", "Ligue 1"), ("PPL", "Primeira Liga"),
            ("DED", "Eredivisie"),
        ]
        
        for league_code, league_name in leagues:
            url = f"https://api.football-data.org/v4/competitions/{league_code}/teams"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for t in data.get("teams", []):
                    tname = t.get("name", "")
                    if nombre.lower() in tname.lower():
                        resultados.append({
                            "id": t.get("id"),
                            "nombre": tname,
                            "short": t.get("shortName", ""),
                            "pais": t.get("country", ""),
                            "liga": league_name,
                        })
    except Exception as e:
        print(f"Error búsqueda: {e}")
    return resultados

def obtener_stats_equipo(team_id):
    """Obtiene estadísticas de un equipo."""
    if not FOOTBALL_DATA_KEY:
        return None
    try:
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        url = f"https://api.football-data.org/v4/teams/{team_id}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "nombre": data.get("name", ""),
                "liga": data.get("runningCompetition", {}).get("name", "") if data.get("runningCompetition") else "",
                "pais": data.get("country", ""),
                "venue": data.get("venue", ""),
            }
    except:
        pass
    return None

def obtener_cuotas(league_key="soccer_epl"):
    """Obtiene cuotas de The Odds API."""
    if not ODDS_API_KEY:
        return []
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds"
        params = {"apiKey": ODDS_API_KEY, "regions": "eu,us,uk", "markets": "h2h"}
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            matches = r.json()
            resultados = []
            for m in matches[:15]:
                home = m.get("home_team", "")
                away = m.get("away_team", "")
                bookmakers = m.get("bookmakers", [])
                
                mejor_l, mejor_e, mejor_v = 0, 0, 0
                for bm in bookmakers[:3]:
                    for market in bm.get("markets", []):
                        if market.get("key") == "h2h":
                            for o in market.get("outcomes", []):
                                name, price = o.get("name", ""), o.get("price", 0)
                                if "Home" in name or home in name:
                                    if price > mejor_l: mejor_l = price
                                elif "Draw" in name:
                                    if price > mejor_e: mejor_e = price
                                else:
                                    if price > mejor_v: mejor_v = price
                
                if mejor_l > 0:
                    resultados.append({
                        "partido": f"{home} vs {away}",
                        "local": mejor_l, "empate": mejor_e, "visita": mejor_v
                    })
            return resultados
    except Exception as e:
        print(f"Error cuotas: {e}")
    return []

def obtener_clima(ciudad):
    """Obtiene clima de OpenWeather."""
    if not OPENWEATHER_KEY:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": ciudad, "appid": OPENWEATHER_KEY, "units": "metric", "lang": "es"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "ciudad": data.get("name", ""),
                "temp": data.get("main", {}).get("temp", 0),
                "clima": data.get("weather", [{}])[0].get("description", ""),
                "humedad": data.get("main", {}).get("humidity", 0),
            }
    except:
        pass
    return None

# ══════════════════════════════════════════════════════════
# LAYOUT SIDEBAR
# ══════════════════════════════════════════════════════════
sidebar = html.Div([
    html.H4("🦂 SCORPION ELITE", style={'color': '#d97706', 'font-weight': 'bold'}),
    html.P("ANÁLISIS Y TENDENCIAS DEPORTIVAS", style={'color': '#8b949e', 'font-size': '11px'}),
    html.Hr(style={'border-color': '#30363d'}),
    html.Div("MENÚ PRINCIPAL", style={'color': '#8b949e', 'font-size': '12px', 'margin-bottom': '10px'}),
    dbc.Nav([
        dbc.NavLink([html.I(className="bi bi-speedometer2 me-2"), "Dashboard"], href="/", active=True, className="text-warning mb-1"),
        dbc.NavLink([html.I(className="bi bi-bullseye me-2"), "Picks del Día"], href="/picks", className="text-light mb-1"),
        dbc.NavLink([html.I(className="bi bi-broadcast me-2"), "En Vivo", dbc.Badge("5", color="danger", className="ms-2")], href="/live", className="text-light mb-1"),
        dbc.NavLink([html.I(className="bi bi-gem me-2"), "Value Bets"], href="/value", className="text-light mb-1"),
        dbc.NavLink([html.I(className="bi bi-search me-2"), "Buscar Equipos"], href="/equipos", className="text-light mb-1"),
        dbc.NavLink([html.I(className="bi bi-thermometer-half me-2"), "Clima"], href="/clima", className="text-light mb-1"),
    ], vertical=True, pills=True),
    html.Hr(style={'border-color': '#30363d'}),
    html.Div([
        html.P("🦂 Plan Premium", style={'color': '#d97706', 'font-weight': 'bold', 'margin-bottom': '2px'}),
        html.Small("Funciones completas activas", style={'color': '#8b949e'})
    ], style={'background-color': '#161b22', 'padding': '10px', 'border-radius': '6px'})
], style=SIDEBAR_STYLE)

# ══════════════════════════════════════════════════════════
# LAYOUT PRINCIPAL - DASHBOARD
# ══════════════════════════════════════════════════════════
content = html.Div([
    # Top Bar
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("⚽ Fútbol 45", color="success", size="sm"),
                dbc.Button("🏀 Baloncesto 12", color="dark", size="sm", outline=True),
                dbc.Button("🎾 Tenis 8", color="dark", size="sm", outline=True),
            ])
        ], width=6),
        dbc.Col([
            dcc.Input(id="buscar-partido", type="text", placeholder="🔍 Buscar partido o equipo...",
                     style={'background-color': '#161b22', 'color': 'white', 'border-color': '#30363d', 'border-radius': '6px'})
        ], width=6)
    ], className="mb-3 align-items-center"),
    
    dbc.Row([
        # COLUMNA 1: Cuotas
        dbc.Col([
            html.Div([
                html.H6("💰 CUOTAS DE HOY", style={'color': '#d97706', 'font-size': '12px', 'font-weight': 'bold'}),
                dcc.Dropdown(
                    id="liga-selector",
                    options=[
                        {"label": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", "value": "soccer_epl"},
                        {"label": "🇪🇸 La Liga", "value": "soccer_esp La Liga"},
                        {"label": "🇩🇪 Bundesliga", "value": "soccer_deu Bundesliga"},
                        {"label": "🇮🇹 Serie A", "value": "soccer_ita Serie A"},
                        {"label": "🇫🇷 Ligue 1", "value": "soccer_fra Ligue 1"},
                    ],
                    value="soccer_epl",
                    style={'background-color': '#161b22', 'color': 'black'}
                ),
                html.Div(id="cuotas-container", className="mt-3")
            ], style=CARD_STYLE),
        ], width=4),
        
        # COLUMNA 2: Buscar Equipos
        dbc.Col([
            html.Div([
                html.H6("🔍 BUSCAR EQUIPOS", style={'color': '#d97706', 'font-size': '12px', 'font-weight': 'bold'}),
                dbc.Input(id="input-buscar-equipo", type="text", placeholder="Escribe el nombre del equipo...",
                         style={'background-color': '#161b22', 'color': 'white', 'border-color': '#30363d'}),
                html.Button("🔍 Buscar", id="btn-buscar-equipo", n_clicks=0, color="warning", className="mt-2"),
                html.Div(id="resultados-equipos", className="mt-3")
            ], style=CARD_STYLE),
        ], width=4),
        
        # COLUMNA 3: Stats Equipo
        dbc.Col([
            html.Div([
                html.H6("📊 ESTADÍSTICAS", style={'color': '#d97706', 'font-size': '12px', 'font-weight': 'bold'}),
                html.Div(id="stats-equipo", children=[
                    html.P("Busca un equipo para ver sus estadísticas", style={'color': '#8b949e', 'font-size': '12px'})
                ])
            ], style=CARD_STYLE),
            
            html.Div([
                html.H6("🌤️ CLIMA", style={'color': '#d97706', 'font-size': '12px', 'font-weight': 'bold'}),
                dbc.Input(id="input-ciudad-clima", type="text", placeholder="Ciudad (ej: Madrid, Buenos Aires)",
                         style={'background-color': '#161b22', 'color': 'white', 'border-color': '#30363d'}),
                html.Button("🌡️ Ver Clima", id="btn-clima", n_clicks=0, color="info", className="mt-2"),
                html.Div(id="resultado-clima", className="mt-3")
            ], style=CARD_STYLE),
        ], width=4),
    ])
], style=CONTENT_STYLE)

# ══════════════════════════════════════════════════════════
# LAYOUT PAGE: EQUIPOS
# ══════════════════════════════════════════════════════════
page_equipos = html.Div([
    dbc.Row([
        dbc.Col([
            html.H4("🔍 Buscar Equipos", style={'color': 'white'}),
            dbc.Input(id="input-buscar-eq-pag", type="text", placeholder="Nombre del equipo...",
                     style={'background-color': '#161b22', 'color': 'white', 'border-color': '#30363d'}),
            html.Button("🔍 Buscar", id="btn-buscar-eq-pag", n_clicks=0, color="warning", className="mt-2"),
        ], width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div(id="resultados-eq-pag", style=CARD_STYLE)
        ], width=8),
        dbc.Col([
            html.Div(id="detalle-eq", style=CARD_STYLE)
        ], width=4),
    ])
], style=CONTENT_STYLE)

# ══════════════════════════════════════════════════════════
# LAYOUT PAGE: CLIMA
# ══════════════════════════════════════════════════════════
page_clima = html.Div([
    dbc.Row([
        dbc.Col([
            html.H4("🌤️ Clima", style={'color': 'white'}),
            dbc.Input(id="input-clima-pag", type="text", placeholder="Ciudad...",
                     style={'background-color': '#161b22', 'color': 'white', 'border-color': '#30363d', 'width': '300px'}),
            html.Button("🌡️ Buscar", id="btn-clima-pag", n_clicks=0, color="info", className="mt-2 ms-2"),
        ], width=6),
    ], className="mb-4"),
    
    html.Div(id="resultado-clima-pag", style=CARD_STYLE)
], style=CONTENT_STYLE)

# ══════════════════════════════════════════════════════════
# LAYOUT PAGE: PICKS
# ══════════════════════════════════════════════════════════
page_picks = html.Div([
    html.H4("🎯 Picks del Día", style={'color': 'white', 'margin-bottom': '20px'}),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H6("PICK DESTACADO", style={'color': '#d97706', 'font-size': '12px', 'font-weight': 'bold'}),
                html.H4("Manchester City vs Arsenal", style={'color': 'white', 'text-align': 'center'}),
                html.H5("Cuota: 1.91", style={'color': '#10b981', 'text-align': 'center'}),
                dbc.Progress(value=72, color="success", className="mt-3"),
            ], style=CARD_STYLE),
        ], width=6),
        dbc.Col([
            html.Div([
                html.H6("ANÁLISIS IA", style={'color': '#d97706', 'font-size': '12px', 'font-weight': 'bold'}),
                html.Ul([
                    html.Li("City ha ganado 8/10 últimos partidos", style={'color': '#10b981', 'font-size': '12px'}),
                    html.Li("Arsenal con 3 bajas en defensa", style={'color': '#ef4444', 'font-size': '12px'}),
                    html.Li("City promedia 2.4 goles en casa", style={'color': '#8b949e', 'font-size': '12px'}),
                ]),
            ], style=CARD_STYLE),
        ], width=6),
    ])
], style=CONTENT_STYLE)

# ══════════════════════════════════════════════════════════
# LAYOUT PRINCIPAL (multi-página)
# ══════════════════════════════════════════════════════════
app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    html.Div(id="page-content")
])

# ══════════════════════════════════════════════════════════
# CALLBACKS
# ══════════════════════════════════════════════════════════
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def render_page(pathname):
    if pathname == "/equipos":
        return page_equipos
    elif pathname == "/clima":
        return page_clima
    elif pathname == "/picks":
        return page_picks
    elif pathname == "/live":
        return html.Div([
            html.H4("🔴 En Vivo", style={'color': 'white'}),
            html.P("Partidos en vivo aparecerán aquí", style={'color': '#8b949e'})
        ], style={**CONTENT_STYLE})
    elif pathname == "/value":
        return html.Div([
            html.H4("💎 Value Bets", style={'color': 'white'}),
            html.P("Value bets aparecerán aquí", style={'color': '#8b949e'})
        ], style={**CONTENT_STYLE})
    else:
        return content

# Callback: Cuotas
@app.callback(
    Output("cuotas-container", "children"),
    Input("liga-selector", "value")
)
def actualizar_cuotas(liga_key):
    if not ODDS_API_KEY:
        return html.Div([
            html.P("⚠️ Configura ODDS_API_KEY", style={'color': '#ef4444', 'font-size': '12px'}),
            html.P("Agrega la key en las variables de entorno", style={'color': '#8b949e', 'font-size': '11px'}),
        ])
    
    cuotas = obtener_cuotas(liga_key)
    if not cuotas:
        return html.P("No hay cuotas disponibles para esta liga", style={'color': '#8b949e', 'font-size': '12px'})
    
    rows = []
    for c in cuotas[:10]:
        rows.append(
            html.Div([
                html.Div(c['partido'], style={'color': 'white', 'font-size': '12px', 'flex': '2'}),
                html.Div(str(c['local']), style={'color': '#10b981', 'font-size': '12px', 'text-align': 'center', 'flex': '1'}),
                html.Div(str(c['empate']), style={'color': '#8b949e', 'font-size': '12px', 'text-align': 'center', 'flex': '1'}),
                html.Div(str(c['visita']), style={'color': '#10b981', 'font-size': '12px', 'text-align': 'center', 'flex': '1'}),
            ], style={'display': 'flex', 'padding': '8px 0', 'border-bottom': '1px solid #21262d', 'align-items': 'center'})
        )
    
    return html.Div([
        html.Div(["Partido", "1", "X", "2"], style={'display': 'flex', 'color': '#8b949e', 'font-size': '10px', 'padding': '0 0 5px 0'}),
        *rows
    ])

# Callback: Buscar Equipo
@app.callback(
    [Output("resultados-equipos", "children"),
     Output("stats-equipo", "children")],
    Input("btn-buscar-equipo", "n_clicks"),
    State("input-buscar-equipo", "value")
)
def buscar_equipos_callback(n_clicks, nombre):
    if not n_clicks or not nombre:
        return html.P("Escribe un nombre para buscar", style={'color': '#8b949e'}), html.P("Sin datos", style={'color': '#8b949e'})
    
    if not FOOTBALL_DATA_KEY:
        return html.Div([
            html.P("⚠️ Configura FOOTBALL_DATA_KEY", style={'color': '#ef4444', 'font-size': '12px'}),
        ]), html.P("Sin API key", style={'color': '#8b949e'})
    
    resultados = buscar_equipos(nombre)
    if not resultados:
        return html.P(f"No se encontró: {nombre}", style={'color': '#ef4444'}), html.P("Sin resultados", style={'color': '#8b949e'})
    
    items = []
    for eq in resultados[:8]:
        items.append(
            html.Div([
                html.Span(eq['nombre'], style={'color': 'white', 'font-size': '13px'}),
                html.Span(f"  {eq['liga']}", style={'color': '#8b949e', 'font-size': '11px'}),
            ], style={'padding': '8px', 'border-bottom': '1px solid #21262d', 'cursor': 'pointer'})
        )
    
    return html.Div(items), html.Div([
        html.H6(f"📊 {resultados[0]['nombre']}", style={'color': '#10b981'}),
        html.P(f"Liga: {resultados[0]['liga']}", style={'color': '#8b949e', 'font-size': '12px'}),
        html.P(f"País: {resultados[0]['pais']}", style={'color': '#8b949e', 'font-size': '12px'}),
    ])

# Callback: Buscar Equipo Página
@app.callback(
    Output("resultados-eq-pag", "children"),
    Input("btn-buscar-eq-pag", "n_clicks"),
    State("input-buscar-eq-pag", "value")
)
def buscar_equipos_pag(n_clicks, nombre):
    if not n_clicks or not nombre:
        return html.P("Busca un equipo", style={'color': '#8b949e'})
    
    resultados = buscar_equipos(nombre)
    if not resultados:
        return html.P("Sin resultados", style={'color': '#ef4444'})
    
    df = pd.DataFrame([{"Equipo": e['nombre'], "Liga": e['liga'], "País": e['pais']} for e in resultados[:15]])
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in ["Equipo", "Liga", "País"]],
        style_as_list_view=True,
        style_header={'backgroundColor': '#161b22', 'color': '#8b949e', 'fontSize': '11px'},
        style_cell={'backgroundColor': '#161b22', 'color': 'white', 'fontSize': '12px', 'borderBottom': '1px solid #21262d'}
    )

# Callback: Clima
@app.callback(
    Output("resultado-clima", "children"),
    Input("btn-clima", "n_clicks"),
    State("input-ciudad-clima", "value")
)
def ver_clima(n_clicks, ciudad):
    if not n_clicks or not ciudad:
        return html.P("Ingresa una ciudad", style={'color': '#8b949e'})
    
    if not OPENWEATHER_KEY:
        return html.Div([
            html.P("⚠️ Configura OPENWEATHER_KEY", style={'color': '#ef4444', 'font-size': '12px'}),
            html.P("La API se está activando...", style={'color': '#8b949e', 'font-size': '11px'}),
        ])
    
    clima = obtener_clima(ciudad)
    if not clima:
        return html.Div([
            html.P("Clima no disponible", style={'color': '#ef4444', 'font-size': '12px'}),
            html.P("La API de OpenWeather aún se está activando", style={'color': '#8b949e', 'font-size': '11px'}),
        ])
    
    return html.Div([
        html.H5(f"📍 {clima['ciudad']}", style={'color': '#10b981'}),
        html.H4(f"🌡️ {clima['temp']:.1f}°C", style={'color': 'white'}),
        html.P(f"☁️ {clima['clima'].capitalize()}", style={'color': '#8b949e', 'font-size': '12px'}),
        html.P(f"💧 Humedad: {clima['humedad']}%", style={'color': '#8b949e', 'font-size': '12px'}),
    ])

# Callback: Clima Página
@app.callback(
    Output("resultado-clima-pag", "children"),
    Input("btn-clima-pag", "n_clicks"),
    State("input-clima-pag", "value")
)
def ver_clima_pag(n_clicks, ciudad):
    if not n_clicks or not ciudad:
        return html.P("Ingresa una ciudad", style={'color': '#8b949e'})
    
    clima = obtener_clima(ciudad)
    if not clima:
        return html.Div([
            html.P("❌ Clima no disponible", style={'color': '#ef4444'}),
            html.P("La API de OpenWeather está en proceso de activación", style={'color': '#8b949e'}),
        ])
    
    return dbc.Row([
        dbc.Col([
            html.H2(f"🌡️ {clima['temp']:.1f}°C", style={'color': 'white'}),
            html.H5(clima['ciudad'], style={'color': '#10b981'}),
        ], width=4),
        dbc.Col([
            html.P(f"☁️ {clima['clima'].capitalize()}", style={'color': '#8b949e', 'font-size': '16px'}),
            html.P(f"💧 Humedad: {clima['humedad']}%", style={'color': '#8b949e', 'font-size': '14px'}),
        ], width=8),
    ])

# ══════════════════════════════════════════════════════════
# EJECUTAR
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8501)

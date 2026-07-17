import dash
from dash import html, dash_table
import dash_bootstrap_components as dbc


# Inicialización de la app con un tema oscuro
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])
app.title = "SCORPION ELITE"


# Estilos generales para replicar el estilo de la imagen
BG_COLOR = "#070b0e"      # Fondo principal oscuro
CARD_BG = "#0d131a"       # Fondo de las tarjetas
BORDER_COLOR = "#1b2430"  # Bordes sutiles
GREEN_ACCENT = "#22c55e"  # Verde brillante para los números/textos
TITLE_GREEN = "#a3e635"   # Verde lima para títulos
TEXT_MUTED = "#94a3b8"    # Gris para texto secundario


CARD_STYLE = {
    "backgroundColor": CARD_BG,
    "border": f"1px solid {BORDER_COLOR}",
    "borderRadius": "8px",
    "padding": "16px",
    "height": "100%",
}


# --- DATOS ---
data_partidos = [
    {"Partido": "Manchester City\nArsenal", "Hora": "16:00", "Liga": "Premier League"},
    {"Partido": "Real Madrid\nBarcelona", "Hora": "17:30", "Liga": "LaLiga"},
    {"Partido": "Bayern München\nBorussia Dortmund", "Hora": "14:30", "Liga": "Bundesliga"},
    {"Partido": "PSG\nOlympique Lyon", "Hora": "15:00", "Liga": "Ligue 1"},
    {"Partido": "Inter\nAC Milan", "Hora": "20:45", "Liga": "Serie A"},
]


data_comparador = [
    {"CASA": "Pinnacle", "1": "1.91", "X": "3.80", "2": "4.20", "MEJOR": "⭐"},
    {"CASA": "Bet365", "1": "1.87", "X": "3.75", "2": "4.00", "MEJOR": "-"},
    {"CASA": "Betano", "1": "1.85", "X": "3.70", "2": "3.95", "MEJOR": "-"},
    {"CASA": "1xBet", "1": "1.90", "X": "3.78", "2": "4.10", "MEJOR": "-"},
    {"CASA": "Stake", "1": "1.88", "X": "3.76", "2": "4.05", "MEJOR": "-"},
]


# --- LAYOUT ---
app.layout = html.Div(
    style={"backgroundColor": BG_COLOR, "color": "white", "minHeight": "100vh", "padding": "15px"},
    children=[
        # 1. NAVBAR / ENCABEZADO SUPERIOR
        dbc.Row(
            [
                # LOGO
                dbc.Col(
                    html.Div([
                        html.H5("🦂 SCORPION ELITE", className="m-0", style={"color": "#f59e0b", "fontWeight": "bold"}),
                        html.Small("ANÁLISIS Y TENDENCIAS DEPORTIVAS", style={"color": TEXT_MUTED, "fontSize": "10px"})
                    ]),
                    width="auto"
                ),
                # CATEGORÍAS DE DEPORTES
                dbc.Col(
                    dbc.ButtonGroup([
                        dbc.Button("⚽ FÚTBOL", color="success", size="sm", style={"fontSize": "12px", "fontWeight": "bold"}),
                        dbc.Button("🏀 BALONCESTO", color="dark", size="sm", outline=True, style={"fontSize": "12px"}),
                        dbc.Button("🎾 TENIS", color="dark", size="sm", outline=True, style={"fontSize": "12px"}),
                        dbc.Button("🏒 HOCKEY", color="dark", size="sm", outline=True, style={"fontSize": "12px"}),
                        dbc.Button("⚾ BÉISBOL", color="dark", size="sm", outline=True, style={"fontSize": "12px"}),
                        dbc.Button("🥊 MMA", color="dark", size="sm", outline=True, style={"fontSize": "12px"}),
                    ]),
                    width="auto",
                    className="mx-auto"
                ),
                # BUSCADOR Y FECHA
                dbc.Col(
                    html.Div([
                        dbc.Input(
                            placeholder="🔍 Buscar partido o liga...",
                            size="sm",
                            style={"backgroundColor": CARD_BG, "borderColor": BORDER_COLOR, "color": "white", "width": "200px"}
                        ),
                        dbc.Button("📅 Hoy, 7 Mayo 2025 v", size="sm", color="dark", outline=True, className="ms-2", style={"fontSize": "12px"}),
                    ], className="d-flex align-items-center"),
                    width="auto"
                )
            ],
            className="align-items-center mb-4 pb-2",
            style={"borderBottom": f"1px solid {BORDER_COLOR}"}
        ),


        # 2. CONTENIDO PRINCIPAL: 3 COLUMNAS
        dbc.Row([
            
            # --- SECCIÓN 1: PARTIDOS DESTACADOS ---
            dbc.Col([
                html.Div([
                    html.H6("PARTIDOS DESTACADOS", style={"color": TITLE_GREEN, "fontSize": "12px", "fontWeight": "bold"}),
                    dash_table.DataTable(
                        data=data_partidos,
                        columns=[{"name": i, "id": i} for i in ["Partido", "Hora", "Liga"]],
                        style_as_list_view=True,
                        style_header={'display': 'none'},
                        style_cell={
                            'backgroundColor': CARD_BG,
                            'color': 'white',
                            'fontSize': '12px',
                            'borderBottom': f'1px solid {BORDER_COLOR}',
                            'textAlign': 'left',
                            'padding': '10px 5px',
                            'whiteSpace': 'pre-line'
                        },
                        style_cell_conditional=[
                            {'if': {'column_id': 'Hora'}, 'width': '60px', 'color': TEXT_MUTED},
                            {'if': {'column_id': 'Liga'}, 'color': TEXT_MUTED}
                        ]
                    )
                ], style=CARD_STYLE)
            ], md=4),


            # --- SECCIÓN 2: MEJOR PICK DEL DÍA ---
            dbc.Col([
                html.Div([
                    html.H6("MEJOR PICK DEL DÍA", style={"color": TITLE_GREEN, "fontSize": "12px", "fontWeight": "bold"}),
                    
                    html.Div("Premier League - Jornada 36", className="text-center my-1", style={"color": TEXT_MUTED, "fontSize": "11px"}),
                    
                    # Enfrentamiento Central
                    html.Div([
                        html.H5("Manchester City", style={"fontWeight": "bold", "fontSize": "16px", "margin": "0"}),
                        html.Span(" VS ", style={"color": TEXT_MUTED, "margin": "0 10px", "fontSize": "12px"}),
                        html.H5("Arsenal", style={"fontWeight": "bold", "fontSize": "16px", "margin": "0"}),
                    ], className="d-flex align-items-center justify-content-center my-3"),


                    # Caja con Mercado y Cuota Recomendada
                    html.Div([
                        html.Div([
                            html.Small("MERCADO", style={"color": TEXT_MUTED, "fontSize": "9px", "display": "block"}),
                            html.Small("Resultado Final", style={"color": TEXT_MUTED, "fontSize": "11px", "display": "block"}),
                            html.Strong("Manchester City Gana", style={"color": "white", "fontSize": "13px"})
                        ]),
                        html.Div([
                            html.Small("CUOTA RECOMENDADA", style={"color": TEXT_MUTED, "fontSize": "9px", "display": "block"}),
                            html.Div([
                                html.Span("1.91", style={"fontSize": "22px", "fontWeight": "bold", "color": "white", "marginRight": "8px"}),
                                dbc.Badge("Pinnacle", color="secondary", style={"fontSize": "10px", "backgroundColor": "#1e293b"})
                            ], className="d-flex align-items-center")
                        ], className="text-end")
                    ], className="d-flex justify-content-between align-items-center p-2 mb-3", style={"backgroundColor": BG_COLOR, "borderRadius": "6px", "border": f"1px solid {BORDER_COLOR}"}),


                    # Métricas Inferiores
                    dbc.Row([
                        dbc.Col([
                            html.Small("PROBABILIDAD", style={"color": TEXT_MUTED, "fontSize": "9px"}),
                            html.H4("72%", style={"color": GREEN_ACCENT, "margin": "0", "fontWeight": "bold"})
                        ], className="text-center"),
                        dbc.Col([
                            html.Small("CONFIANZA", style={"color": TEXT_MUTED, "fontSize": "9px"}),
                            html.H4("92%", style={"color": GREEN_ACCENT, "margin": "0", "fontWeight": "bold"}),
                            html.Small("MUY ALTA", style={"color": GREEN_ACCENT, "fontSize": "8px", "fontWeight": "bold"})
                        ], className="text-center"),
                        dbc.Col([
                            html.Small("VALOR", style={"color": TEXT_MUTED, "fontSize": "9px"}),
                            html.H4("+19%", style={"color": GREEN_ACCENT, "margin": "0", "fontWeight": "bold"}),
                            html.Small("VALUE BET", style={"color": GREEN_ACCENT, "fontSize": "8px", "fontWeight": "bold"})
                        ], className="text-center"),
                        dbc.Col([
                            html.Small("RIESGO", style={"color": TEXT_MUTED, "fontSize": "9px"}),
                            html.H4("BAJO", style={"color": GREEN_ACCENT, "margin": "0", "fontWeight": "bold", "fontSize": "15px", "marginTop": "5px"}),
                            html.Span("🟢", style={"fontSize": "8px"})
                        ], className="text-center"),
                    ])


                ], style=CARD_STYLE)
            ], md=4),


            # --- SECCIÓN 3: COMPARADOR DE CUOTAS ---
            dbc.Col([
                html.Div([
                    html.H6("COMPARADOR DE CUOTAS", style={"color": TITLE_GREEN, "fontSize": "12px", "fontWeight": "bold"}),
                    dash_table.DataTable(
                        data=data_comparador,
                        columns=[{"name": i, "id": i} for i in ["CASA", "1", "X", "2", "MEJOR"]],
                        style_as_list_view=True,
                        style_header={
                            'backgroundColor': CARD_BG,
                            'color': TEXT_MUTED,
                            'fontSize': '10px',
                            'borderBottom': f'1px solid {BORDER_COLOR}',
                            'textAlign': 'center',
                            'fontWeight': 'bold'
                        },
                        style_cell={
                            'backgroundColor': CARD_BG,
                            'color': 'white',
                            'fontSize': '12px',
                            'borderBottom': f'1px solid {BORDER_COLOR}',
                            'textAlign': 'center',
                            'padding': '10px 5px'
                        },
                        style_cell_conditional=[
                            {'if': {'column_id': 'CASA'}, 'textAlign': 'left', 'fontWeight': 'bold'},
                            {'if': {'column_id': 'MEJOR'}, 'color': '#f59e0b'}
                        ]
                    ),
                    html.Div(
                        html.A("Ver todas las cuotas >", href="#", style={"color": GREEN_ACCENT, "fontSize": "11px", "textDecoration": "none"}),
                        className="text-center mt-3"
                    )
                ], style=CARD_STYLE)
            ], md=4),


        ])
    ]
)


# Ejecutar la aplicación
if __name__ == "__main__":
    app.run_server(debug=True)

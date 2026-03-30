import os
import sys
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# --- IMPORTACIONES DE NUESTROS MÓDULOS ---
from data_loader import (
    RUTA_EXCEL, NOMBRE_HOJA, COL_CONDUCTOR, COL_AÑO, COL_COMENTARIO,
    df_global, lista_conductores, lista_años_global, ERROR_CARGA
)
from logic import calcular_indicadores
from visualization import crear_tarjeta_indicadores, generar_grafica, crear_seccion_comentarios

# =============================================================================
# LAYOUT DE DASH
# =============================================================================

# Si no se pudo instalar dash_bootstrap_components, usar solo dcc/html
try:
    import dash_bootstrap_components as dbc
    USE_DBC = True
except ImportError:
    USE_DBC = False

app = Dash(
    __name__,
    external_stylesheets=(
        [dbc.themes.BOOTSTRAP, "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"]
        if USE_DBC
        else ["https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"]
    ),
    title="Rendimiento de Conductores",
)

server = app.server  # EXPOSICIÓN DEL OBJETO SERVER (Básico para gunicorn en Render)

# Estilos base
ESTILO_CONTAINER = {
    "fontFamily": "Inter, Segoe UI, Arial",
    "maxWidth": "1200px",
    "margin": "0 auto",
    "padding": "30px 24px",
    "background": "#ffffff",
}

ESTILO_TITULO_APP = {
    "fontSize": "26px",
    "fontWeight": "700",
    "color": "#0f172a",
    "marginBottom": "4px",
}

ESTILO_SUBTITULO = {
    "fontSize": "14px",
    "color": "#64748b",
    "marginBottom": "24px",
}

ESTILO_LABEL = {
    "fontSize": "13px",
    "fontWeight": "600",
    "color": "#374151",
    "marginBottom": "6px",
    "display": "block",
}

ESTILO_DROPDOWN = {
    "width": "360px",
    "borderRadius": "8px",
    "fontSize": "14px",
    "marginBottom": "24px",
}


def build_layout():
    if ERROR_CARGA:
        return html.Div(
            style=ESTILO_CONTAINER,
            children=[
                html.H1("Error al cargar datos", style=ESTILO_TITULO_APP),
                html.Pre(
                    ERROR_CARGA,
                    style={
                        "background": "#fef2f2",
                        "border": "1px solid #fecaca",
                        "borderRadius": "8px",
                        "padding": "16px",
                        "color": "#b91c1c",
                        "fontSize": "13px",
                        "whiteSpace": "pre-wrap",
                    },
                ),
                html.P(
                    "Ajusta la variable RUTA_EXCEL en data_loader.py y vuelve a ejecutar.",
                    style={"color": "#64748b", "marginTop": "12px"},
                ),
            ],
        )

    conductor_inicial = lista_conductores[0] if lista_conductores else None

    # Opciones iniciales del dropdown de año (todos los años del conductor inicial)
    if conductor_inicial and not df_global.empty and COL_AÑO in df_global.columns:
        def _a_entero_safe(x):
            try:
                return int(float(x))
            except (ValueError, TypeError):
                return None
        años_conductor_inicial = sorted({
            _a_entero_safe(v)
            for v in df_global.loc[df_global[COL_CONDUCTOR] == conductor_inicial, COL_AÑO].dropna()
        } - {None})
    else:
        años_conductor_inicial = list(lista_años_global)

    opciones_año_inicial = [{"label": "Todos", "value": "Todos"}] + [
        {"label": str(a), "value": str(a)} for a in años_conductor_inicial
    ]

    return html.Div(
        style=ESTILO_CONTAINER,
        children=[
            # Encabezado
            html.H1("📊 Rendimiento de Conductores", style=ESTILO_TITULO_APP),
            html.P(
                f"Datos cargados desde: {os.path.basename(RUTA_EXCEL)}  •  Hoja: '{NOMBRE_HOJA}'  •  {len(df_global)} registros totales",
                style=ESTILO_SUBTITULO,
            ),
            html.Hr(style={"borderColor": "#e2e8f0", "marginBottom": "20px"}),

            # ── Fila de filtros: Conductor + Año (side-by-side) ───────────────
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "32px",
                    "alignItems": "flex-end",
                    "marginBottom": "24px",
                },
                children=[
                    # -- Dropdown conductor --
                    html.Div([
                        html.Label("Conductor:", style=ESTILO_LABEL),
                        dcc.Dropdown(
                            id="dropdown-conductor",
                            options=[{"label": c, "value": c} for c in lista_conductores],
                            value=conductor_inicial,
                            clearable=False,
                            searchable=True,
                            placeholder="Selecciona un conductor...",
                            style={"width": "340px", "fontSize": "14px"},
                        ),
                    ]),
                    # -- Dropdown año (se actualiza dinámicamente según el conductor) --
                    html.Div([
                        html.Label("Año:", style=ESTILO_LABEL),
                        dcc.Dropdown(
                            id="dropdown-año",
                            options=opciones_año_inicial,
                            value="Todos",
                            clearable=False,
                            searchable=False,
                            style={"width": "160px", "fontSize": "14px"},
                        ),
                    ]),
                ],
            ),

            # Tarjetas de indicadores (se actualiza vía callback)
            html.Div(id="tarjetas-indicadores"),

            # Gráfica principal
            dcc.Graph(
                id="grafica-rendimiento",
                config={"displayModeBar": True, "displaylogo": False},
            ),

            # === NUEVO CONTENEDOR DE COMENTARIOS ===
            html.Div(id="seccion-comentarios"),

            # Footer
            html.Hr(style={"borderColor": "#e2e8f0", "marginTop": "8px"}),
            html.P(
                "Tip: coloca el cursor sobre las barras para ver detalles · Usa los controles del gráfico para hacer zoom",
                style={"color": "#94a3b8", "fontSize": "12px", "textAlign": "center"},
            ),
        ],
    )


app.layout = build_layout()


# =============================================================================
# CALLBACKS
# =============================================================================

# ── CALLBACK ENCADENADO: actualiza opciones del año cuando cambia el conductor ─
@app.callback(
    Output("dropdown-año", "options"),
    Output("dropdown-año", "value"),
    Input("dropdown-conductor", "value"),
)
def actualizar_opciones_año(conductor_seleccionado):
    """
    Cuando cambia el conductor, recalcula los años disponibles para ese conductor
    y resetea el filtro a 'Todos'.
    """
    def _a_entero_safe(x):
        try:
            return int(float(x))
        except (ValueError, TypeError):
            return None

    if conductor_seleccionado and not df_global.empty and COL_AÑO in df_global.columns:
        años_disponibles = sorted({
            _a_entero_safe(v)
            for v in df_global.loc[
                df_global[COL_CONDUCTOR] == conductor_seleccionado, COL_AÑO
            ].dropna()
        } - {None})
    else:
        años_disponibles = list(lista_años_global)

    opciones = [{"label": "Todos", "value": "Todos"}] + [
        {"label": str(a), "value": str(a)} for a in años_disponibles
    ]
    return opciones, "Todos"   # siempre resetea a "Todos" al cambiar conductor


# ── CALLBACK PRINCIPAL: actualiza KPIs y gráfica según conductor + año ───
@app.callback(
    Output("tarjetas-indicadores", "children"),
    Output("grafica-rendimiento",  "figure"),
    Output("seccion-comentarios", "children"),
    Input("dropdown-conductor",    "value"),
    Input("dropdown-año",         "value"),
)
def actualizar_dashboard(conductor_seleccionado, año_seleccionado):
    """
    Actualiza las tarjetas y la gráfica cuando cambia el conductor o el año.
    """
    def _fig_vacia(mensaje):
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[dict(
                text=mensaje,
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                font=dict(size=16, color="#94a3b8"),
            )],
        )
        return fig

    if not conductor_seleccionado or df_global.empty:
        return html.Div(), _fig_vacia("Selecciona un conductor para ver su rendimiento"), html.Div()

    # ── Filtrar por conductor ────────────────────────────────────────────
    df_filtrado = df_global[df_global[COL_CONDUCTOR] == conductor_seleccionado].copy()

    # ── Filtrar por año (si no es "Todos") ──────────────────────────────
    filtro_año_activo = año_seleccionado and año_seleccionado != "Todos"
    if filtro_año_activo and COL_AÑO in df_filtrado.columns:
        def _a_entero_safe(x):
            try:
                return int(float(x))
            except (ValueError, TypeError):
                return None
        try:
            año_int = int(año_seleccionado)
        except ValueError:
            año_int = None
        if año_int is not None:
            df_filtrado = df_filtrado[
                df_filtrado[COL_AÑO].apply(_a_entero_safe) == año_int
            ].copy()

    if df_filtrado.empty:
        msg = f"Sin datos para {conductor_seleccionado}"
        if filtro_año_activo:
            msg += f" — {año_seleccionado}"
        return html.Div(), _fig_vacia(msg), html.Div()

    # ── Calcular indicadores y generar componentes ────────────────────────
    indicadores = calcular_indicadores(df_filtrado)
    tarjetas    = crear_tarjeta_indicadores(conductor_seleccionado, indicadores)
    figura      = generar_grafica(df_filtrado, conductor_seleccionado)
    comentarios = crear_seccion_comentarios(df_filtrado)

    return tarjetas, figura, comentarios


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Rendimiento de Conductores — Dashboard Interactivo (Modularizado)")
    print("=" * 60)
    if ERROR_CARGA:
        print(f"\n[ERROR al cargar datos]\n{ERROR_CARGA}")
        print("\nAbre el script y ajusta la variable RUTA_EXCEL.")
        sys.exit(1)
    else:
        print(f"\n  Conductores disponibles: {len(lista_conductores)}")
        print(f"  Registros totales:        {len(df_global)}")
        print("\n  Accede en tu navegador en:  http://127.0.0.1:8050")
        print("  (Presiona Ctrl+C para detener el servidor)\n")
        
        # Puerto inyectado por Render en el entorno, o 8050 en local
        port = int(os.environ.get("PORT", 8050))
        app.run(debug=False, host="0.0.0.0", port=port)

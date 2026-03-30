import pandas as pd
import plotly.graph_objects as go
from dash import html

from data_loader import COL_GANANCIAS, COL_META, COL_COMENTARIO

# =============================================================================
# FUNCIONES DE VISUALIZACIÓN
# =============================================================================

def crear_tarjeta_indicadores(conductor: str, indicadores: dict) -> list:
    """
    Genera la tarjeta/texto de resumen con los indicadores del conductor.
    """
    pct = indicadores["pct_cumplimiento"]
    pct_str = f"{pct:.1f}%" if pct is not None else "N/D"

    # Determinar color según porcentaje de cumplimiento
    if pct is None:
        color_pct = "#6c757d"
    elif pct >= 100:
        color_pct = "#28a745"
    elif pct >= 80:
        color_pct = "#fd7e14"
    else:
        color_pct = "#dc3545"

    def fmt(valor):
        try:
            return f"${valor:,.2f}"
        except Exception:
            return "N/D"

    cards = html.Div(
        style={
            "display": "flex",
            "gap": "20px",
            "flexWrap": "wrap",
            "marginBottom": "18px",
            "justifyContent": "flex-start",
        },
        children=[
            # Tarjeta: Ganancias acumuladas
            html.Div(
                style={
                    "background": "#f8fafc",
                    "border": "1px solid #e2e8f0",
                    "borderRadius": "12px",
                    "padding": "16px 24px",
                    "minWidth": "180px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
                },
                children=[
                    html.P("Ganancias Acumuladas", style={"margin": "0 0 4px 0", "color": "#64748b", "fontSize": "12px", "fontWeight": "600", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                    html.P(fmt(indicadores["total_ganancias"]), style={"margin": "0", "color": "#1e40af", "fontSize": "22px", "fontWeight": "700"}),
                ],
            ),
            # Tarjeta: Meta acumulada
            html.Div(
                style={
                    "background": "#f8fafc",
                    "border": "1px solid #e2e8f0",
                    "borderRadius": "12px",
                    "padding": "16px 24px",
                    "minWidth": "180px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
                },
                children=[
                    html.P("Meta Acumulada", style={"margin": "0 0 4px 0", "color": "#64748b", "fontSize": "12px", "fontWeight": "600", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                    html.P(fmt(indicadores["total_meta"]), style={"margin": "0", "color": "#7c3aed", "fontSize": "22px", "fontWeight": "700"}),
                ],
            ),
            # Tarjeta: % cumplimiento
            html.Div(
                style={
                    "background": "#f8fafc",
                    "border": "1px solid #e2e8f0",
                    "borderRadius": "12px",
                    "padding": "16px 24px",
                    "minWidth": "180px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
                },
                children=[
                    html.P("% Cumplimiento", style={"margin": "0 0 4px 0", "color": "#64748b", "fontSize": "12px", "fontWeight": "600", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                    html.P(pct_str, style={"margin": "0", "color": color_pct, "fontSize": "22px", "fontWeight": "700"}),
                ],
            ),
            # Tarjeta: N° registros
            html.Div(
                style={
                    "background": "#f8fafc",
                    "border": "1px solid #e2e8f0",
                    "borderRadius": "12px",
                    "padding": "16px 24px",
                    "minWidth": "160px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
                },
                children=[
                    html.P("Registros", style={"margin": "0 0 4px 0", "color": "#64748b", "fontSize": "12px", "fontWeight": "600", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                    html.P(str(indicadores["n_registros"]), style={"margin": "0", "color": "#374151", "fontSize": "22px", "fontWeight": "700"}),
                ],
            ),
        ],
    )
    return cards


def _calcular_rango_y(ganancias: list, metas: list, padding_pct: float = 0.18):
    """
    Calcula el rango [y_min, y_max] del eje Y a partir de los datos reales,
    agregando un margen visual (padding_pct) arriba y abajo.
    Retorna (None, None) si no hay datos numéricos válidos.
    """
    valores = [
        v for v in ganancias + metas
        if v is not None and v == v  # descarta None y NaN
    ]
    if not valores:
        return None, None
    y_min = min(valores)
    y_max = max(valores)
    span  = max(abs(y_max - y_min), 1)     # evita span=0 si todos los valores son iguales
    return y_min - span * padding_pct, y_max + span * padding_pct


def generar_grafica(df_conductor: pd.DataFrame, conductor: str) -> go.Figure:
    """
    Genera la figura de Plotly con GANANCIAS TOTALES como barras
    y META como línea punteada para el conductor seleccionado.

    Mejoras respecto a la versión anterior:
    - Rango del eje Y calculado dinámicamente con padding para escala legible.
    - Etiquetas de barras ocultas cuando el valor está cerca de cero,
      para no saturar la vista en barras muy pequeñas.
    - Texto blanco en barras negativas para contrastar con el fondo azul.
    """
    etiquetas = df_conductor["ETIQUETA_PERIODO"].tolist()
    ganancias = df_conductor[COL_GANANCIAS].tolist()
    metas     = df_conductor[COL_META].tolist()

    # ── Calcular rango dinámico del eje Y ────────────────────────────────────
    y_lo, y_hi = _calcular_rango_y(ganancias, metas)
    span_y = (y_hi - y_lo) if (y_lo is not None and y_hi is not None) else 1

    # Umbral para ocultar etiquetas: barras cuyo valor absoluto sea < 2 % del span
    # evitan saturar la vista con números en barras casi invisibles.
    umbral_etiqueta = span_y * 0.02

    # ── Posición y color de texto por barra ──────────────────────────────────
    text_positions = []
    text_fonts     = []
    for v in ganancias:
        es_nulo  = v is None or v != v          # None o NaN
        es_cero  = not es_nulo and abs(v) < umbral_etiqueta
        negativo = not es_nulo and v < 0

        if es_nulo or es_cero:
            # Barra sin valor o casi cero: mostrar texto vacío ocultando la etiqueta
            text_positions.append("none")
            text_fonts.append(dict(size=0, color="rgba(0,0,0,0)"))
        elif negativo:
            # Barra negativa: etiqueta dentro con texto blanco para contraste
            text_positions.append("inside")
            text_fonts.append(dict(size=11, color="#ffffff"))
        else:
            # Barra positiva: etiqueta fuera (encima) con texto oscuro
            text_positions.append("outside")
            text_fonts.append(dict(size=11, color="#1e293b"))

    fig = go.Figure()

    # ── Barras de GANANCIAS TOTALES ──────────────────────────────────────────
    fig.add_trace(go.Bar(
        x=etiquetas,
        y=ganancias,
        text=ganancias,
        texttemplate="$%{text:.1f}",
        textposition=text_positions,
        cliponaxis=False,                    # evita que las etiquetas se recorten
        name="Ganancias Totales",
        marker=dict(
            color="#1e40af",
            opacity=0.87,
            line=dict(color="#1e3a8a", width=0.8),
        ),
        # textfont no soporta lista directamente en go.Bar; se maneja por uniformtext
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Ganancias: $%{y:,.1f}<extra></extra>"
        ),
    ))

    # ── Línea punteada de META ───────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=etiquetas,
        y=metas,
        mode="lines+markers",
        name="Meta",
        line=dict(color="#7c3aed", width=2.5, dash="dash"),
        marker=dict(size=7, color="#7c3aed", symbol="diamond"),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Meta: $%{y:,.1f}<extra></extra>"
        ),
    ))

    # ── Layout ───────────────────────────────────────────────────────────────
    yaxis_cfg = dict(
        title="Monto ($)",
        showgrid=True,
        gridcolor="#e2e8f0",
        zeroline=True,
        zerolinecolor="#64748b",
        zerolinewidth=1.5,
        linecolor="#cbd5e1",
        tickprefix="$",
        tickformat=",.1f",
        automargin=True,
    )
    # Aplicar rango dinámico solo si tenemos datos válidos
    if y_lo is not None:
        yaxis_cfg["range"] = [y_lo, y_hi]

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"Rendimiento de conductor a través del tiempo — <b>{conductor}</b>",
            font=dict(size=18, color="#1e293b", family="Inter, Segoe UI, Arial"),
            x=0,
            xanchor="left",
        ),
        font=dict(family="Inter, Segoe UI, Arial", size=13, color="#374151"),
        bargap=0.25,
        uniformtext=dict(minsize=9, mode="hide"),
        xaxis=dict(
            title="Período",
            tickangle=-35,
            showgrid=True,
            gridcolor="#e2e8f0",
            zeroline=False,
            linecolor="#cbd5e1",
            automargin=True,
        ),
        yaxis=yaxis_cfg,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#e2e8f0",
            borderwidth=1,
        ),
        hovermode="x unified",
        margin=dict(l=70, r=30, t=110, b=110),
        height=520,
    )

    return fig

def crear_seccion_comentarios(df_conductor: pd.DataFrame):
    """
    Crea un contenedor con los comentarios del conductor.
    Ignora valores nulos o vacíos.
    """
    if COL_COMENTARIO not in df_conductor.columns:
        return html.Div(
            "La columna de comentarios no existe en los datos.",
            style={"color": "#64748b", "fontStyle": "italic", "padding": "16px"}
        )

    # Filtrar solo registros que tengan un comentario válido
    df_coments = df_conductor[df_conductor[COL_COMENTARIO].notna()].copy()
    df_coments[COL_COMENTARIO] = df_coments[COL_COMENTARIO].astype(str).str.strip()
    df_coments = df_coments[df_coments[COL_COMENTARIO] != ""]
    df_coments = df_coments[df_coments[COL_COMENTARIO].str.lower() != "nan"]

    if df_coments.empty:
        return html.Div(
            "No hay comentarios disponibles para este filtro.",
            style={"color": "#64748b", "fontStyle": "italic", "padding": "16px", "textAlign": "center"}
        )

    lista_items = []
    for _, row in df_coments.iterrows():
        etiqueta = row.get("ETIQUETA_PERIODO", "Sin fecha")
        comentario = row[COL_COMENTARIO]
        
        item = html.Div(
            style={
                "background": "#fbfcfd",
                "border": "1px solid #e2e8f0",
                "borderLeft": "4px solid #3b82f6",
                "borderRadius": "6px",
                "padding": "12px 16px",
                "marginBottom": "12px",
                "boxShadow": "0 1px 2px rgba(0,0,0,0.02)"
            },
            children=[
                html.Span(f"[{etiqueta}]", style={"fontWeight": "600", "color": "#1e40af", "fontSize": "12px", "marginRight": "12px"}),
                html.Span(comentario, style={"color": "#334155", "fontSize": "14px", "lineHeight": "1.5"})
            ]
        )
        lista_items.append(item)

    return html.Div(
        children=[
            html.H3("💬 Comentarios del conductor", style={"fontSize": "18px", "fontWeight": "700", "color": "#0f172a", "marginBottom": "16px"}),
            html.Div(lista_items)
        ],
        style={
            "marginTop": "16px",
            "paddingTop": "24px",
            "borderTop": "1px solid #e2e8f0",
            "paddingBottom": "24px"
        }
    )

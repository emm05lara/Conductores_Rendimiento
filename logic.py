import pandas as pd
from data_loader import COL_GANANCIAS, COL_META

# =============================================================================
# FUNCIONES DE LÓGICA / NEGOCIO
# =============================================================================

def calcular_indicadores(df_conductor: pd.DataFrame) -> dict:
    """
    Calcula los indicadores de resumen para el conductor seleccionado.
    Los nulos se tratan como 0 solo para el cálculo del acumulado.
    """
    total_ganancias = df_conductor[COL_GANANCIAS].fillna(0).sum()
    total_meta      = df_conductor[COL_META].fillna(0).sum()
    pct_cumplimiento = (total_ganancias / total_meta * 100) if total_meta != 0 else None
    return {
        "total_ganancias":   total_ganancias,
        "total_meta":        total_meta,
        "pct_cumplimiento":  pct_cumplimiento,
        "n_registros":       len(df_conductor),
    }

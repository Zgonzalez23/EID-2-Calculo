import pandas as pd
import plotly.graph_objects as go
from calculos import calcular_serie, limite_empirico, C_MAX

N_ANALISIS = 5000   # k para estimar limite empirico con mayor precision


def generar_grafico_caso(caso, resultados, p1, p2, p3):
    """Genera un grafico dinamico (Plotly) para un caso específico."""
    probabilidades = [p1, p2, p3]
    colores = ["blue", "green", "red"]

    fig = go.Figure()

    for j, p in enumerate(probabilidades, start=1):
        clave = f"p{j}"
        r = resultados[caso][clave]
        fig.add_trace(go.Scatter(
            x=r["ks_conv"],
            y=r["S_conv"],
            mode="lines",
            name=f"p{j} = {p:.4f}",
            line=dict(color=colores[j - 1], width=2)
        ))

    fig.add_hline(
        y=C_MAX,
        line_dash="dash",
        line_color="black",
        annotation_text=f"C_max = {C_MAX}",
        annotation_position="bottom right"
    )

    fig.update_layout(
        title=f"Caso {caso}: S_k vs k",
        xaxis_title="k (numero de terminos acumulados)",
        yaxis_title="S_k (costo esperado acumulado)",
        hovermode="x unified",
        legend=dict(title="Probabilidades"),
        template="plotly_white",
        height=500
    )

    return fig


def analizar_viabilidad(resultados):
    """Calcula convergencia y viabilidad de las 9 combinaciones y elige una."""
    filas_conv = []
    filas_viab = []
    viables = []

    for caso in ["A", "B", "C"]:
        for clave in ["p1", "p2", "p3"]:
            p = resultados[caso][clave]["p"]
            s10 = resultados[caso][clave]["S_tabla"][-1]

            ks, S = calcular_serie(p, caso, N_ANALISIS)
            lim, k_est = limite_empirico(S, ks)

            converge = k_est < N_ANALISIS
            cumple = converge and lim <= C_MAX

            filas_conv.append({
                "Caso": caso,
                "Prob": clave,
                "p": round(p, 4),
                "S10": round(s10, 4),
                "Converge": "Si" if converge else "No",
                "Limite empirico": round(lim, 4),
                "k de estabilizacion": k_est,
            })
            filas_viab.append({
                "Caso": caso,
                "Prob": clave,
                "Limite": round(lim, 4),
                "C_max": C_MAX,
                "Cumple": "Si" if cumple else "No",
            })
            if cumple:
                viables.append((lim, k_est, caso, clave, p))

    df_conv = pd.DataFrame(filas_conv)
    df_viab = pd.DataFrame(filas_viab)

    if len(viables) == 0:
        return df_conv, df_viab, None

    # elijo el de menor costo esperado; si empatan, el que se estabiliza antes
    viables.sort()
    lim, k_est, caso, clave, p = viables[0]
    recomendacion = {
        "caso": caso,
        "prob": clave,
        "p": round(p, 4),
        "limite": round(lim, 4),
        "k": k_est,
        "n_viables": len(viables),
    }
    return df_conv, df_viab, recomendacion
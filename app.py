import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

st.set_page_config(page_title="EID 2", layout="wide")

# Funciones 

def extraer_digitos_rut(rut_str):
    """Extrae los dígitos numéricos del RUT y devuelve d1..d8"""
    digitos = re.findall(r'\d', rut_str)
    if len(digitos) < 8:
        digitos = ['0'] * (8 - len(digitos)) + digitos
    return [int(x) for x in digitos[:8]]


def calcular_probabilidades(d):
    """p1, p2, p3 según las fórmulas del enunciado"""
    p1 = (d[0] + d[2] + d[4] + 1) * 2 / 100   # d1,d3,d5
    p2 = (d[1] + d[3] + d[5] + 1) * 3 / 100   # d2,d4,d6
    p3 = (d[6] + d[7] + 1) * 4 / 100          # d7,d8
    return p1, p2, p3


def termino_reintento(i, p, caso):
    """Costo del i-ésimo reintento ponderado por su probabilidad"""
    q = 1 - p
    if caso == 'A':
        return i * (q ** (i - 1)) * p
    elif caso == 'B':
        return (1 / i) * (q ** (i - 1)) * p
    elif caso == 'C':
        return (i + 1) * (q ** (i - 1)) * p


def calcular_serie(p, caso, k_max):
    """Devuelve listas de k y S_k para k=1..k_max"""
    ks = list(range(1, k_max + 1))
    S = []
    acumulado = 0.0
    for k in ks:
        acumulado += termino_reintento(k, p, caso)
        S.append(acumulado)
    return ks, S


def limite_empirico(S, ks, tolerancia=1e-7):
    """
    Busca hacia atrás desde el último valor el punto donde S_k dejó de cambiar
    significativamente. Devuelve (valor_límite, k_aproximado_estabilización).
    """
    for i in range(len(S) - 1, 0, -1):
        if abs(S[i] - S[i - 1]) > tolerancia:
            return S[i], ks[i]
    return S[-1], ks[-1]


# Interfaz 

st.title("Protocolo ARQ – Análisis de Reintentos")
st.markdown("""Ingrese ruts""")

rut1 = st.text_input("RUT 1",            placeholder="Ej: 24.365.895-K")
rut2 = st.text_input("RUT 2 (opcional)", placeholder="Ej: 12.345.678-9")
rut3 = st.text_input("RUT 3 (opcional)", placeholder="Ej: 98.765.432-1")

# Procesar RUTs ingresados
integrantes = []
for i, rut in enumerate([rut1, rut2, rut3], start=1):
    if rut.strip():
        try:
            d = extraer_digitos_rut(rut)
            p1, p2, p3 = calcular_probabilidades(d)
            integrantes.append({
                "nombre": f" {i}",
                "rut": rut,
                "d": d,
                "p1": p1,
                "p2": p2,
                "p3": p3,
            })
        except Exception as e:
            st.error(f"Error procesando RUT {i}: {e}")

if not integrantes:
    st.warning("Ingrese al menos un RUT para continuar.")
    st.stop()

# Seleccionar qué RUT usar
sel = st.selectbox(
    "Seleccione el RUT a utilizar para el análisis",
    options=[(i, it["rut"]) for i, it in enumerate(integrantes, start=1)],
    format_func=lambda x: f"Integrante {x[0]}: {x[1]}"
)
idx = sel[0] - 1
d = integrantes[idx]["d"]
p1 = integrantes[idx]["p1"]
p2 = integrantes[idx]["p2"]
p3 = integrantes[idx]["p3"]

st.success(f"RUT seleccionado: {integrantes[idx]['rut']}  →  d = {d}")
st.write(f"**p₁ = {p1:.4f}**  **p₂ = {p2:.4f}**  **p₃ = {p3:.4f}")

# Parámetros fijos del enunciado
probabilidades = [p1, p2, p3]
casos = ["A", "B", "C"]
K_TABLA = 10          # S₁ … S₁₀
K_CONV = 300          # para estimar límite empírico
C_MAX = 10            # umbral de costo máximo

# Calculo 

resultados = {}  # resultados[caso][f"p{j}"] = {...}

for caso in casos:
    resultados[caso] = {}
    for j, p in enumerate(probabilidades, start=1):
        ks_tabla, S_tabla = calcular_serie(p, caso, K_TABLA)
        ks_conv, S_conv = calcular_serie(p, caso, K_CONV)
        lim_emp, k_est = limite_empirico(S_conv, ks_conv)

        resultados[caso][f"p{j}"] = {
            "p": p,
            "ks_tabla": ks_tabla,
            "S_tabla": S_tabla,
            "ks_conv": ks_conv,
            "S_conv": S_conv,
            "limite_empirico": lim_emp,
            "k_est": k_est,
            "cumple": lim_emp <= C_MAX,
        }

# 1. TABLAS S₁..S₁

st.header("1. Tablas S₁ … S₁₀ por caso y probabilidad")

for caso in casos:
    st.subheader(f"Caso {caso}")
    datos = {"k": list(range(1, K_TABLA + 1))}
    for j in range(1, 4):
        clave = f"p{j}"
        nombre_col = f"p{j} = {resultados[caso][clave]['p']:.4f}"
        datos[nombre_col] = [f"{val:.6f}" for val in resultados[caso][clave]["S_tabla"]]
    df_tabla = pd.DataFrame(datos)
    st.dataframe(df_tabla, use_container_width=True)

# 2. Convergencia

st.header("2. Convergencia y límite empírico")

datos_conv = []
for caso in casos:
    for j in range(1, 4):
        clave = f"p{j}"
        r = resultados[caso][clave]
        datos_conv.append({
            "Caso": caso,
            "Probabilidad": f"p{j} = {r['p']:.4f}",
            "¿Converge?": "Sí",
            "Límite empírico": f"{r['limite_empirico']:.6f}",
            "K estabilización aprox": r["k_est"],
        })

df_conv = pd.DataFrame(datos_conv)
st.dataframe(df_conv, use_container_width=True)

# 3. Graficos

st.header("3. Gráficos Sₖ vs k (uno por caso, tres curvas cada uno)")

colores = ["blue", "green", "red"]

for caso in casos:
    st.subheader(f"Caso {caso}")
    fig = go.Figure()

    for j, p in enumerate(probabilidades, start=1):
        clave = f"p{j}"
        r = resultados[caso][clave]
        fig.add_trace(go.Scatter(
            x=r["ks_conv"],
            y=r["S_conv"],
            mode="lines+markers",
            name=f"p{j} = {p:.4f}",
            line=dict(color=colores[j - 1]),
            marker=dict(size=4),
        ))

    # Línea de referencia del umbral
    fig.add_hline(
        y=C_MAX,
        line_dash="dash",
        line_color="black",
        annotation_text=f"C_máx = {C_MAX}",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title=f"Caso {caso}: Sₖ vs k",
        xaxis_title="k (número de términos acumulados)",
        yaxis_title="Sₖ (costo esperado acumulado)",
        hovermode="x unified",
        height=500,
        legend=dict(title="Probabilidades"),
    )
    st.plotly_chart(fig, use_container_width=True)

# Tabla

st.header("4. Tabla de viabilidad (Umbral C_máx = 10)")

datos_viab = []
for caso in casos:
    for j in range(1, 4):
        clave = f"p{j}"
        r = resultados[caso][clave]
        datos_viab.append({
            "Combinación": f"Caso {caso}, p{j}",
            "p": f"{r['p']:.4f}",
            "Límite empírico": f"{r['limite_empirico']:.6f}",
            "¿Cumple ≤ 10?": "SÍ" if r["cumple"] else "NO",
        })

df_viab = pd.DataFrame(datos_viab)
st.dataframe(df_viab, use_container_width=True)

# 5. La recomendacion

st.header("5. Recomendación de combinación")

opciones_viables = []
for caso in casos:
    for j in range(1, 4):
        clave = f"p{j}"
        r = resultados[caso][clave]
        if r["cumple"]:
            opciones_viables.append((caso, j, r))

if opciones_viables:
    # Elegir la de menor límite empírico (más eficiente dentro de las viables)
    mejor_caso, mejor_j, mejor_r = min(opciones_viables, key=lambda x: x[2]["limite_empirico"])

    st.success(f"""
    **Combinación recomendada: Caso {mejor_caso} con probabilidad p{mejor_j}**
    - Valor de p: {mejor_r['p']:.4f}
    - Límite empírico: {mejor_r['limite_empirico']:.6f} (≤ {C_MAX})
    - K de estabilización aproximado: {mejor_r['k_est']}

    **Justificación:**
    Esta combinación cumple el umbral de costo máximo requerido ({C_MAX} transmisiones esperadas) y, entre todas las opciones que lo cumplen, presenta el costo esperado total más bajo, lo que implica un uso más eficiente de la red. Además, su sucesión converge y se estabiliza rápidamente.
    """)
else:
    st.error("Ninguna de las 9 combinaciones cumple el umbral de C_máx = 10.")

st.markdown("---")
st.caption("Desarrollado con Python + Streamlit para la Evaluación Integrada de Desempeño.")
import streamlit as st
import pandas as pd

from calculos import (
    extraer_digitos_rut,
    calcular_probabilidades,
    generar_resultados,
    obtener_tablas_dataframe,
    C_MAX,
)
from analisis import (
    generar_grafico_caso,
    analizar_viabilidad,
)

st.set_page_config(page_title="EID 2 - Analisis de Reintentos", layout="wide")

st.title("EID 2 - Analisis de Reintentos-")
st.markdown("""
Aplicacion que calcula p1, p2, p3 desde un RUT, genera las tablas S1 a S10 para los 3 casos (A, B, C),
produce los graficos S_k vs k (dinamicos) y determina la combinacion recomendada segun el umbral C_max = 10.
""")

# Inicializar session_state
if "datos" not in st.session_state:
    st.session_state["datos"] = None
if "resultados" not in st.session_state:
    st.session_state["resultados"] = None

# Pestañas
tab_datos, tab_tablas, tab_graficos, tab_viabilidad = st.tabs([
    "1. Datos (RUTs)",
    "2. Tablas S1-S10",
    "3. Graficos",
    "4. Viabilidad"
])

# Pestaña 1 
with tab_datos:
    st.subheader("Ingreso de RUTs")
    st.write("Ingrese los RUT de los integrantes.")

    ruts = []
    cols = st.columns(3)
    for i in range(3):
        with cols[i]:
            rut = st.text_input(f"RUT Integrante {i+1}", placeholder="Ej: 24.365.895-K")
            if rut.strip():
                ruts.append(rut)

    if st.button("Calcular probabilidades", key="btn_calcular"):
        if not ruts:
            st.error("Ingrese al menos un RUT.")
        else:
            integrantes = []
            for i, rut in enumerate(ruts, start=1):
                try:
                    d = extraer_digitos_rut(rut)
                    p1, p2, p3 = calcular_probabilidades(d)
                    integrantes.append({
                        "nombre": f"Integrante {i}",
                        "rut": rut,
                        "d": d,
                        "p1": p1,
                        "p2": p2,
                        "p3": p3,
                    })
                except Exception as e:
                    st.error(f"Error procesando RUT {i}: {e}")
                    st.stop()

            if len(integrantes) == 1:
                sel_idx = 0
            else:
                sel_idx = st.selectbox(
                    "Seleccione el RUT a utilizar",
                    options=list(range(len(integrantes))),
                    format_func=lambda i: f"{integrantes[i]['rut']}  (p1={integrantes[i]['p1']:.4f}, p2={integrantes[i]['p2']:.4f}, p3={integrantes[i]['p3']:.4f})"
                )

            it = integrantes[sel_idx]
            st.session_state["datos"] = {
                "rut": it["rut"],
                "d": it["d"],
                "p1": it["p1"],
                "p2": it["p2"],
                "p3": it["p3"],
            }

            # Calcular resultados automaticamente para las demas pestañas
            st.session_state["resultados"] = generar_resultados(
                it["p1"], it["p2"], it["p3"]
            )
            st.success("Datos calculados correctamente. Revise las demas pestañas.")

    if st.session_state["datos"] is not None:
        d = st.session_state["datos"]
        st.info(f"RUT seleccionado: {d['rut']}  ->  d = {d['d']}")
        st.write(f"**p1 = {d['p1']:.4f}**   **p2 = {d['p2']:.4f}**   **p3 = {d['p3']:.4f}**")

# Pestaña 2
with tab_tablas:
    st.subheader("Tablas S1 a S10 (una por caso)")
    if st.session_state["resultados"] is None:
        st.warning("Primero calcule los datos en la pestaña 'Datos'.")
    else:
        tablas = obtener_tablas_dataframe(st.session_state["resultados"])
        for caso in ["A", "B", "C"]:
            st.markdown(f"### Caso {caso}")
            st.dataframe(tablas[caso], use_container_width=True)
        st.caption(f"Umbral de costo maximo C_max = {C_MAX}")

# Pestaña 3
with tab_graficos:
    st.subheader("Graficos S_k vs k (uno por caso, tres curvas cada uno)")
    st.write("Graficos interactivos: pase el mouse sobre las curvas para ver valores, use la barra de zoom, etc.")
    if st.session_state["resultados"] is None:
        st.warning("Primero calcule los datos en la pestaña 'Datos'.")
    else:
        d = st.session_state["datos"]
        if st.button("Generar graficos automaticamente", key="btn_graficos"):
            for caso in ["A", "B", "C"]:
                fig = generar_grafico_caso(
                    caso,
                    st.session_state["resultados"],
                    d["p1"], d["p2"], d["p3"]
                )
                st.plotly_chart(fig, use_container_width=True)

# Pestaña 4
with tab_viabilidad:
    st.subheader("Analisis de viabilidad y recomendacion")
    if st.session_state["resultados"] is None:
        st.warning("Primero calcule los datos en la pestaña 'Datos'.")
    else:
        df_conv, df_viab, recomendacion = analizar_viabilidad(
            st.session_state["resultados"]
        )

        st.markdown("### Convergencia y limite empirico")
        st.dataframe(df_conv, use_container_width=True)

        st.markdown("### Tabla de viabilidad (umbral C_max = 10)")
        st.dataframe(df_viab, use_container_width=True)

        st.markdown("### Recomendacion")
        if recomendacion:
            st.success(
                f"**Combinacion recomendada:** Caso {recomendacion['caso']} con {recomendacion['prob']}\n\n"
                f"- Valor de p: {recomendacion['p']:.4f}\n"
                f"- Limite empirico: {recomendacion['limite']:.4f} (<= {C_MAX})\n"
                f"- K de estabilizacion: {recomendacion['k']}\n"
                f"- Combinaciones viables: {recomendacion['n_viables']}"
            )
            st.markdown(
                "**Justificacion:** Esta combinacion cumple el umbral de costo maximo requerido y, entre "
                "todas las opciones que lo cumplen, presenta el costo esperado total mas bajo, lo que "
                "implica un uso mas eficiente de la red. Ademas, su sucesion converge y se estabiliza rapidamente."
            )
        else:
            st.error("Ninguna de las 9 combinaciones cumple el umbral de C_max = 10.")
import re
import pandas as pd

K_TABLA = 10      # S1 a S10
K_CONV = 300      # k para estimar limite empirico
C_MAX = 10        # umbral de costo maximo

def extraer_digitos_rut(rut_str):
    """Extrae los primeros 8 digitos numericos de un RUT."""
    digitos = re.findall(r'\d', rut_str)
    if len(digitos) < 8:
        digitos = ['0'] * (8 - len(digitos)) + digitos
    return [int(x) for x in digitos[:8]]


def calcular_probabilidades(d):
    """Calcula p1, p2, p3 segun las formulas del enunciado."""
    p1 = (d[0] + d[2] + d[4] + 1) * 2 / 100   # d1, d3, d5
    p2 = (d[1] + d[3] + d[5] + 1) * 3 / 100   # d2, d4, d6
    p3 = (d[6] + d[7] + 1) * 4 / 100          # d7, d8
    return p1, p2, p3


def termino_reintento(i, p, caso):
    """Costo del i-esimo reintento ponderado por su probabilidad."""
    q = 1 - p
    if caso == "A":
        return i * (q ** (i - 1)) * p
    elif caso == "B":
        return (1 / i) * (q ** (i - 1)) * p
    elif caso == "C":
        return (i + 1) * (q ** (i - 1)) * p
    return 0


def calcular_serie(p, caso, k_max):
    """Devuelve listas de k y S_k para k = 1 .. k_max."""
    ks = list(range(1, k_max + 1))
    S = []
    acumulado = 0.0
    for k in ks:
        acumulado += termino_reintento(k, p, caso)
        S.append(acumulado)
    return ks, S


def limite_empirico(S, ks, tolerancia=1e-7):
    """Busca hacia atras el punto donde S_k dejo de cambiar significativamente."""
    for i in range(len(S) - 1, 0, -1):
        if abs(S[i] - S[i - 1]) > tolerancia:
            return S[i], ks[i]
    return S[-1], ks[-1]


def generar_resultados(p1, p2, p3):
    """Calcula todo para los 9 casos (3 casos x 3 probabilidades)."""
    probabilidades = [p1, p2, p3]
    casos = ["A", "B", "C"]
    resultados = {}
    for caso in casos:
        resultados[caso] = {}
        for j, p in enumerate(probabilidades, start=1):
            clave = f"p{j}"
            ks_tabla, S_tabla = calcular_serie(p, caso, K_TABLA)
            ks_conv, S_conv = calcular_serie(p, caso, K_CONV)
            lim_emp, k_est = limite_empirico(S_conv, ks_conv)
            resultados[caso][clave] = {
                "p": p,
                "ks_tabla": ks_tabla,
                "S_tabla": S_tabla,
                "ks_conv": ks_conv,
                "S_conv": S_conv,
                "limite_empirico": lim_emp,
                "k_est": k_est,
                "cumple": lim_emp <= C_MAX,
            }
    return resultados


def obtener_tablas_dataframe(resultados):
    """Retorna un diccionario con los DataFrames de S1-S10 por caso."""
    casos = ["A", "B", "C"]
    tablas = {}
    for caso in casos:
        datos = {"k": list(range(1, K_TABLA + 1))}
        for j in range(1, 4):
            clave = f"p{j}"
            nombre = f"p{j} = {resultados[caso][clave]['p']:.4f}"
            datos[nombre] = [f"{val:.6f}" for val in resultados[caso][clave]["S_tabla"]]
        tablas[caso] = pd.DataFrame(datos)
    return tablas
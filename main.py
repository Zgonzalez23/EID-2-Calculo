import re
import pandas
import matplotlib.pyplot as plt

K_TABLA = 10      # S1 a S10
K_CONV = 300      # k para estimar limite empirico
C_MAX = 10        # umbral de costo maximo
N_ANALISIS = 5000

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


def imprimir_tablas(resultados):
    """Imprime en consola las 3 tablas S1...S10 (una por caso)."""
    casos = ["A", "B", "C"]
    for caso in casos:
        print(f"\n{'='*50}")
        print(f"CASO {caso} - S_k para k = 1 a 10")
        print(f"{'='*50}")
        print(f"{'k':<5} {'p1':<18} {'p2':<18} {'p3':<18}")
        for k in range(1, K_TABLA + 1):
            s1 = f"{resultados[caso]['p1']['S_tabla'][k-1]:.6f}"
            s2 = f"{resultados[caso]['p2']['S_tabla'][k-1]:.6f}"
            s3 = f"{resultados[caso]['p3']['S_tabla'][k-1]:.6f}"
            print(f"{k:<5} {s1:<18} {s2:<18} {s3:<18}")
    print(f"\nUmbral de costo maximo C_max = {C_MAX}")

def generar_graficos(resultados, p1, p2, p3):
    """Genera y guarda 3 graficos (uno por caso A, B y C) como archivos .png."""
    probabilidades = [p1, p2, p3]
    colores = ["blue", "green", "red"]
    casos = ["A", "B", "C"]

    for caso in casos:
        plt.figure(figsize=(8, 5))
        for j, p in enumerate(probabilidades, start=1):
            clave = f"p{j}"
            r = resultados[caso][clave]
            plt.plot(r["ks_conv"], r["S_conv"],
                     label=f"p{j} = {p:.4f}",
                     color=colores[j - 1],
                     linewidth=2)
        plt.axhline(y=C_MAX, color="black", linestyle="--", linewidth=1,
                    label=f"C_max = {C_MAX}")
        plt.title(f"Caso {caso}: S_k vs k")
        plt.xlabel("k (numero de terminos acumulados)")
        plt.ylabel("S_k (costo esperado acumulado)")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        nombre_archivo = f"grafico_caso_{caso}.png"
        plt.savefig(nombre_archivo, dpi=150)
        plt.close()
        print(f"Grafico guardado: {nombre_archivo}")





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

    df_conv = pandas.DataFrame(filas_conv)
    df_viab = pandas.DataFrame(filas_viab)

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


def imprimir_analisis_consola(df_conv, df_viab, recomendacion):
    """Imprime tabla de convergencia, tabla de viabilidad y recomendacion."""
    print(f"\n{'='*50}")
    print("TABLA DE CONVERGENCIA")
    print(f"{'='*50}")
    print(df_conv.to_string(index=False))

    print(f"\n{'='*50}")
    print(f"TABLA DE VIABILIDAD (C_max = {C_MAX})")
    print(f"{'='*50}")
    print(df_viab.to_string(index=False))

    print(f"\n{'='*50}")
    print("RECOMENDACION")
    print(f"{'='*50}")
    if recomendacion is None:
        print("Ninguna combinacion cumple el umbral C_max.")
        return

    r = recomendacion
    print(f"Combinacion recomendada: Caso {r['caso']} con {r['prob']} (p = {r['p']})")
    print(f"Justificacion: la serie converge a {r['limite']}, que es menor o igual "
          f"al umbral de {C_MAX}. Es la de menor costo entre las {r['n_viables']} "
          f"combinaciones que cumplen, y su curva se estabiliza desde k = {r['k']}.")

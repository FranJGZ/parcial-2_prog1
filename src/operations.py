import os
import csv
import json
from datetime import datetime
from validations import *

# Definición de rutas relativas hacia la carpeta datos/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_DATOS = os.path.join(BASE_DIR, "..", "datos")


def get_data_path(filename):
    """Devuelve la ruta hacia un archivo ubicado dentro de la carpeta datos/."""
    os.makedirs(DIR_DATOS, exist_ok=True)
    return os.path.join(DIR_DATOS, filename)


def load_json(file_path):
    """Carga un archivo JSON de forma segura."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_csv(file_path, headers, rows, mode="w"):
    """Escribe o añade filas en un archivo CSV."""
    file_exists = os.path.exists(file_path)
    with open(file_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if mode == "w" or not file_exists or os.path.getsize(file_path) == 0:
            writer.writerow(headers)
        writer.writerows(rows)


def read_csv(file_path):
    """Lee un archivo CSV y devuelve una lista de diccionarios."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return []
    try:
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []


def calcular_estacionamiento_recursivo(minutos_restantes, tipo_vehiculo, tarifas):
    """
    Función recursiva para calcular el costo de estacionamiento por tramos de tiempo.
    No utiliza bucles (while, for).
    """
    # Caso base
    if minutos_restantes <= 0:
        return 0

    categoria = tarifas["tarifas"][tipo_vehiculo]
    precio_30min = categoria["precio_bloque_30min"]
    precio_hora_adicional = categoria["precio_hora_adicional"]

    # Paso recursivo
    if minutos_restantes > 120:
        siguiente = 120 if (minutos_restantes - 60 < 120) else (minutos_restantes - 60)
        return precio_hora_adicional + calcular_estacionamiento_recursivo(siguiente, tipo_vehiculo, tarifas)
    else:
        return precio_30min + calcular_estacionamiento_recursivo(minutos_restantes - 30, tipo_vehiculo, tarifas)


def liquidar(tipo_vehiculo, dias, minutos, solicito_lavado, tarifas):
    """Aplica las reglas de negocio y cálculo tarifario."""
    categoria = tarifas["tarifas"][tipo_vehiculo]
    tope_dia = categoria["tope_dia"]
    precio_lavado = categoria["precio_lavado"]

    if dias > 0:
        # Estadía prolongada
        base = dias * tope_dia
        bonificacion = 0
        est_neto = base
        costo_lav = precio_lavado if solicito_lavado else 0
        total = est_neto + costo_lav
    else:
        # Estadía en el mismo día
        costo_sin_tope = calcular_estacionamiento_recursivo(minutos, tipo_vehiculo, tarifas)
        base = min(costo_sin_tope, tope_dia)

        if solicito_lavado:
            costo_lav = precio_lavado
            if minutos <= 120:
                # 100% bonificado
                bonificacion = base
                est_neto = 0
            else:
                # Primeras 2 horas bonificadas
                primeras_2hs = calcular_estacionamiento_recursivo(120, tipo_vehiculo, tarifas)
                bonificacion = min(base, primeras_2hs)
                est_neto = max(0, base - bonificacion)
            total = est_neto + costo_lav
        else:
            bonificacion = 0
            est_neto = base
            costo_lav = 0
            total = est_neto

    return {
        "estacionamiento_base": base,
        "bonificacion_lavado": bonificacion,
        "costo_estacionamiento_neto": est_neto,
        "costo_lavado": costo_lav,
        "total_cobrado": total
    }


def registrar_cobro_manual(tarifas):
    """Opción 1: Simular y registrar cobro en ventanilla."""
    print("\n" + "=" * 45)
    print("      REGISTRAR COBRO MANUAL EN VENTANILLA")
    print("=" * 45)

    patente = get_patente("Ingrese la patente (ABC123 o AA123BB): ")
    tipo_vehiculo = get_tipo_vehiculo("Seleccione la categoría: ", tarifas)

    dias = get_dias("\n¿Cuántos días pasaron? (0 si se retira en el mismo día): ")
    if dias == 0:
        entrada, salida, minutos = get_horarios_mismo_dia()
    else:
        entrada = "00:00"
        salida = "00:00"
        minutos = dias * 1440
        print(f"Estadía prolongada de {dias} día(s). Se cobrará a tarifa fija de Tope Diario.")

    solicito_lavado = get_confirmation("\n¿Solicitó servicio de lavado? (s/n): ")

    liq = liquidar(tipo_vehiculo, dias, minutos, solicito_lavado, tarifas)

    ticket = {
        "patente": patente,
        "tipo_vehiculo": tipo_vehiculo,
        "dias": dias,
        "minutos": minutos,
        "duracion_str": format_duration(minutos, dias),
        "entrada": entrada,
        "salida": salida,
        "estacionamiento_base": liq["estacionamiento_base"],
        "bonificacion_lavado": liq["bonificacion_lavado"],
        "costo_estacionamiento_neto": liq["costo_estacionamiento_neto"],
        "costo_lavado": liq["costo_lavado"],
        "total_cobrado": liq["total_cobrado"]
    }

    print_ticket_card(ticket)

    # Guardar en datos/liquidacion-manual.csv
    headers = [
        "id", "fecha_hora", "patente", "tipo_vehiculo", "dias",
        "entrada", "salida", "minutos", "estacionamiento_base",
        "bonificacion_lavado", "costo_lavado", "total_cobrado"
    ]
    id_manual = f"MAN-{datetime.now().strftime('%H%M%S')}"
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        id_manual, fecha_hora, patente, tipo_vehiculo, dias,
        entrada, salida, minutos, liq["estacionamiento_base"],
        liq["bonificacion_lavado"], liq["costo_lavado"], liq["total_cobrado"]
    ]
    ruta_manual = get_data_path("liquidacion-manual.csv")
    save_csv(ruta_manual, headers, [row], mode="a")
    print("[OK] Operación guardada exitosamente en 'datos/liquidacion-manual.csv'.")


def procesar_lote_movimientos(ruta_tarifas=None, ruta_movimientos=None):
    """Opción 2: Procesa el lote de movimientos del archivo JSON."""
    print("\n" + "=" * 45)
    print("      PROCESAR LOTE (JSON -> CSV)")
    print("=" * 45)

    if ruta_tarifas is None:
        ruta_tarifas = get_data_path("tarifas.json")
    if ruta_movimientos is None:
        ruta_movimientos = get_data_path("movimientos.json")

    tarifas = load_json(ruta_tarifas)
    if not tarifas or "tarifas" not in tarifas:
        print(f"Error: No se pudo cargar el archivo de tarifas '{ruta_tarifas}'.")
        return

    movimientos_data = load_json(ruta_movimientos)
    if not movimientos_data or "movimientos" not in movimientos_data:
        print(f"Error: No se pudo cargar el archivo de movimientos '{ruta_movimientos}'.")
        return

    movimientos = movimientos_data["movimientos"]
    validos = []
    rechazados = []

    for m in movimientos:
        if not isinstance(m, dict):
            rechazados.append(["SIN_ID", "SIN_PATENTE", "DESCONOCIDO", "-", "-", False, "El registro no es un objeto válido"])
            continue

        mid = str(m.get("id", "SIN_ID")).strip()
        patente = str(m.get("patente", "")).strip().replace(" ", "").upper()
        tipo = str(m.get("tipo_vehiculo", "")).strip().lower()
        entrada = str(m.get("entrada", "")).strip()
        salida = str(m.get("salida", "")).strip()
        
        # Normalizar lavado tolerante
        lavado_raw = m.get("solicito_lavado", False)
        lavado = lavado_raw in (True, 1, "true", "True", "SI", "si", "s", "S", "true")

        # Validación campo días
        try:
            dias = int(m.get("dias", 0))
            if dias < 0:
                rechazados.append([mid, patente, tipo, entrada, salida, lavado, "Cantidad de días no puede ser negativa"])
                continue
        except (ValueError, TypeError):
            rechazados.append([mid, patente, tipo, entrada, salida, lavado, "Valor de días no es un entero válido"])
            continue

        # Validación 1: Patente
        if not is_valid_plate(patente):
            rechazados.append([mid, patente, tipo, entrada, salida, lavado, "Patente inválida"])
            continue

        # Validación 2: Tipo de vehículo
        if tipo not in tarifas["tarifas"]:
            rechazados.append([mid, patente, tipo, entrada, salida, lavado, f"Tipo de vehículo inválido ('{tipo}')"])
            continue

        # Validación 3: Horarios y minutos
        if dias == 0:
            partes_e = entrada.split(":")
            partes_s = salida.split(":")
            if len(partes_e) != 2 or len(partes_s) != 2 or len(partes_e[0]) != 2 or len(partes_e[1]) != 2 or len(partes_s[0]) != 2 or len(partes_s[1]) != 2:
                rechazados.append([mid, patente, tipo, entrada, salida, lavado, "Formato de hora inválido (debe ser HH:MM con 2 dígitos)"])
                continue

            try:
                eh, em = int(partes_e[0]), int(partes_e[1])
                sh, sm = int(partes_s[0]), int(partes_s[1])
            except ValueError:
                rechazados.append([mid, patente, tipo, entrada, salida, lavado, "Formato numérico de hora inválido"])
                continue

            # Rango de horas y minutos
            if not (0 <= eh <= 23 and 0 <= em <= 59 and 0 <= sh <= 23 and 0 <= sm <= 59):
                rechazados.append([mid, patente, tipo, entrada, salida, lavado, "Horario fuera de rango (00:00 a 23:59)"])
                continue

            minutos = (sh * 60 + sm) - (eh * 60 + em)
            if minutos <= 0:
                rechazados.append([mid, patente, tipo, entrada, salida, lavado, "Hora de salida anterior o igual a entrada"])
                continue
        else:
            minutos = dias * 1440

        # Liquidar registro válido
        liq = liquidar(tipo, dias, minutos, lavado, tarifas)
        validos.append([
            mid, patente, tipo, dias, entrada, salida, minutos,
            liq["estacionamiento_base"], liq["bonificacion_lavado"],
            liq["costo_lavado"], liq["total_cobrado"]
        ])

    # Guardar en datos/liquidacion.csv
    headers_val = [
        "id", "patente", "tipo_vehiculo", "dias", "entrada", "salida",
        "minutos", "estacionamiento_base", "bonificacion_lavado",
        "costo_lavado", "total_cobrado"
    ]
    save_csv(get_data_path("liquidacion.csv"), headers_val, validos, mode="w")

    # Guardar en datos/rechazados.csv
    headers_rech = [
        "id", "patente", "tipo_vehiculo", "entrada", "salida",
        "solicito_lavado", "motivo_rechazo"
    ]
    save_csv(get_data_path("rechazados.csv"), headers_rech, rechazados, mode="w")

    total_recaudado = sum(row[10] for row in validos)

    print("\n" + "-" * 45)
    print("          RESUMEN DE PROCESAMIENTO")
    print("-" * 45)
    print(f"Total registros leídos:       {len(movimientos)}")
    print(f"Registros válidos procesados: {len(validos)} -> datos/liquidacion.csv")
    print(f"Registros rechazados:         {len(rechazados)} -> datos/rechazados.csv")
    print(f"TOTAL RECAUDADO:              {format_currency(total_recaudado)}")
    print("-" * 45)

    if rechazados:
        print("\nDetalle de movimientos rechazados:")
        print("ID | PATENTE | TIPO | MOTIVO")
        print("-" * 45)
        for r in rechazados:
            print(f"{r[0]} | {r[1]} | {r[2]} | {r[6]}")
        print("-" * 45)


def buscar_por_patente():
    """Opción 3: Desafío Nivel 1 - Búsqueda e Historial por Patente."""
    print("\n" + "=" * 45)
    print("    BÚSQUEDA E HISTORIAL POR PATENTE")
    print("=" * 45)

    patente = input("Ingrese la patente a consultar: ").strip().replace(" ", "").upper()
    if not patente:
        print("Error: Ingrese una patente.")
        return

    # Leer ambos archivos desde la carpeta datos/
    filas_lote = read_csv(get_data_path("liquidacion.csv"))
    filas_manual = read_csv(get_data_path("liquidacion-manual.csv"))

    encontrados = []

    for f in filas_lote:
        if f.get("patente", "").strip().replace(" ", "").upper() == patente:
            f["origen"] = "Lote"
            encontrados.append(f)

    for f in filas_manual:
        if f.get("patente", "").strip().replace(" ", "").upper() == patente:
            f["origen"] = "Manual"
            encontrados.append(f)

    if not encontrados:
        print(f"\nNo se encontraron registros para la patente '{patente}'.")
        return

    total_visitas = len(encontrados)
    total_recaudado = 0
    total_minutos = 0

    for reg in encontrados:
        try:
            total_recaudado += float(reg.get("total_cobrado", 0))
        except ValueError:
            pass

        try:
            minutos = int(reg.get("minutos", 0))
            dias = int(reg.get("dias", 0))
            if dias > 0 and minutos == 0:
                minutos = dias * 1440
            total_minutos += minutos
        except ValueError:
            pass

    promedio_minutos = total_minutos / total_visitas if total_visitas > 0 else 0

    print("\n" + "-" * 55)
    print(f"HISTORIAL DE LA PATENTE: {patente}")
    print("-" * 55)
    print(f"Cantidad total de visitas:   {total_visitas}")
    print(f"Total acumulado abonado:     {format_currency(total_recaudado)}")
    print(f"Promedio de permanencia:     {promedio_minutos:.1f} minutos ({promedio_minutos / 60:.1f} hs)")
    print("-" * 55)

    print("\nDetalle de movimientos:")
    print("ORIGEN | ID/FECHA | VEHÍCULO | TIEMPO | TOTAL")
    print("-" * 55)
    for reg in encontrados:
        origen = reg.get("origen", "Lote")
        id_fecha = reg.get("fecha_hora") if reg.get("fecha_hora") else reg.get("id", "-")
        tipo = reg.get("tipo_vehiculo", "").capitalize()
        mins = int(reg.get("minutos", 0))
        dias = int(reg.get("dias", 0))
        duracion = format_duration(mins, dias)
        cobrado = format_currency(float(reg.get("total_cobrado", 0)))
        print(f"{origen} | {id_fecha} | {tipo} | {duracion} | {cobrado}")
    print("=" * 55 + "\n")

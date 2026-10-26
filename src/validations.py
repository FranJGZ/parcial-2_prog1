import re

# Formato Tradicional: 3 letras y 3 números (ej. ABC123)
REGEX_TRADICIONAL = re.compile(r"^[A-Z]{3}[0-9]{3}$")
# Formato Mercosur: 2 letras, 3 números y 2 letras (ej. AA123BB)
REGEX_MERCOSUR = re.compile(r"^[A-Z]{2}[0-9]{3}[A-Z]{2}$")


def is_valid_plate(plate):
    """Verifica si la patente cumple con el formato Tradicional o Mercosur."""
    if not plate:
        return False
    plate_clean = plate.strip().replace(" ", "").upper()
    return bool(REGEX_TRADICIONAL.match(plate_clean) or REGEX_MERCOSUR.match(plate_clean))


def get_patente(message):
    """Solicita una patente por teclado y la valida en bucle."""
    while True:
        user_input = input(message).strip().replace(" ", "").upper()
        if is_valid_plate(user_input):
            return user_input
        print("Error: La patente debe ser formato Tradicional (ABC123) o Mercosur (AA123BB).")


def get_tipo_vehiculo(message, tarifas):
    """Muestra las categorías disponibles y solicita elegir una."""
    tipos = list(tarifas.get("tarifas", {}).keys())
    while True:
        print("\nCategorías disponibles:")
        for idx, t in enumerate(tipos, 1):
            print(f"{idx}. {t.capitalize()}")

        user_input = input(message).strip().lower()

        # Permite ingresar el número (1, 2, 3)
        try:
            opc = int(user_input)
            if 1 <= opc <= len(tipos):
                return tipos[opc - 1]
        except ValueError:
            pass

        # O permite ingresar el texto (auto, moto, camioneta)
        if user_input in tipos:
            return user_input

        print(f"Error: Categoría inválida. Opciones válidas: {', '.join(tipos)}.")


def get_dias(message):
    """Solicita y valida la cantidad de días transcurridos."""
    while True:
        user_input = input(message).strip()
        try:
            dias = int(user_input)
            if dias >= 0:
                return dias
            print("Error: Los días no pueden ser negativos.")
        except ValueError:
            print("Error: Debe ingresar un número entero.")


def get_hora(message):
    """Solicita y valida un horario en formato HH:MM (24 horas)."""
    while True:
        user_input = input(message).strip()
        partes = user_input.split(":")
        if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
            h, m = int(partes[0]), int(partes[1])
            if 0 <= h <= 23 and 0 <= m <= 59 and len(partes[0]) == 2 and len(partes[1]) == 2:
                return user_input
        print("Error: Formato inválido. Debe ser HH:MM entre 00:00 y 23:59.")


def get_horarios_mismo_dia():
    """Solicita hora de entrada y salida, asegurando que la salida sea posterior."""
    while True:
        entrada = get_hora("Ingrese hora de entrada (HH:MM): ")
        salida = get_hora("Ingrese hora de salida  (HH:MM): ")

        eh, em = map(int, entrada.split(":"))
        sh, sm = map(int, salida.split(":"))

        minutos = (sh * 60 + sm) - (eh * 60 + em)
        if minutos > 0:
            return entrada, salida, minutos

        print("Error: La hora de salida debe ser posterior a la de entrada.")


def get_confirmation(message):
    """Solicita confirmación por sí o por no (s/n)."""
    while True:
        answer = input(message).strip().lower()
        if answer in ('s', 'si'):
            return True
        elif answer in ('n', 'no'):
            return False
        print("Error: Por favor ingrese 's' para confirmar o 'n' para cancelar.")


def format_currency(amount):
    """Formatea importes numéricos a pesos con separador de miles."""
    return f"$ {amount:,.0f}".replace(",", ".")


def format_duration(minutos, dias=0):
    """Formatea la duración en minutos o días a un texto legible."""
    if dias > 0:
        return f"{dias} {'día' if dias == 1 else 'días'} ({dias * 24} hs)"
    horas = minutos // 60
    resto = minutos % 60
    if horas > 0 and resto > 0:
        return f"{minutos} min ({horas}h {resto}m)"
    elif horas > 0:
        return f"{minutos} min ({horas}h)"
    return f"{minutos} min"


def print_ticket_card(ticket):
    """Imprime una tarjeta con el desglose del cobro."""
    print("\n" + "=" * 45)
    print("           COMPROBANTE DE COBRO")
    print("=" * 45)
    print(f"Patente:               {ticket['patente']}")
    print(f"Vehículo:              {ticket['tipo_vehiculo'].capitalize()}")
    print(f"Permanencia:           {format_duration(ticket['minutos'], ticket['dias'])}")
    if ticket['dias'] == 0:
        print(f"Horario:               {ticket['entrada']} a {ticket['salida']}")
    print(f"Estacionamiento Base:  {format_currency(ticket['estacionamiento_base'])}")
    if ticket['bonificacion_lavado'] > 0:
        print(f"Bonificación Lavado:  -{format_currency(ticket['bonificacion_lavado'])}")
    print(f"Estacionamiento Neto:  {format_currency(ticket['costo_estacionamiento_neto'])}")
    print(f"Servicio de Lavado:    {format_currency(ticket['costo_lavado'])}")
    print("-" * 45)
    print(f"TOTAL A PAGAR:         {format_currency(ticket['total_cobrado'])}")
    print("=" * 45 + "\n")

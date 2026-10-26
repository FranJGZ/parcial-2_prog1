from operations import (
    registrar_cobro_manual,
    procesar_lote_movimientos,
    buscar_por_patente,
    load_json,
    get_data_path
)


def main():
    # Cargar archivo de tarifas ubicado en datos/tarifas.json
    ruta_tarifas = get_data_path("tarifas.json")
    tarifas = load_json(ruta_tarifas)

    if not tarifas:
        print(f"Error: No se pudo cargar el archivo de tarifas en '{ruta_tarifas}'")
        return

    while True:
        print("\n===== SISTEMA DE GESTIÓN AUTOPARK =====")
        print("1. Registrar cobro manual")
        print("2. Procesar lote de movimientos (JSON -> CSV)")
        print("3. Búsqueda e historial por patente (Desafío Nivel 1)")
        print("4. Salir")

        try:
            option = int(input("Ingrese una opción: "))
        except ValueError:
            print("Error: Ingrese un número")
            continue

        match option:
            case 1:
                registrar_cobro_manual(tarifas)
            case 2:
                procesar_lote_movimientos()
            case 3:
                buscar_por_patente()
            case 4:
                print("Saliendo del sistema...")
                break
            case _:
                print("Opción incorrecta")


if __name__ == "__main__":
    main()

import unittest
from validations import is_valid_plate, format_currency, format_duration
from operations import (
    calcular_estacionamiento_recursivo,
    liquidar,
    load_json,
    procesar_lote_movimientos,
    read_csv,
    get_data_path
)


class TestParcial(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tarifas = load_json(get_data_path("tarifas.json"))
        assert cls.tarifas is not None, "No se pudo cargar tarifas.json desde datos/"

    def test_patentes(self):
        # Validas
        self.assertTrue(is_valid_plate("ABC123"))
        self.assertTrue(is_valid_plate("AA123BB"))
        self.assertTrue(is_valid_plate("  bf 901 gg  "))
        # Invalidas
        self.assertFalse(is_valid_plate("PATENTE99"))
        self.assertFalse(is_valid_plate("A12345"))

    def test_recursividad(self):
        # Auto: bloque 30=$700, hora extra=$1200
        self.assertEqual(calcular_estacionamiento_recursivo(0, "auto", self.tarifas), 0)
        self.assertEqual(calcular_estacionamiento_recursivo(25, "auto", self.tarifas), 700)
        self.assertEqual(calcular_estacionamiento_recursivo(60, "auto", self.tarifas), 1400)
        self.assertEqual(calcular_estacionamiento_recursivo(120, "auto", self.tarifas), 2800)
        # 135 minutos = 4 bloques de 30 min ($2800) + 1 hora extra ($1200) = $4000
        self.assertEqual(calcular_estacionamiento_recursivo(135, "auto", self.tarifas), 4000)

    def test_liquidar_con_lavado(self):
        # <= 120 min bonifica estacionamiento
        res_45 = liquidar("auto", dias=0, minutos=45, solicito_lavado=True, tarifas=self.tarifas)
        self.assertEqual(res_45["bonificacion_lavado"], 1400)
        self.assertEqual(res_45["total_cobrado"], 5000)

        # > 120 min bonifica 2 horas
        res_135 = liquidar("auto", dias=0, minutos=135, solicito_lavado=True, tarifas=self.tarifas)
        self.assertEqual(res_135["bonificacion_lavado"], 2800)
        self.assertEqual(res_135["total_cobrado"], 6200)

    def test_lote(self):
        procesar_lote_movimientos()
        validos = read_csv(get_data_path("liquidacion.csv"))
        rechazados = read_csv(get_data_path("rechazados.csv"))
        self.assertEqual(len(validos), 30)
        self.assertEqual(len(rechazados), 3)


if __name__ == "__main__":
    unittest.main()

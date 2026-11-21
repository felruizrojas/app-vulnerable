import ast
import unittest


class TestAppVulnerable(unittest.TestCase):
    """Pruebas basicas sobre la aplicacion Flask del laboratorio."""

    def setUp(self):
        with open('app.py', encoding='utf-8') as f:
            self.codigo = f.read()

    def test_sintaxis_valida(self):
        """El codigo Python debe ser sintacticamente valido."""
        ast.parse(self.codigo)

    def test_existe_ruta_raiz(self):
        """Debe existir la ruta principal."""
        self.assertIn("@app.route('/')", self.codigo)

    def test_existe_ruta_hello(self):
        """Debe existir el endpoint /hello usado por ZAP."""
        self.assertIn("@app.route('/hello')", self.codigo)

    def test_entrada_usuario_sin_sanitizar(self):
        """Evidencia la vulnerabilidad XSS intencional del laboratorio."""
        self.assertIn("request.args.get('name'", self.codigo)

    def test_modo_debug_activado(self):
        """Evidencia la mala practica de seguridad debug=True."""
        self.assertIn('debug=True', self.codigo)


if __name__ == '__main__':
    unittest.main()

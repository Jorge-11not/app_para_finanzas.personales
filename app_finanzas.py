from datetime import datetime
import sqlite3
import flet as ft


class FinanceAppFlet:

  def __init__(self, page: ft.Page):
    self.page = page
    self.page.title = "FinanzasApp • Mobile & Desktop"
    self.page.theme_mode = ft.ThemeMode.DARK
    self.page.padding = 20
    self.page.scroll = ft.ScrollMode.AUTO

    # Inicializar base de datos SQLite con seguridad para hilos
    self.init_db()

    # Construir interfaz
    self.create_widgets()
    self.load_data()

  def init_db(self):
    """Crea la base de datos y la tabla SQLite."""
    self.conn = sqlite3.connect("finanzas_flet.db", check_same_thread=False)
    self.cursor = self.conn.cursor()
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                monto REAL NOT NULL,
                categoria TEXT NOT NULL,
                fecha TEXT NOT NULL
            )
        """)
    self.conn.commit()

  def create_widgets(self):
    """Diseña los componentes visuales."""
    self.page.add(
        ft.Text(
            "Control de Finanzas", size=22, weight=ft.FontWeight.BOLD, color="green"
        )
    )

    # Estas son las tarjetas de resumen, funcionan para agregar la cantidad
    self.txt_balance = ft.Text("$0.00", size=16, weight=ft.FontWeight.BOLD)
    self.txt_ingresos = ft.Text("$0.00", size=13, color="green")
    self.txt_gastos = ft.Text("$0.00", size=13, color="red")

    resumen_row = ft.Row(
        [
            ft.Container(
                content=ft.Column(
                    [ft.Text("Balance", size=10, color="grey"), self.txt_balance]
                ),
                padding=10,
                bgcolor="#2b2b2b",
                border_radius=8,
                expand=True,
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Ingresos", size=10, color="grey"),
                        self.txt_ingresos,
                    ]
                ),
                padding=10,
                bgcolor="#2b2b2b",
                border_radius=8,
                expand=True,
            ),
            ft.Container(
                content=ft.Column(
                    [ft.Text("Gastos", size=10, color="grey"), self.txt_gastos]
                ),
                padding=10,
                bgcolor="#2b2b2b",
                border_radius=8,
                expand=True,
            ),
        ],
        spacing=10,
    )
    self.page.add(resumen_row)

    # Formulario
    self.tipo_dropdown = ft.Dropdown(
        label="Tipo",
        value="Gasto",
        options=[ft.dropdown.Option("Gasto"), ft.dropdown.Option("Ingreso")],
        border_color="green",
    )

    self.monto_input = ft.TextField(
        label="Monto ($)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color="green",
    )

    self.cat_input = ft.TextField(
        label="Categoría (ej. Comida)", border_color="green"
    )

    btn_guardar = ft.ElevatedButton(
        text="Registrar Movimiento",
        icon=ft.icons.ADD,
        on_click=self.add_transaction,
        bgcolor="green",
        color="white",
        width=float("inf"),
    )

    form_container = ft.Container(
        content=ft.Column(
            [
                ft.Text("Nueva Transacción", size=15, weight=ft.FontWeight.W_500),
                self.tipo_dropdown,
                self.monto_input,
                self.cat_input,
                btn_guardar,
            ],
            spacing=10,
        ),
        padding=15,
        bgcolor="#1e1e1e",
        border_radius=10,
        margin=ft.margin.symmetric(vertical=10),
    )
    self.page.add(form_container)

    # Historial
    self.page.add(
        ft.Text(
            "Historial Reciente", size=15, weight=ft.FontWeight.BOLD, color="white"
        )
    )

    # Esto muestra el registro de transacciones 
    self.history_list = ft.ListView(expand=1, spacing=5, padding=0)
    self.page.add(
        ft.Container(content=self.history_list, height=200, border_radius=8)
    )

  def add_transaction(self, e):
    """Valida e inserta la transacción."""
    tipo = self.tipo_dropdown.value
    monto_str = self.monto_input.value.strip()
    categoria = self.cat_input.value.strip()

    if not monto_str or not categoria:
      self.show_snack("Por favor completa todos los campos.")
      return

    try:
      monto = float(monto_str)
      if monto <= 0:
        raise ValueError
    except ValueError:
      self.show_snack("El monto debe ser un número válido mayor a 0.")
      return

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    self.cursor.execute(
        "INSERT INTO transacciones (tipo, monto, categoria, fecha) VALUES (?, ?,"
        " ?, ?)",
        (tipo, monto, categoria, fecha),
    )
    self.conn.commit()

    # para limpiar datos
    self.monto_input.value = ""
    self.cat_input.value = ""
    self.monto_input.update()
    self.cat_input.update()

    self.load_data()
    self.show_snack("¡Transacción registrada con éxito!")

  def load_data(self):
    """Carga los registros y actualiza la interfaz de forma segura."""
    self.history_list.controls.clear()

    self.cursor.execute(
        "SELECT tipo, monto, categoria, fecha FROM transacciones ORDER BY"
        " id DESC"
    )
    rows = self.cursor.fetchall()

    total_ingresos = 0
    total_gastos = 0

    if not rows:
      self.history_list.controls.append(
          ft.Text("Aún no hay movimientos.", color="grey", italic=True)
      )
    else:
      for row in rows:
        tipo, monto, categoria, fecha = row
        if tipo == "Ingreso":
          total_ingresos += monto
          color = "green"
          signo = "+"
        else:
          total_gastos += monto
          color = "red"
          signo = "-"

        item = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                categoria,
                                weight=ft.FontWeight.BOLD,
                                size=12,
                            ),
                            ft.Text(fecha, size=9, color="grey"),
                        ],
                        spacing=2,
                    ),
                    ft.Text(
                        f"{signo}${monto:.2f}",
                        weight=ft.FontWeight.BOLD,
                        size=13,
                        color=color,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=8,
            bgcolor="#2b2b2b",
            border_radius=6,
        )
        self.history_list.controls.append(item)

    # Actualizar todos los datos
    balance = total_ingresos - total_gastos
    self.txt_balance.value = f"${balance:.2f}"
    self.txt_balance.color = "green" if balance >= 0 else "red"
    self.txt_ingresos.value = f"${total_ingresos:.2f}"
    self.txt_gastos.value = f"${total_gastos:.2f}"

    # Actualizar la página completa
    self.history_list.update()
    self.page.update()

  def show_snack(self, message):
    self.page.snack_bar = ft.SnackBar(ft.Text(message))
    self.page.snack_bar.open = True
    self.page.update()


def main(page: ft.Page):
  FinanceAppFlet(page)


if __name__ == "__main__":
  ft.app(target=main)

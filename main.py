import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

import mysql.connector


class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Laja123*",
            database="panaderia",
            connection_timeout=5,
        )
        self.create_table()
        self.seed_products()

    def create_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS productos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    categoria VARCHAR(50) NOT NULL,
                    precio DECIMAL(10, 2) NOT NULL,
                    stock INT NOT NULL
                )
                """
            )
        self.connection.commit()

    def seed_products(self):
        products = (
            ("Pan francés", "Pan", Decimal("1.50"), 30),
            ("Croissant", "Repostería", Decimal("2.75"), 18),
            ("Concha", "Pan dulce", Decimal("1.25"), 24),
            ("Pastel de chocolate", "Pasteles", Decimal("18.00"), 6),
        )
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM productos")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.executemany(
                    """
                    INSERT INTO productos (nombre, categoria, precio, stock)
                    VALUES (%s, %s, %s, %s)
                    """,
                    products,
                )
        self.connection.commit()

    def get_products(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nombre, categoria, precio, stock
                FROM productos
                ORDER BY id
                """
            )
            return cursor.fetchall()

    def add_product(self, name, category, price, stock):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO productos (nombre, categoria, precio, stock)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (name, category, price, stock),
                )
            self.connection.commit()
        except mysql.connector.Error:
            self.connection.rollback()
            raise

    def update_product(self, product_id, name, category, price, stock):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE productos
                    SET nombre = %s, categoria = %s, precio = %s, stock = %s
                    WHERE id = %s
                    """,
                    (name, category, price, stock, product_id),
                )
            self.connection.commit()
        except mysql.connector.Error:
            self.connection.rollback()
            raise

    def delete_product(self, product_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM productos WHERE id = %s", (product_id,))
            self.connection.commit()
        except mysql.connector.Error:
            self.connection.rollback()
            raise

    def close(self):
        if self.connection.is_connected():
            self.connection.close()


class BakeryInventoryApp:
    BG = "#17191f"
    PANEL = "#20232b"
    FIELD = "#292d37"
    TEXT = "#f4f4f5"
    MUTED = "#a3a8b3"
    ACCENT = "#d99a55"

    def __init__(self, root, database):
        self.root = root
        self.database = database
        self.root.title("Horno & Miga | Inventario")
        self.root.geometry("940x590")
        self.root.minsize(760, 480)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.configure_styles()
        self.build_interface()
        self.refresh_products()
        self.root.after(3000, self.refresh_periodically)

    def configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=self.PANEL,
            fieldbackground=self.PANEL,
            foreground=self.TEXT,
            rowheight=36,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=self.FIELD,
            foreground=self.TEXT,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 10),
        )
        style.map(
            "Treeview",
            background=[("selected", "#59432f")],
            foreground=[("selected", self.TEXT)],
        )
        style.map("Treeview.Heading", background=[("active", "#343945")])
        style.configure(
            "TButton",
            background=self.FIELD,
            foreground=self.TEXT,
            borderwidth=0,
            padding=(14, 9),
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "TButton",
            background=[("active", "#3a3f4b"), ("disabled", self.PANEL)],
            foreground=[("disabled", self.MUTED)],
        )
        style.configure(
            "Accent.TButton",
            background=self.ACCENT,
            foreground="#17191f",
        )
        style.map("Accent.TButton", background=[("active", "#e7ad6c")])
        style.configure("Vertical.TScrollbar", background=self.FIELD, troughcolor=self.BG)

    def build_interface(self):
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill=tk.X, padx=30, pady=(26, 18))

        tk.Label(
            header,
            text="HORNO & MIGA",
            bg=self.BG,
            fg=self.ACCENT,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W)
        tk.Label(
            header,
            text="Inventario de productos",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor=tk.W, pady=(5, 2))
        tk.Label(
            header,
            text="Administra existencias y precios de tu panadería.",
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor=tk.W)

        actions = tk.Frame(self.root, bg=self.BG)
        actions.pack(fill=tk.X, padx=30, pady=(0, 14))
        ttk.Button(
            actions,
            text="＋  Agregar producto",
            style="Accent.TButton",
            command=self.add_product,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            actions, text="Editar seleccionado", command=self.edit_product
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(
            actions, text="Eliminar", command=self.delete_product
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(
            actions, text="Actualizar", command=self.refresh_products
        ).pack(side=tk.RIGHT)

        table_panel = tk.Frame(self.root, bg=self.PANEL, padx=1, pady=1)
        table_panel.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 12))

        columns = ("id", "nombre", "categoria", "precio", "stock")
        self.table = ttk.Treeview(
            table_panel, columns=columns, show="headings", selectmode="browse"
        )
        headings = {
            "id": ("ID", 65, tk.CENTER),
            "nombre": ("Producto", 260, tk.W),
            "categoria": ("Categoría", 190, tk.W),
            "precio": ("Precio", 130, tk.CENTER),
            "stock": ("Existencias", 130, tk.CENTER),
        }
        for column, (title, width, anchor) in headings.items():
            self.table.heading(column, text=title)
            self.table.column(column, width=width, minwidth=60, anchor=anchor)

        scrollbar = ttk.Scrollbar(
            table_panel, orient=tk.VERTICAL, command=self.table.yview
        )
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.status = tk.StringVar(value="Conectado a panaderia")
        tk.Label(
            self.root,
            textvariable=self.status,
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 9),
            anchor=tk.W,
        ).pack(fill=tk.X, padx=30, pady=(0, 16))

    def refresh_products(self, show_error=True):
        try:
            products = self.database.get_products()
            selected = self.table.selection()
            selected_id = self.table.item(selected[0], "values")[0] if selected else None
            self.table.delete(*self.table.get_children())
            for product in products:
                product_id, name, category, price, stock = product
                self.table.insert(
                    "",
                    tk.END,
                    values=(product_id, name, category, f"${price:.2f}", stock),
                )
            if selected_id is not None:
                for item in self.table.get_children():
                    if str(self.table.item(item, "values")[0]) == str(selected_id):
                        self.table.selection_set(item)
                        break
            self.status.set(f"{len(products)} productos · Sincronización cada 3 segundos")
        except mysql.connector.Error as error:
            self.status.set(f"No se pudo actualizar el inventario: {error}")
            if show_error:
                messagebox.showerror(
                    "Error de MySQL",
                    f"No se pudieron cargar los productos.\n\n{error}",
                    parent=self.root,
                )

    def refresh_periodically(self):
        if not self.root.winfo_exists():
            return
        self.refresh_products(show_error=False)
        self.root.after(3000, self.refresh_periodically)

    def selected_product(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showwarning(
                "Selección requerida",
                "Selecciona un producto de la tabla.",
                parent=self.root,
            )
            return None
        return self.table.item(selection[0], "values")

    def add_product(self):
        self.open_product_form()

    def edit_product(self):
        product = self.selected_product()
        if product is not None:
            self.open_product_form(product)

    def open_product_form(self, product=None):
        editing = product is not None
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar producto" if editing else "Agregar producto")
        dialog.configure(bg=self.BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        content = tk.Frame(dialog, bg=self.BG, padx=26, pady=22)
        content.pack(fill=tk.BOTH, expand=True)
        tk.Label(
            content,
            text="Editar producto" if editing else "Nuevo producto",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor=tk.W, pady=(0, 14))

        fields = ("Nombre", "Categoría", "Precio", "Stock")
        entries = {}
        for label in fields:
            tk.Label(
                content,
                text=label,
                bg=self.BG,
                fg=self.MUTED,
                font=("Segoe UI", 9),
            ).pack(anchor=tk.W, pady=(7, 4))
            entry = tk.Entry(
                content,
                bg=self.FIELD,
                fg=self.TEXT,
                insertbackground=self.TEXT,
                relief=tk.FLAT,
                font=("Segoe UI", 10),
                width=36,
            )
            entry.pack(fill=tk.X, ipady=7)
            entries[label] = entry

        if editing:
            entries["Nombre"].insert(0, product[1])
            entries["Categoría"].insert(0, product[2])
            entries["Precio"].insert(0, str(product[3]).replace("$", ""))
            entries["Stock"].insert(0, str(product[4]))

        def save():
            name = entries["Nombre"].get().strip()
            category = entries["Categoría"].get().strip()
            try:
                price = Decimal(entries["Precio"].get().strip())
                stock = int(entries["Stock"].get().strip())
            except (InvalidOperation, ValueError):
                messagebox.showerror(
                    "Datos inválidos",
                    "Ingresa un precio decimal y un stock entero válido.",
                    parent=dialog,
                )
                return

            if not name or not category:
                messagebox.showerror(
                    "Datos incompletos",
                    "El nombre y la categoría son obligatorios.",
                    parent=dialog,
                )
                return
            if len(name) > 100 or len(category) > 50:
                messagebox.showerror(
                    "Texto demasiado largo",
                    "El nombre admite hasta 100 caracteres y la categoría hasta 50.",
                    parent=dialog,
                )
                return
            if not price.is_finite() or price < 0 or price > Decimal("99999999.99"):
                messagebox.showerror(
                    "Precio inválido",
                    "El precio debe estar entre 0 y 99,999,999.99.",
                    parent=dialog,
                )
                return
            if stock < 0 or stock > 2147483647:
                messagebox.showerror(
                    "Stock inválido",
                    "El stock debe estar entre 0 y 2,147,483,647.",
                    parent=dialog,
                )
                return

            try:
                if editing:
                    self.database.update_product(
                        int(product[0]), name, category, price, stock
                    )
                else:
                    self.database.add_product(name, category, price, stock)
            except mysql.connector.Error as error:
                messagebox.showerror(
                    "Error de MySQL",
                    f"No se pudo guardar el producto.\n\n{error}",
                    parent=dialog,
                )
                return

            dialog.destroy()
            self.refresh_products()

        buttons = tk.Frame(content, bg=self.BG)
        buttons.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(buttons, text="Cancelar", command=dialog.destroy).pack(
            side=tk.RIGHT, padx=(8, 0)
        )
        ttk.Button(
            buttons, text="Guardar", style="Accent.TButton", command=save
        ).pack(side=tk.RIGHT)
        entries["Nombre"].focus_set()

    def delete_product(self):
        product = self.selected_product()
        if product is None:
            return
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Deseas eliminar «{product[1]}» del inventario?",
            parent=self.root,
        ):
            return
        try:
            self.database.delete_product(int(product[0]))
        except mysql.connector.Error as error:
            messagebox.showerror(
                "Error de MySQL",
                f"No se pudo eliminar el producto.\n\n{error}",
                parent=self.root,
            )
            return
        self.refresh_products()

    def close(self):
        self.database.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    root.withdraw()

    try:
        database = Database()
    except mysql.connector.Error as error:
        messagebox.showerror(
            "Error de conexión",
            "No se pudo conectar con MySQL.\n"
            "Verifica que MySQL esté iniciado y que exista la base de datos "
            "'panaderia'.\n\n"
            f"Detalle: {error}",
            parent=root,
        )
        root.destroy()
        return

    root.deiconify()
    BakeryInventoryApp(root, database)
    root.mainloop()


if __name__ == "__main__":
    main()

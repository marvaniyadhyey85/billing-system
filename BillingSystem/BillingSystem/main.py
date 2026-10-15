import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
from pathlib import Path

DB_NAME = "billing.db"
TAX_RATE = 5.0


def connect_db():
    return sqlite3.connect(DB_NAME)


def create_database():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_date TEXT NOT NULL,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL,
                tax REAL NOT NULL,
                grand_total REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bill_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (bill_id) REFERENCES bills(bill_id)
            )
        """)


class BillingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Billing Management System")
        self.root.geometry("1000x720")
        self.root.minsize(850, 620)
        self.root.configure(bg="#eef2f7")
        self.cart = []
        self.last_saved_bill_id = None

        self.build_ui()
        self.refresh_table()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text="BILLING MANAGEMENT SYSTEM",
            font=("Arial", 22, "bold"),
            bg="#183153",
            fg="white",
            pady=15
        )
        title.pack(fill="x")

        self.date_label = tk.Label(
            self.root,
            text="Date: " + datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            font=("Arial", 10),
            bg="#eef2f7"
        )
        self.date_label.pack(anchor="e", padx=20, pady=8)

        input_frame = tk.LabelFrame(
            self.root,
            text="Product Details",
            font=("Arial", 11, "bold"),
            bg="#eef2f7",
            padx=10,
            pady=10
        )
        input_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(input_frame, text="Product Name", bg="#eef2f7").grid(
            row=0, column=0, padx=5, pady=5
        )
        self.name_entry = tk.Entry(input_frame, width=25)
        self.name_entry.grid(row=1, column=0, padx=5, pady=5)

        tk.Label(input_frame, text="Price (Rs.)", bg="#eef2f7").grid(
            row=0, column=1, padx=5, pady=5
        )
        self.price_entry = tk.Entry(input_frame, width=15)
        self.price_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Quantity", bg="#eef2f7").grid(
            row=0, column=2, padx=5, pady=5
        )
        self.qty_entry = tk.Entry(input_frame, width=12)
        self.qty_entry.grid(row=1, column=2, padx=5, pady=5)

        tk.Button(
            input_frame, text="Add Product", command=self.add_product,
            bg="#198754", fg="white", width=15
        ).grid(row=1, column=3, padx=10, pady=5)

        table_frame = tk.Frame(self.root, bg="#eef2f7")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("name", "price", "quantity", "amount")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=12
        )
        self.tree.heading("name", text="Product Name")
        self.tree.heading("price", text="Price (Rs.)")
        self.tree.heading("quantity", text="Quantity")
        self.tree.heading("amount", text="Amount (Rs.)")
        self.tree.column("name", width=350)
        self.tree.column("price", width=150, anchor="center")
        self.tree.column("quantity", width=130, anchor="center")
        self.tree.column("amount", width=170, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        summary = tk.LabelFrame(
            self.root,
            text="Bill Summary",
            font=("Arial", 11, "bold"),
            bg="#eef2f7",
            padx=10,
            pady=8
        )
        summary.pack(fill="x", padx=20, pady=5)

        self.subtotal_var = tk.StringVar(value="Rs. 0.00")
        self.discount_var = tk.StringVar(value="Rs. 0.00")
        self.tax_var = tk.StringVar(value="Rs. 0.00")
        self.grand_var = tk.StringVar(value="Rs. 0.00")

        self.add_summary_row(summary, 0, "Subtotal:", self.subtotal_var)
        self.add_summary_row(summary, 1, "Discount:", self.discount_var)
        self.add_summary_row(summary, 2, f"Tax ({TAX_RATE:g}%):", self.tax_var)
        self.add_summary_row(summary, 3, "Grand Total:", self.grand_var)

        tk.Label(summary, text="Discount (%)", bg="#eef2f7").grid(
            row=0, column=2, padx=10
        )
        self.discount_entry = tk.Entry(summary, width=10)
        self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=0, column=3, padx=10)
        self.discount_entry.bind("<KeyRelease>", lambda event: self.calculate_totals())

        button_frame = tk.Frame(self.root, bg="#eef2f7")
        button_frame.pack(fill="x", padx=20, pady=12)

        buttons = [
            ("Remove Product", self.remove_product, "#dc3545"),
            ("Save to Database", self.save_bill, "#0d6efd"),
            ("Generate Bill File", self.generate_bill, "#6f42c1"),
            ("Clear Bill", self.clear_bill, "#6c757d"),
            ("Bill History", self.show_history, "#198754"),
        ]
        for text, command, color in buttons:
            tk.Button(
                button_frame, text=text, command=command,
                bg=color, fg="white", font=("Arial", 9, "bold"),
                padx=7, pady=7
            ).pack(side="left", padx=4)

    @staticmethod
    def add_summary_row(frame, row, label_text, variable):
        tk.Label(
            frame, text=label_text, font=("Arial", 10),
            bg="#eef2f7"
        ).grid(row=row, column=0, sticky="w", padx=10, pady=2)
        tk.Label(
            frame, textvariable=variable, font=("Arial", 10, "bold"),
            bg="#eef2f7"
        ).grid(row=row, column=1, sticky="e", padx=10, pady=2)

    def add_product(self):
        name = self.name_entry.get().strip()
        try:
            price = float(self.price_entry.get())
            quantity = int(self.qty_entry.get())
            if not name:
                messagebox.showerror("Invalid Input", "Enter a product name.")
                return
            if price <= 0 or quantity <= 0:
                messagebox.showerror(
                    "Invalid Input", "Price and quantity must be greater than zero."
                )
                return
        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Enter a valid price and whole-number quantity."
            )
            return

        self.cart.append({
            "name": name,
            "price": price,
            "quantity": quantity,
            "amount": round(price * quantity, 2)
        })
        self.refresh_table()
        self.name_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.qty_entry.delete(0, tk.END)
        self.name_entry.focus_set()

    def remove_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Product", "Select a product to remove.")
            return
        index = self.tree.index(selected[0])
        self.cart.pop(index)
        self.refresh_table()

    def get_totals(self, show_error=True):
        subtotal = round(sum(item["amount"] for item in self.cart), 2)
        try:
            discount_percent = float(self.discount_entry.get() or "0")
            if not 0 <= discount_percent <= 100:
                raise ValueError
        except ValueError:
            if show_error:
                messagebox.showerror(
                    "Invalid Discount", "Discount must be between 0 and 100."
                )
            return None

        discount = round(subtotal * discount_percent / 100, 2)
        taxable_amount = round(subtotal - discount, 2)
        tax = round(taxable_amount * TAX_RATE / 100, 2)
        grand_total = round(taxable_amount + tax, 2)
        return subtotal, discount, tax, grand_total

    def calculate_totals(self):
        totals = self.get_totals(show_error=False)
        if totals is None:
            self.subtotal_var.set("Invalid discount")
            self.discount_var.set("-")
            self.tax_var.set("-")
            self.grand_var.set("-")
            return None

        subtotal, discount, tax, grand_total = totals
        self.subtotal_var.set(f"Rs. {subtotal:.2f}")
        self.discount_var.set(f"Rs. {discount:.2f}")
        self.tax_var.set(f"Rs. {tax:.2f}")
        self.grand_var.set(f"Rs. {grand_total:.2f}")
        return totals

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.cart:
            self.tree.insert("", "end", values=(
                item["name"],
                f'{item["price"]:.2f}',
                item["quantity"],
                f'{item["amount"]:.2f}'
            ))
        self.calculate_totals()

    def save_bill(self):
        if not self.cart:
            messagebox.showwarning("Empty Bill", "Add at least one product.")
            return

        totals = self.get_totals()
        if totals is None:
            return
        subtotal, discount, tax, grand_total = totals
        bill_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO bills
                    (bill_date, subtotal, discount, tax, grand_total)
                    VALUES (?, ?, ?, ?, ?)
                """, (bill_date, subtotal, discount, tax, grand_total))
                bill_id = cursor.lastrowid

                for item in self.cart:
                    cursor.execute("""
                        INSERT INTO bill_items
                        (bill_id, product_name, price, quantity, amount)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        bill_id, item["name"], item["price"],
                        item["quantity"], item["amount"]
                    ))
            self.last_saved_bill_id = bill_id
            messagebox.showinfo(
                "Bill Saved", f"Bill #{bill_id} saved to the database."
            )
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def generate_bill(self):
        if not self.cart:
            messagebox.showwarning("Empty Bill", "Add products before generating a bill.")
            return

        totals = self.get_totals()
        if totals is None:
            return
        subtotal, discount, tax, grand_total = totals
        bill_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        bill_id = self.last_saved_bill_id if self.last_saved_bill_id else "Not saved"

        lines = [
            "=" * 58,
            "                 BILLING SYSTEM",
            "=" * 58,
            f"Bill No: {bill_id}",
            f"Date: {bill_date}",
            "-" * 58,
            f"{'Product':24} {'Price':>9} {'Qty':>5} {'Amount':>12}",
            "-" * 58
        ]
        for item in self.cart:
            lines.append(
                f"{item['name'][:24]:24} {item['price']:9.2f} "
                f"{item['quantity']:5d} {item['amount']:12.2f}"
            )
        lines.extend([
            "-" * 58,
            f"Subtotal:                         Rs. {subtotal:.2f}",
            f"Discount:                         Rs. {discount:.2f}",
            f"Tax ({TAX_RATE:g}%):                           Rs. {tax:.2f}",
            f"GRAND TOTAL:                      Rs. {grand_total:.2f}",
            "=" * 58,
            "                 Thank you!",
            "=" * 58
        ])

        file_path = filedialog.asksaveasfilename(
            title="Save Bill",
            defaultextension=".txt",
            initialfile=f"Bill_{datetime.now():%Y%m%d_%H%M%S}.txt",
            filetypes=[("Text files", "*.txt")]
        )
        if not file_path:
            return
        try:
            Path(file_path).write_text("\n".join(lines), encoding="utf-8")
            messagebox.showinfo("Success", f"Bill saved to:\n{file_path}")
        except OSError as error:
            messagebox.showerror("File Error", str(error))

    def clear_bill(self):
        if self.cart and not messagebox.askyesno(
            "Clear Bill", "Remove all products from the current bill?"
        ):
            return
        self.cart.clear()
        self.last_saved_bill_id = None
        self.discount_entry.delete(0, tk.END)
        self.discount_entry.insert(0, "0")
        self.refresh_table()

    def show_history(self):
        history = tk.Toplevel(self.root)
        history.title("Bill History")
        history.geometry("800x400")

        columns = ("id", "date", "subtotal", "discount", "tax", "total")
        table = ttk.Treeview(history, columns=columns, show="headings")
        headings = {
            "id": "Bill No.",
            "date": "Date",
            "subtotal": "Subtotal",
            "discount": "Discount",
            "tax": "Tax",
            "total": "Grand Total"
        }
        for col, heading in headings.items():
            table.heading(col, text=heading)
        table.column("id", width=70, anchor="center")
        table.column("date", width=190)
        for col in ("subtotal", "discount", "tax", "total"):
            table.column(col, width=110, anchor="e")
        table.pack(fill="both", expand=True, padx=10, pady=10)

        try:
            with connect_db() as conn:
                rows = conn.execute("""
                    SELECT bill_id, bill_date, subtotal, discount, tax, grand_total
                    FROM bills ORDER BY bill_id DESC
                """).fetchall()
            for row in rows:
                table.insert("", "end", values=(
                    row[0], row[1], f"{row[2]:.2f}",
                    f"{row[3]:.2f}", f"{row[4]:.2f}", f"{row[5]:.2f}"
                ))
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error), parent=history)


def main():
    create_database()
    root = tk.Tk()
    BillingSystem(root)
    root.mainloop()


if __name__ == "__main__":
    main()

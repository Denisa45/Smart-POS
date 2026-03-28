import tkinter as tk
from tkinter import messagebox
import webbrowser

from data import products, prep_times
from firebase_config import db
from order_logic import build_order_data
from card_service import process_card_payment
from rfid_reader import read_card_uid

order = {}

BG_MAIN = "#f5f7fb"
BG_CARD = "#ffffff"
BG_PRODUCTS = "#eaf2ff"
BTN_PRODUCT = "#4f8cff"
BTN_REMOVE = "#ff6b6b"
BTN_CHECKOUT = "#2fbf71"
TEXT_DARK = "#1f2937"
TEXT_LIGHT = "#ffffff"
ACCENT = "#dbeafe"


def update_cart():
    cart_list.delete(0, tk.END)
    total = 0

    for product, quantity in order.items():
        subtotal = products[product] * quantity
        cart_list.insert(tk.END, f"{product} x {quantity} - {subtotal} lei")
        total += subtotal

    total_label.config(text=f"Total: {total} lei")


def add_product(product):
    if product in order:
        order[product] += 1
    else:
        order[product] = 1
    update_cart()


def remove_selected():
    selection = cart_list.curselection()

    if not selection:
        messagebox.showwarning("Warning", "Please select a product to remove")
        return

    selected_text = cart_list.get(selection[0])
    product = selected_text.split(" x ")[0]

    order[product] -= 1
    if order[product] == 0:
        del order[product]

    update_cart()

def checkout():
    if not order:
        messagebox.showinfo("Checkout", "Cart is empty")
        return

    payment_method = payment_var.get()
    total = sum(products[p] * q for p, q in order.items())

    try:
        if payment_method == "Card":
            messagebox.showinfo("Card Payment", "Apropie cardul")
            uid = read_card_uid()

            success, message, balance = process_card_payment(uid, total)

            if not success:
                messagebox.showerror("Eroare", message)
                return

            messagebox.showinfo(
                "Succes",
                f"{message}\nSold rămas: {balance} lei"
            )

        data = build_order_data(order, products, prep_times, payment_method, db)

        if payment_method == "Card":
            data["status"] = "paid"
            data["card_uid"] = str(uid)
        else:
            data["status"] = "pending"

        db.child("orders").push(data)
        webbrowser.open(f"http://127.0.0.1:5000/order/{data['order_id']}")

        order.clear()
        update_cart()

    except Exception as e:
        messagebox.showerror("Firebase Error", f"Order could not be saved.\n{e}")
root = tk.Tk()
root.title("Smart POS Kiosk")
root.geometry("900x600")
root.configure(bg=BG_MAIN)

title = tk.Label(
    root,
    text="Smart POS Kiosk",
    font=("Arial", 24, "bold"),
    bg=BG_MAIN,
    fg=TEXT_DARK
)
title.pack(pady=15)

subtitle = tk.Label(
    root,
    text="Touch a product to add it to the order",
    font=("Arial", 12),
    bg=BG_MAIN,
    fg="#4b5563"
)
subtitle.pack(pady=(0, 15))

main_frame = tk.Frame(root, bg=BG_MAIN)
main_frame.pack(fill="both", expand=True, padx=20, pady=10)

left_frame = tk.Frame(main_frame, bg=BG_PRODUCTS, bd=0, relief="flat")
left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=5)

right_frame = tk.Frame(main_frame, bg=BG_CARD, bd=0, relief="flat")
right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=5)

products_title = tk.Label(
    left_frame,
    text="Menu",
    font=("Arial", 18, "bold"),
    bg=BG_PRODUCTS,
    fg=TEXT_DARK
)
products_title.pack(pady=15)

products_frame = tk.Frame(left_frame, bg=BG_PRODUCTS)
products_frame.pack(pady=10, padx=10)

row = 0
col = 0

for product, price in products.items():
    btn = tk.Button(
        products_frame,
        text=f"{product}\n{price} lei",
        font=("Arial", 14, "bold"),
        width=14,
        height=4,
        bg=BTN_PRODUCT,
        fg=TEXT_LIGHT,
        activebackground="#2563eb",
        activeforeground=TEXT_LIGHT,
        relief="flat",
        bd=0,
        command=lambda p=product: add_product(p)
    )
    btn.grid(row=row, column=col, padx=10, pady=10)

    col += 1
    if col > 1:
        col = 0
        row += 1

cart_title = tk.Label(
    right_frame,
    text="Current Order",
    font=("Arial", 18, "bold"),
    bg=BG_CARD,
    fg=TEXT_DARK
)
cart_title.pack(pady=15)

cart_list = tk.Listbox(
    right_frame,
    width=35,
    height=15,
    font=("Arial", 13),
    bg=ACCENT,
    fg=TEXT_DARK,
    selectbackground="#93c5fd",
    selectforeground=TEXT_DARK,
    bd=0,
    relief="flat"
)
cart_list.pack(padx=20, pady=10, fill="both", expand=True)

total_label = tk.Label(
    right_frame,
    text="Total: 0 lei",
    font=("Arial", 18, "bold"),
    bg=BG_CARD,
    fg=TEXT_DARK
)
total_label.pack(pady=10)

payment_label = tk.Label(
    right_frame,
    text="Payment Method",
    font=("Arial", 12, "bold"),
    bg=BG_CARD,
    fg=TEXT_DARK
)
payment_label.pack(pady=(5, 5))

payment_var = tk.StringVar(value="Cash")

payment_menu = tk.OptionMenu(right_frame, payment_var, "Cash", "Card")
payment_menu.config(font=("Arial", 12), bg="#e5e7eb", relief="flat")
payment_menu.pack(pady=(0, 10))

buttons_frame = tk.Frame(right_frame, bg=BG_CARD)
buttons_frame.pack(pady=15)

remove_btn = tk.Button(
    buttons_frame,
    text="Remove Selected",
    font=("Arial", 12, "bold"),
    bg=BTN_REMOVE,
    fg=TEXT_LIGHT,
    activebackground="#dc2626",
    activeforeground=TEXT_LIGHT,
    relief="flat",
    bd=0,
    padx=18,
    pady=10,
    command=remove_selected
)
remove_btn.pack(side="left", padx=10)

checkout_btn = tk.Button(
    buttons_frame,
    text="Checkout",
    font=("Arial", 12, "bold"),
    bg=BTN_CHECKOUT,
    fg=TEXT_LIGHT,
    activebackground="#15803d",
    activeforeground=TEXT_LIGHT,
    relief="flat",
    bd=0,
    padx=18,
    pady=10,
    command=checkout
)
checkout_btn.pack(side="left", padx=10)

root.mainloop()

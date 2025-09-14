from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.core.clipboard import Clipboard
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
import csv
from datetime import datetime


def make_label(text, height=None):
    lbl = Label(text=text, color=(1, 1, 1, 1), halign="center", valign="middle")
    if height:
        lbl.size_hint_y = None
        lbl.height = height
    lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (inst.width, inst.height)))
    return lbl


class ProductRow(GridLayout):
    def __init__(self, product, price_medio=None, price_grande=None, price_fixed=None, update_callback=None, **kwargs):
        cols = 1
        if price_medio:
            cols += 1
        if price_grande:
            cols += 1
        if price_fixed:
            cols += 2
        super().__init__(cols=cols, size_hint_y=None, height=dp(40), spacing=0, **kwargs)
        self.product = product
        self.price_medio = price_medio
        self.price_grande = price_grande
        self.price_fixed = price_fixed
        self.update_callback = update_callback

        # Product name
        self.add_widget(make_label(product))

        # Medio
        if price_medio:
            self.medio_count = 0
            self.medio_label = make_label("0")
            self.add_widget(self._make_counter(self.medio_label, "medio"))

        # Grande
        if price_grande:
            self.grande_count = 0
            self.grande_label = make_label("0")
            self.add_widget(self._make_counter(self.grande_label, "grande"))

        # Fixed-price product (Special Drinks & Secret Menu)
        if price_fixed:
            self.fixed_count = 0
            self.fixed_label = make_label("0")
            self.sale_label = make_label("0")
            self.add_widget(self._make_counter_with_sale(self.fixed_label, self.sale_label, "fixed"))

        with self.canvas.before:
            from kivy.graphics import Color, Line
            Color(1, 1, 1, 1)
            self.rect = Line(rectangle=(self.x, self.y, self.width, self.height), width=1)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.rectangle = (self.x, self.y, self.width, self.height)

    def _make_counter(self, label, kind):
        box = BoxLayout(orientation="horizontal", spacing=2)
        btn_minus = Button(text="-", size_hint_x=None, width=dp(36))
        btn_plus = Button(text="+", size_hint_x=None, width=dp(36))
        btn_minus.bind(on_press=lambda x: self._decrement(label, kind))
        btn_plus.bind(on_press=lambda x: self._increment(label, kind))
        box.add_widget(btn_minus)
        box.add_widget(label)
        box.add_widget(btn_plus)
        return box

    def _make_counter_with_sale(self, label, sale_label, kind):
        box = BoxLayout(orientation="horizontal", spacing=2)
        btn_minus = Button(text="-", size_hint_x=None, width=dp(36))
        btn_plus = Button(text="+", size_hint_x=None, width=dp(36))
        btn_minus.bind(on_press=lambda x: self._decrement_with_sale(label, sale_label, kind))
        btn_plus.bind(on_press=lambda x: self._increment_with_sale(label, sale_label, kind))
        box.add_widget(btn_minus)
        box.add_widget(label)
        box.add_widget(btn_plus)
        box.add_widget(sale_label)
        return box

    def _increment(self, label, kind):
        if kind == "medio":
            self.medio_count += 1
            label.text = str(self.medio_count)
        elif kind == "grande":
            self.grande_count += 1
            label.text = str(self.grande_count)
        if self.update_callback:
            self.update_callback()

    def _decrement(self, label, kind):
        if kind == "medio" and self.medio_count > 0:
            self.medio_count -= 1
            label.text = str(self.medio_count)
        elif kind == "grande" and self.grande_count > 0:
            self.grande_count -= 1
            label.text = str(self.grande_count)
        if self.update_callback:
            self.update_callback()

    def _increment_with_sale(self, label, sale_label, kind):
        if kind == "fixed":
            self.fixed_count += 1
            label.text = str(self.fixed_count)
            sale_label.text = str(self.fixed_count * self.price_fixed)
        if self.update_callback:
            self.update_callback()

    def _decrement_with_sale(self, label, sale_label, kind):
        if kind == "fixed" and self.fixed_count > 0:
            self.fixed_count -= 1
            label.text = str(self.fixed_count)
            sale_label.text = str(self.fixed_count * self.price_fixed)
        if self.update_callback:
            self.update_callback()

    def get_totals(self):
        cups = 0
        sales = 0
        if hasattr(self, "medio_count"):
            cups += self.medio_count
            sales += self.medio_count * (self.price_medio or 0)
        if hasattr(self, "grande_count"):
            cups += self.grande_count
            sales += self.grande_count * (self.price_grande or 0)
        if hasattr(self, "fixed_count"):
            cups += self.fixed_count
            sales += self.fixed_count * (self.price_fixed or 0)
        return cups, sales


class Category(TabbedPanelItem):
    def __init__(self, name, products, kind="size", price_medio=None, price_grande=None, fixed_prices=None,
                 update_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.text = name
        self.kind = kind
        self.price_medio = price_medio
        self.price_grande = price_grande
        self.fixed_prices = fixed_prices or {}
        self.update_callback = update_callback

        scroll = ScrollView()
        self.container = BoxLayout(orientation="vertical", spacing=2, padding=2, size_hint_y=None)
        self.container.bind(minimum_height=self.container.setter("height"))

        headers = ["PRODUCT"]
        if kind == "size":
            headers += ["MEDIO", "GRANDE"]
        elif kind == "single":
            headers += ["COUNT", "SALE"]
        elif kind == "addons":
            headers += ["COUNT"]

        header_grid = GridLayout(cols=len(headers), size_hint_y=None, height=dp(32))
        for h in headers:
            header_grid.add_widget(make_label(h, height=dp(32)))
        self.container.add_widget(header_grid)

        self.rows = []
        for p in products:
            if kind == "single" or kind == "addons":
                price = self.fixed_prices.get(p, None)
                row = ProductRow(p, price_fixed=price, update_callback=self.update_callback)
            else:
                row = ProductRow(p, price_medio=self.price_medio, price_grande=self.price_grande,
                                 update_callback=self.update_callback)
            self.rows.append(row)
            self.container.add_widget(row)

        if kind == "addons":
            self.ao_label = make_label("Total AO: 0 | ₱0", height=dp(28))
            self.es_label = make_label("Total ES: 0 | ₱0", height=dp(28))
            totals_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=8)
            totals_box.add_widget(self.ao_label)
            totals_box.add_widget(self.es_label)
            self.container.add_widget(totals_box)
        elif kind == "size":
            self.medio_label = make_label("Total Medio: 0 cups | ₱0", height=dp(28))
            self.grande_label = make_label("Total Grande: 0 cups | ₱0", height=dp(28))
            totals_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(64), spacing=4)
            totals_box.add_widget(self.medio_label)
            totals_box.add_widget(self.grande_label)
            self.container.add_widget(totals_box)
        else:
            self.single_label = make_label("Total: 0 cups | ₱0", height=dp(28))
            self.container.add_widget(self.single_label)

        scroll.add_widget(self.container)
        self.add_widget(scroll)
        self.last_totals = {"cups": 0, "sales": 0, "ao_cups": 0, "ao_sales": 0, "es_cups": 0, "es_sales": 0}

    def update_totals(self):
        cups = 0
        sales = 0
        if self.kind == "size":
            medio_cups = sum(getattr(r, "medio_count", 0) for r in self.rows)
            grande_cups = sum(getattr(r, "grande_count", 0) for r in self.rows)
            medio_sales = sum(getattr(r, "medio_count", 0) * (r.price_medio or 0) for r in self.rows)
            grande_sales = sum(getattr(r, "grande_count", 0) * (r.price_grande or 0) for r in self.rows)
            self.medio_label.text = f"Total Medio: {medio_cups} cups | ₱{medio_sales}"
            self.grande_label.text = f"Total Grande: {grande_cups} cups | ₱{grande_sales}"
            cups = medio_cups + grande_cups
            sales = medio_sales + grande_sales
        elif self.kind == "single":
            total_cups = sum(getattr(r, "fixed_count", 0) for r in self.rows)
            total_sales = sum(getattr(r, "fixed_count", 0) * (r.price_fixed or 0) for r in self.rows)
            self.single_label.text = f"Total: {total_cups} cups | ₱{total_sales}"
            cups = total_cups
            sales = total_sales
        elif self.kind == "addons":
            ao_cups = sum(getattr(r, "fixed_count", 0) for r in self.rows if r.product != "ES")
            ao_sales = sum(getattr(r, "fixed_count", 0) * r.price_fixed for r in self.rows if r.product != "ES")
            es_cups = sum(getattr(r, "fixed_count", 0) for r in self.rows if r.product == "ES")
            es_sales = sum(getattr(r, "fixed_count", 0) * r.price_fixed for r in self.rows if r.product == "ES")
            self.ao_label.text = f"Total AO: {ao_cups} | ₱{ao_sales}"
            self.es_label.text = f"Total ES: {es_cups} | ₱{es_sales}"
            cups = ao_cups + es_cups
            sales = ao_sales + es_sales
        self.last_totals = {"cups": cups, "sales": sales}
        return self.last_totals


class MainApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical", padding=6, spacing=6)

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(50), padding=6)
        header.add_widget(Label(text="CUPS REPORT", color=(1, 1, 1, 1), font_size='20sp', halign="center"))
        menu_btn = Button(text="☰", size_hint_x=None, width=dp(50))
        header.add_widget(menu_btn)
        root.add_widget(header)

        # Tab panel
        self.panel = TabbedPanel(do_default_tab=False, tab_height=dp(36))
        self.categories = []

        # --- data ---
        praf_products = ["PCA", "PCJ", "PV", "PSL", "PC", "PCC", "PCNC", "PCM", "PJC",
                         "PMO", "PMAT", "PS", "PT", "M. MELON", "M. MANGO", "SCB", "UBE", "PANDAN", "PISTACIO"]
        milk_tea = ["CKMT", "CMT", "CCMT", "CNCMT", "DCMT", "MATMT", "OMT", "RVMT", "SCMT", "SMT", "TMT", "WMT"]
        iced_coffee = ["BIC", "FIC", "KIC", "MACIC", "MOIC", "MATIC", "SIC", "VIC"]
        fruit_tea = ["BFT", "GAFT", "HPFT", "KFT", "LEFT", "LYFT", "MFT", "SFT"]
        brosty_products = ["BB", "BGA", "BHP", "BK", "BLE", "BLY", "BM", "BS"]
        hotbrew_products = ["HB", "HF", "HK", "HMAC", "HMO", "HMAT", "HSL", "HV"]

        hotbrew_prices = {p: 39 for p in hotbrew_products}
        special_prices = {"SDBP": 66, "SDBB": 66, "SDCD": 48, "KMJS": 60, "SDKV": 72,
                          "SDSM": 52, "SDSC": 49, "SDCB": 39}
        secret_prices = {"BARBIE": 82, "BTS": 78, "LOCO": 82, "CRAZY": 82, "TANGO": 77, "BROWNIE": 86}
        addons_prices = {"P": 9, "CJ": 9, "CC": 9, "CP": 9, "CCH": 9, "CO": 9, "C": 9, "ES": 5}

        tabs = [
            ("Add Ons", addons_prices, "addons"),
            ("Brosty", brosty_products, "size", 49, 59),
            ("Fruit Tea", fruit_tea, "size", 29, 39),
            ("Hot Brew", hotbrew_products, "single", None, None, hotbrew_prices),
            ("Iced Coffee", iced_coffee, "size", 29, 39),
            ("Milk Tea", milk_tea, "size", 29, 39),
            ("Praf", praf_products, "size", 49, 59),
            ("Secret Menu", list(secret_prices.keys()), "single", None, None, secret_prices),
            ("Special Drinks", list(special_prices.keys()), "single", None, None, special_prices)
        ]

        for t in tabs:
            if t[2] == "addons":
                cat = Category(t[0], list(t[1].keys()), kind="addons", fixed_prices=t[1],
                               update_callback=self.update_all)
            elif t[2] == "size":
                cat = Category(t[0], t[1], kind="size", price_medio=t[3], price_grande=t[4],
                               update_callback=self.update_all)
            else:
                cat = Category(t[0], t[1], kind="single", fixed_prices=t[5], update_callback=self.update_all)
            self.categories.append(cat)
            self.panel.add_widget(cat)

        root.add_widget(self.panel)

        totals_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(96), padding=6, spacing=4)
        self.total_cups_label = make_label("Total Cups: 0", height=dp(28))
        self.total_sales_label = make_label("Total Sales: ₱0", height=dp(28))
        self.total_addons_label = make_label("Total Add-ons: 0 | ₱0", height=dp(28))
        totals_box.add_widget(self.total_cups_label)
        totals_box.add_widget(self.total_sales_label)
        totals_box.add_widget(self.total_addons_label)
        root.add_widget(totals_box)

        # Menu popup
        def open_menu(instance):
            content = BoxLayout(orientation="vertical", spacing=4, padding=6)
            btn1 = Button(text="Cashier Performance", size_hint_y=None, height=dp(36))
            btn2 = Button(text="Save Report", size_hint_y=None, height=dp(36))
            btn3 = Button(text="Load Report", size_hint_y=None, height=dp(36))
            btn4 = Button(text="Cancel", size_hint_y=None, height=dp(36))

            content.add_widget(btn1)
            content.add_widget(btn2)
            content.add_widget(btn3)
            content.add_widget(btn4)

            menu_popup = Popup(title="Menu", content=content, size_hint=(0.5, 0.5))
            menu_popup.open()

            btn1.bind(on_press=lambda x: (menu_popup.dismiss(), self.show_cashier_performance()))
            btn2.bind(on_press=lambda x: (menu_popup.dismiss(), self.save_report()))

            # Load report functionality
            def load_report_btn(instance):
                menu_popup.dismiss()
                filechooser_layout = BoxLayout(orientation="vertical", spacing=6, padding=6)
                filechooser = FileChooserListView(filters=['*.csv'], path='.', size_hint=(1, 0.9))
                select_btn = Button(text="Select", size_hint=(1, 0.1))
                filechooser_layout.add_widget(filechooser)
                filechooser_layout.add_widget(select_btn)
                chooser_popup = Popup(title="Load Report", content=filechooser_layout, size_hint=(0.9, 0.9))
                chooser_popup.open()

                def load_selected_file(instance):
                    selection = filechooser.selection
                    if selection:
                        filename = selection[0]
                        try:
                            with open(filename, newline='') as file:
                                reader = csv.DictReader(file)
                                # Reset all counts first
                                for cat in self.categories:
                                    for row in cat.rows:
                                        if hasattr(row, "medio_count"): row.medio_count = 0
                                        if hasattr(row, "grande_count"): row.grande_count = 0
                                        if hasattr(row, "fixed_count"): row.fixed_count = 0

                                # Load CSV data
                                for row_data in reader:
                                    cat_name = row_data["Category"]
                                    product = row_data["Product"]
                                    medio = int(row_data.get("Medio", 0) or 0)
                                    grande = int(row_data.get("Grande", 0) or 0)
                                    fixed = int(row_data.get("Fixed", 0) or 0)

                                    # Find category
                                    cat = next((c for c in self.categories if c.text == cat_name), None)
                                    if cat:
                                        # Find product row
                                        p_row = next((r for r in cat.rows if r.product == product), None)
                                        if p_row:
                                            if hasattr(p_row, "medio_count"):
                                                p_row.medio_count = medio
                                                p_row.medio_label.text = str(medio)
                                            if hasattr(p_row, "grande_count"):
                                                p_row.grande_count = grande
                                                p_row.grande_label.text = str(grande)
                                            if hasattr(p_row, "fixed_count"):
                                                p_row.fixed_count = fixed
                                                if hasattr(p_row, "fixed_label"):
                                                    p_row.fixed_label.text = str(fixed)
                                                if hasattr(p_row, "sale_label") and hasattr(p_row, "price_fixed"):
                                                    p_row.sale_label.text = str(fixed * (p_row.price_fixed or 0))
                            chooser_popup.dismiss()
                            self.update_all()
                            Popup(title="Loaded", content=Label(text=f"Report loaded from {filename}"),
                                  size_hint=(0.6, 0.4)).open()
                        except Exception as e:
                            Popup(title="Error", content=Label(text=f"Failed to load file.\n{e}"),
                                  size_hint=(0.6, 0.4)).open()

                select_btn.bind(on_press=load_selected_file)

            btn3.bind(on_press=load_report_btn)
            btn4.bind(on_press=lambda x: menu_popup.dismiss())

        menu_btn.bind(on_press=open_menu)

        self.update_all()
        return root

    def show_cashier_performance(self):
        popup_content = BoxLayout(orientation="vertical", spacing=6, padding=6)
        date_input = TextInput(hint_text="Enter date", size_hint_y=None, height=dp(36))
        cashier_input = TextInput(hint_text="Enter cashier", size_hint_y=None, height=dp(36))
        submit_btn = Button(text="Generate", size_hint_y=None, height=dp(36))
        popup_content.add_widget(Label(text="CASHIER PERFORMANCE"))
        popup_content.add_widget(date_input)
        popup_content.add_widget(cashier_input)
        popup_content.add_widget(submit_btn)
        popup = Popup(title="Cashier Performance", content=popup_content, size_hint=(0.6, 0.6))
        popup.open()

        def generate_report(instance):
            total_cups = sum(cat.last_totals["cups"] for cat in self.categories if cat.kind != "addons")
            total_addons = sum(cat.last_totals["cups"] for cat in self.categories if cat.kind == "addons")
            special_drinks = next(cat.last_totals["cups"] for cat in self.categories if cat.text == "Special Drinks")

            # --- Secret Menu ---
            secret_cat = next(cat for cat in self.categories if cat.text == "Secret Menu")
            bv_total = sum(getattr(r, "fixed_count", 0) for r in secret_cat.rows)
            brownie_count = next((r.fixed_count for r in secret_cat.rows if r.product == "BROWNIE"), 0)
            crazy_count = next((r.fixed_count for r in secret_cat.rows if r.product == "CRAZY"), 0)

            report_text = (
                f"CASHIER PERFORMANCE\n"
                f"DATE: {date_input.text}\n\n"
                f"🟤 San Vicente ({total_cups})\n"
                f"CASHIER: {cashier_input.text}\n"
                f"AO: {total_addons}\n"
                f"SD: {special_drinks}\n"
                f"BV: {bv_total}\n\n"
                f"BROWNIE: {brownie_count}\n"
                f"CRAZY : {crazy_count}"
            )

            Clipboard.copy(report_text)
            popup.dismiss()
            Popup(title="Copied", content=Label(text="Cashier performance copied to clipboard!"),
                  size_hint=(0.5, 0.3)).open()

        submit_btn.bind(on_press=generate_report)

    def save_report(self):
        filename = f"cups_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Category", "Product", "Medio", "Grande", "Fixed", "Sale"])
            for cat in self.categories:
                for row in cat.rows:
                    medio = getattr(row, "medio_count", "")
                    grande = getattr(row, "grande_count", "")
                    fixed = getattr(row, "fixed_count", "")
                    sale = 0
                    if hasattr(row, "price_medio"):
                        sale += getattr(row, "medio_count", 0) * (row.price_medio or 0)
                    if hasattr(row, "price_grande"):
                        sale += getattr(row, "grande_count", 0) * (row.price_grande or 0)
                    if hasattr(row, "fixed_count") and hasattr(row, "price_fixed"):
                        sale += getattr(row, "fixed_count", 0) * (row.price_fixed or 0)
                    writer.writerow([cat.text, row.product, medio, grande, fixed, sale])
        Popup(title="Saved", content=Label(text=f"Report saved to {filename}"), size_hint=(0.6, 0.4)).open()

    def update_all(self, *args):
        total_drink_cups = 0
        total_sales_all = 0
        addons_cups_total = 0
        addons_sales_total = 0

        for cat in self.categories:
            t = cat.update_totals()
            if cat.kind == "addons":
                addons_cups_total = t.get("cups", 0)
                addons_sales_total = t.get("sales", 0)
                total_sales_all += addons_sales_total
            else:
                total_drink_cups += t.get("cups", 0)
                total_sales_all += t.get("sales", 0)

        self.total_cups_label.text = f"Total Cups: {total_drink_cups}"
        self.total_sales_label.text = f"Total Sales: ₱{total_sales_all}"
        self.total_addons_label.text = f"Total Add-ons: {addons_cups_total} | ₱{addons_sales_total}"


if __name__ == "__main__":
    MainApp().run()

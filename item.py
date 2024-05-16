class Item:
    def __init__(self, item: str, variant: str, price: float, sold_out: bool):
        self.item = item
        self.variant = variant
        self.price = price
        self.sold_out = sold_out

    def to_csv(self):
        return f"{self.item}, {self.variant}, {self.price}, {self.sold_out}\n"

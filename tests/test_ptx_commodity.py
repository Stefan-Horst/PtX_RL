from rlptx.ptx.commodity import Commodity
from rlptx.ptx.framework import PtxSystem


class TestConversionComponent():
    
    def setup_method(self):
        self.c = Commodity("c", "")
        self.ptx = PtxSystem()
    
    def test_purchase_commodity__exact(self):
        quantity = 1
        self.c.purchase_price = 2
        self.ptx.balance = 2
        
        values, _, _, exact_completion = self.c.purchase_commodity(quantity, self.ptx)
        
        nquantity, cost = values
        assert nquantity == 1
        assert cost == 2
        assert exact_completion
    
    def test_purchase_commodity__adjusted(self):
        quantity = 2
        self.c.purchase_price = 2
        self.ptx.balance = 2
        
        values, _, _, exact_completion = self.c.purchase_commodity(quantity, self.ptx)
        
        nquantity, cost = values
        assert nquantity == 1
        assert cost == 2
        assert not exact_completion
    
    def test_sell_commodity__exact(self):
        quantity = 1
        self.c.available_quantity = 1
        self.c.sale_price = 2
        
        values, _, _, exact_completion = self.c.sell_commodity(quantity, self.ptx)
        
        nquantity, revenue = values
        assert nquantity == 1
        assert revenue == 2
        assert exact_completion
    
    def test_sell_commodity__adjusted(self):
        quantity = 2
        self.c.available_quantity = 1
        self.c.sale_price = 2
        
        values, _, _, exact_completion = self.c.sell_commodity(quantity, self.ptx)
        
        nquantity, revenue = values
        assert nquantity == 1
        assert revenue == 2
        assert not exact_completion
    
    def test_emit_commodity__exact(self):
        quantity = 1
        self.c.available_quantity = 1
        
        values, _, _, exact_completion = self.c.emit_commodity(quantity, self.ptx)
        
        nquantity = values[0]
        assert nquantity == 1
        assert exact_completion
    
    def test_emit_commodity__adjusted(self):
        quantity = 2
        self.c.available_quantity = 1
        
        values, _, _, exact_completion = self.c.emit_commodity(quantity, self.ptx)
        
        nquantity = values[0]
        assert nquantity == 1
        assert not exact_completion

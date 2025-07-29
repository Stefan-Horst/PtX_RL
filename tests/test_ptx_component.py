from rlptx.ptx.component import GenerationComponent
from rlptx.ptx.framework import PtxSystem


class TestGenerationComponent():
    
    def setup_method(self):
        self.gc = GenerationComponent("sc")
        self.ptx = PtxSystem()
    
    def test_apply_or_strip_curtailment__apply(self, mocker):
        quantity = 1
        self.gc.fixed_capacity = 3
        self.gc.curtailment = 1
        self.gc.variable_om = 1
        self.ptx.balance = 1
        mocker.patch("rlptx.ptx.framework.PtxSystem.get_current_weather_coefficient", return_value=1.0)
        
        values, _, success, exact_completion = self.gc.apply_or_strip_curtailment(quantity, self.ptx)
        
        nquantity, generated, cost, possible_current_generation = values
        assert nquantity == 1
        assert generated == 1
        assert cost == 1
        assert possible_current_generation == 3
        assert success
        assert exact_completion
    
    def test_apply_or_strip_curtailment__strip(self, mocker):
        quantity = -1
        self.gc.fixed_capacity = 3
        self.gc.curtailment = 3
        self.gc.variable_om = 1
        self.ptx.balance = 1
        mocker.patch("rlptx.ptx.framework.PtxSystem.get_current_weather_coefficient", return_value=1.0)
        
        values, _, success, exact_completion = self.gc.apply_or_strip_curtailment(quantity, self.ptx)
        
        nquantity, generated, cost, possible_current_generation = values
        assert nquantity == -1
        assert generated == 1
        assert cost == 1
        assert possible_current_generation == 3
        assert success
        assert exact_completion
    
    def test_check_quantity_not_higher_than_potential_generation__exact(self):
        quantity = 1
        generated = 1
        potential_max_generation = 2
        
        nquantity, ngenerated, exact_completion, _ = self.gc._check_quantity_not_higher_than_potential_generation(
            quantity, generated, potential_max_generation, ""
        )

        assert nquantity == 1
        assert ngenerated == 1
        assert exact_completion
    
    def test_check_quantity_not_higher_than_potential_generation__adjusted(self):
        quantity = 2
        generated = 1
        potential_max_generation = 1
        
        nquantity, ngenerated, exact_completion, _ = self.gc._check_quantity_not_higher_than_potential_generation(
            quantity, generated, potential_max_generation, ""
        )
        
        assert nquantity == 1
        assert ngenerated == 0
        assert not exact_completion
    
    def test_check_curtail_strip_quantity_not_higher_than_curtailment__exact(self):
        quantity = 1
        generated = 1
        possible_current_generation = 1
        self.gc.curtailment = 1
        
        nquantity, ngenerated, exact_completion, _ = self.gc._check_curtail_strip_quantity_not_higher_than_curtailment(
            quantity, generated, possible_current_generation, ""
        )
        
        assert nquantity == 1
        assert ngenerated == 1
        assert exact_completion
    
    def test_check_curtail_strip_quantity_not_higher_than_curtailment__adjusted(self):
        quantity = 2
        generated = 2
        possible_current_generation = 1
        self.gc.curtailment = 1
        
        nquantity, ngenerated, exact_completion, _ = self.gc._check_curtail_strip_quantity_not_higher_than_curtailment(
            quantity, generated, possible_current_generation, ""
        )
        
        assert nquantity == 1
        assert ngenerated == 1
        assert not exact_completion
    
    def test_check_cost_not_higher_than_balance__exact(self):
        quantity = 1
        generated = 1
        cost = 1
        possible_current_generation = 3
        balance = 1
        self.gc.variable_om = 1
        self.gc.curtailment = 1
        
        nquantity, ngenerated, ncost, exact_completion, _ = self.gc._check_cost_not_higher_than_balance(
            quantity, generated, cost, possible_current_generation, balance, ""
        )
        
        assert nquantity == 1
        assert ngenerated == 1
        assert ncost == 1
        assert exact_completion
    
    def test_check_cost_not_higher_than_balance__adjusted(self):
        quantity = 2
        generated = 2
        cost = 2
        possible_current_generation = 5
        balance = 1
        self.gc.variable_om = 1
        self.gc.curtailment = 1
        
        nquantity, ngenerated, ncost, exact_completion, _ = self.gc._check_cost_not_higher_than_balance(
            quantity, generated, cost, possible_current_generation, balance, ""
        )
        
        assert nquantity == 3
        assert ngenerated == 1
        assert ncost == 1
        assert not exact_completion

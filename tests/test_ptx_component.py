from rlptx.ptx.component import StorageComponent, GenerationComponent
from rlptx.ptx.framework import PtxSystem
from rlptx.ptx.commodity import Commodity


class TestStorageComponent():
    
    def setup_method(self):
        self.sc = StorageComponent("sc")
        self.ptx = PtxSystem()
        self.ptx.commodities = {"Electricity": Commodity("Electricity", None)}
    
    def test_charge_or_discharge_quantity__charge(self):
        quantity = 2
        self.sc.stored_commodity = "Electricity"
        self.sc.fixed_capacity = 4
        self.sc.max_soc = 0.75
        self.sc.min_soc = 0.25
        self.sc.charge_state = 1
        self.sc.ratio_capacity_p = 0.5
        self.sc.charging_efficiency = 0.5
        self.sc.variable_om = 1
        self.ptx.balance = 2
        self.ptx.commodities["Electricity"].available_quantity = 2
        
        values, _, success, exact_completion = self.sc.charge_or_discharge_quantity(quantity, self.ptx)
        
        nquantity, actual_quantity, cost, is_charging = values
        assert nquantity == 2
        assert actual_quantity == 1
        assert cost == 2
        assert is_charging
        assert success
        assert exact_completion
    
    def test_charge_or_discharge_quantity__discharge(self):
        quantity = -1
        self.sc.stored_commodity = "Electricity"
        self.sc.fixed_capacity = 4
        self.sc.max_soc = 0.75
        self.sc.min_soc = 0.25
        self.sc.charge_state = 3
        self.sc.ratio_capacity_p = 0.5
        self.sc.discharging_efficiency = 0.5
        self.ptx.balance = 0
        
        values, _, success, exact_completion = self.sc.charge_or_discharge_quantity(quantity, self.ptx)
        
        nquantity, actual_quantity, cost, is_charging = values
        assert nquantity == -2
        assert actual_quantity == -1
        assert cost == 0
        assert not is_charging
        assert success
        assert exact_completion
    
    def test_check_actual_quantity_not_higher_than_possible_amount__exact(self):
        quantity = 2
        actual_quantity = 1
        max_possible_amount = 1
        self.sc.charging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_actual_quantity_not_higher_than_possible_amount(
            quantity, actual_quantity, max_possible_amount, ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert exact_completion
    
    def test_check_actual_quantity_not_higher_than_possible_amount__adjusted(self):
        quantity = 4
        actual_quantity = 2
        max_possible_amount = 1
        self.sc.charging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_actual_quantity_not_higher_than_possible_amount(
            quantity, actual_quantity, max_possible_amount, ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert not exact_completion
    
    def test_check_actual_quantity_not_higher_than_free_storage__exact(self):
        quantity = 2
        actual_quantity = 1
        free_storage = 1
        self.sc.charging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_actual_quantity_not_higher_than_free_storage(
            quantity, actual_quantity, free_storage, ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert exact_completion
    
    def test_check_actual_quantity_not_higher_than_free_storage__adjusted(self):
        quantity = 4
        actual_quantity = 2
        free_storage = 1
        self.sc.charging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_actual_quantity_not_higher_than_free_storage(
            quantity, actual_quantity, free_storage, ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert not exact_completion
    
    def test_check_quantity_not_higher_than_available_quantity__exact(self):
        quantity = 2
        actual_quantity = 1
        available_quantity = 2
        self.sc.charging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_quantity_not_higher_than_available_quantity(
            quantity, actual_quantity, available_quantity, ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert exact_completion
    
    def test_check_quantity_not_higher_than_available_quantity__adjusted(self):
        quantity = 4
        actual_quantity = 2
        available_quantity = 2
        self.sc.charging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_quantity_not_higher_than_available_quantity(
            quantity, actual_quantity, available_quantity, ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert not exact_completion
    
    def test_check_cost_not_higher_than_balance__exact(self):
        quantity = 2
        actual_quantity = 1
        cost = 2
        balance = 2
        self.sc.charging_efficiency = 0.5
        self.sc.variable_om = 1
        
        nquantity, nactual_quantity, ncost, exact_completion, _ = self.sc._check_cost_not_higher_than_balance(
            quantity, actual_quantity, cost, balance, ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert ncost == 2
        assert exact_completion
    
    def test_check_cost_not_higher_than_balance__adjusted(self):
        quantity = 4
        actual_quantity = 2
        cost = 4
        balance = 2
        self.sc.charging_efficiency = 0.5
        self.sc.variable_om = 1
        
        nquantity, nactual_quantity, ncost, exact_completion, _ = self.sc._check_cost_not_higher_than_balance(
            quantity, actual_quantity, cost, balance, ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert ncost == 2
        assert not exact_completion
    
    def test_check_discharge_quantity_not_higher_than_possible_amount__exact(self):
        quantity = 2
        actual_quantity = 1
        max_possible_amount = 2
        self.sc.discharging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_discharge_quantity_not_higher_than_possible_amount(
            quantity, actual_quantity, max_possible_amount, "", ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert exact_completion
    
    def test_check_discharge_quantity_not_higher_than_possible_amount__adjusted(self):
        quantity = 4
        actual_quantity = 2
        max_possible_amount = 2
        self.sc.discharging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_discharge_quantity_not_higher_than_possible_amount(
            quantity, actual_quantity, max_possible_amount, "", ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert not exact_completion
    
    def test_check_discharge_quantity_not_higher_than_dischargeable_quantity__exact(self):
        quantity = 2
        actual_quantity = 1
        dischargeable_quantity = 2
        self.sc.discharging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_discharge_quantity_not_higher_than_dischargeable_quantity(
            quantity, actual_quantity, dischargeable_quantity, "", ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert exact_completion
    
    def test_check_discharge_quantity_not_higher_than_dischargeable_quantity__adjusted(self):
        quantity = 4
        actual_quantity = 2
        dischargeable_quantity = 2
        self.sc.discharging_efficiency = 0.5
        
        nquantity, nactual_quantity, exact_completion, _ = self.sc._check_discharge_quantity_not_higher_than_dischargeable_quantity(
            quantity, actual_quantity, dischargeable_quantity, "", ""
        )
        
        assert nquantity == 2
        assert nactual_quantity == 1
        assert not exact_completion


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

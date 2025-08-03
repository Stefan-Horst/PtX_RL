from pytest import approx

from rlptx.ptx.component import ConversionComponent, StorageComponent, GenerationComponent
from rlptx.ptx.framework import PtxSystem
from rlptx.ptx.commodity import Commodity


class TestConversionComponent():
    
    def setup_method(self):
        self.cc = ConversionComponent("cc")
        self.cc.inputs = {"Electricity": 1.0, "Water": 0.5}
        self.cc.main_input = "Electricity"
        self.cc.outputs = {"H2": 2.0, "O2": 2.0}
        self.cc.main_output = "H2"
        self.ptx = PtxSystem()
        self.ptx.commodities = {
            "Electricity": Commodity("Electricity", None), 
            "Water": Commodity("Water", None), 
            "H2": Commodity("H2", None), 
            "O2": Commodity("O2", None)
        }
    
    def test_ramp_up_or_down__up(self):
        quantity = 0.5
        self.cc.load = 0.5
        self.cc.fixed_capacity = 10
        self.cc.variable_om = 1
        self.cc.main_output = "H2"
        self.cc.ramp_up = 0.5
        self.cc.max_p = 1
        self.cc.ramp_down = 0.5
        self.cc.min_p = 0
        self.ptx.balance = 20
        self.ptx.commodities["Electricity"].available_quantity = 10
        self.ptx.commodities["Water"].available_quantity = 5
        
        values, _, success, exact_completion = self.cc.ramp_up_or_down(quantity, self.ptx)
        nquantity, cost, input_values, output_values = values
        input_vals = list(input_values)
        output_vals = list(output_values)
        assert nquantity == approx(0.5)
        assert cost == 20
        assert input_vals[0] == (self.ptx.commodities["Electricity"], 10)
        assert input_vals[1] == (self.ptx.commodities["Water"], 5)
        assert output_vals[0] == (self.ptx.commodities["H2"], 20)
        assert output_vals[1] == (self.ptx.commodities["O2"], 20)
        assert success
        assert exact_completion
    
    def test_ramp_up_or_down__down(self):
        quantity = -0.5
        self.cc.load = 1
        self.cc.fixed_capacity = 10
        self.cc.variable_om = 1
        self.cc.main_output = "H2"
        self.cc.ramp_up = 0.5
        self.cc.max_p = 1
        self.cc.ramp_down = 0.5
        self.cc.min_p = 0
        self.ptx.balance = 10
        self.ptx.commodities["Electricity"].available_quantity = 5
        self.ptx.commodities["Water"].available_quantity = 2.5
        
        values, _, success, exact_completion = self.cc.ramp_up_or_down(quantity, self.ptx)
        
        nquantity, cost, input_values, output_values = values
        input_values = list(input_values)
        output_values = list(output_values)
        assert nquantity == approx(-0.5)
        assert cost == 10
        assert input_values[0] == (self.ptx.commodities["Electricity"], 5)
        assert input_values[1] == (self.ptx.commodities["Water"], approx(2.5))
        assert output_values[0] == (self.ptx.commodities["H2"], 10)
        assert output_values[1] == (self.ptx.commodities["O2"], 10)
        assert success
        assert exact_completion
    
    def test_ramp_up_or_down__fail_cost(self):
        quantity = 0.5
        self.cc.load = 0.5
        self.cc.fixed_capacity = 10
        self.cc.variable_om = 1
        self.cc.main_output = "H2"
        self.cc.ramp_up = 0.5
        self.cc.max_p = 1
        self.cc.ramp_down = 0.5
        self.cc.min_p = 0.1 # make conversion unable to just shut down
        self.ptx.balance = 0
        self.ptx.commodities["Electricity"].available_quantity = 10
        self.ptx.commodities["Water"].available_quantity = 5
        
        values, _, success, exact_completion = self.cc.ramp_up_or_down(quantity, self.ptx)
        
        assert values == (0,0,[],[])
        assert not success
        assert not exact_completion
    
    def test_ramp_up_or_down__fail_conversion(self):
        quantity = 0.5
        self.cc.load = 0.5
        self.cc.fixed_capacity = 10
        self.cc.variable_om = 1
        self.cc.main_output = "H2"
        self.cc.ramp_up = 0.5
        self.cc.max_p = 1
        self.cc.ramp_down = 0.1
        self.cc.min_p = 0.1 # make conversion unable to just shut down
        self.ptx.balance = 10
        self.ptx.commodities["Electricity"].available_quantity = 10
        self.ptx.commodities["Water"].available_quantity = 0
        
        values, _, success, exact_completion = self.cc.ramp_up_or_down(quantity, self.ptx)
        
        assert values == (0,0,[],[])
        assert not success
        assert not exact_completion
    
    def test_normalize_commodity_ratios_based_on_main_input(self):
        self.cc.inputs = {"Electricity": 0.5, "Water": 1.0}
        
        self.cc._normalize_commodity_ratios_based_on_main_input()
        
        assert self.cc.inputs == {"Electricity": 1, "Water": 2}
        assert self.cc.outputs == {"H2": 4, "O2": 4}
    
    def test_try_convert_commodities__exact(self):
        self.ptx.commodities["Electricity"].available_quantity = 1
        self.ptx.commodities["Water"].available_quantity = 1
        input_values = [(self.ptx.commodities["Electricity"], 1), (self.ptx.commodities["Water"], 1)]
        output_values = [(self.ptx.commodities["H2"], 1), (self.ptx.commodities["O2"], 1)]
        
        success, _, _ = self.cc._try_convert_commodities(
            input_values, output_values, ""
        )
        
        assert success
    
    def test_try_convert_commodities__adjusted(self):
        self.ptx.commodities["Electricity"].available_quantity = 1
        self.ptx.commodities["Water"].available_quantity = 0.5
        input_values = [(self.ptx.commodities["Electricity"], 1), (self.ptx.commodities["Water"], 1)]
        output_values = [(self.ptx.commodities["H2"], 1), (self.ptx.commodities["O2"], 1)]
        
        success, _, _ = self.cc._try_convert_commodities(
            input_values, output_values, ""
        )
        
        assert not success
    
    def test_check_cost_not_higher_than_balance__exact(self):
        quantity = 0.5
        main_output_conversion_coefficient = 0.5
        current_capacity = 2
        self.cc.variable_om = 1
        self.cc.fixed_capacity = 4
        self.cc.load = 0.5
        self.ptx.balance = 1
        
        nquantity, exact_completion, _ = self.cc._check_cost_not_higher_than_balance(
            quantity, self.ptx.balance, main_output_conversion_coefficient, current_capacity, ""
        )
        
        assert nquantity == approx(0.5)
        assert exact_completion
    
    def test_check_cost_not_higher_than_balance__adjusted(self):
        quantity = 0.5
        main_output_conversion_coefficient = 0.5
        current_capacity = 4
        self.cc.variable_om = 1
        self.cc.fixed_capacity = 8
        self.cc.load = 0.5
        self.ptx.balance = 1
        
        nquantity, exact_completion, _ = self.cc._check_cost_not_higher_than_balance(
            quantity, self.ptx.balance, main_output_conversion_coefficient, current_capacity, ""
        )
        
        assert nquantity == approx(-0.25)
        assert not exact_completion
    
    def test_check_quantity_not_higher_than_ramp_up__exact(self):
        quantity = 0.5
        self.cc.ramp_up = 0.5
        
        nquantity, exact_completion, _ = self.cc._check_quantity_not_higher_than_ramp_up(
            quantity, ""
        )
        
        assert nquantity == approx(0.5)
        assert exact_completion
    
    def test_check_quantity_not_higher_than_ramp_up__adjusted(self):
        quantity = 0.6
        self.cc.ramp_up = 0.5
        
        nquantity, exact_completion, _ = self.cc._check_quantity_not_higher_than_ramp_up(
            quantity, ""
        )
        
        assert nquantity == approx(0.5)
        assert not exact_completion
    
    def test_check_load_not_higher_than_max_p__exact(self):
        quantity = 0.4
        new_load = 0.5
        self.cc.max_p = 0.5
        self.cc.load = 0.1
        
        nquantity, nnew_load, exact_completion, _ = self.cc._check_load_not_higher_than_max_p(
            quantity, new_load, ""
        )
        
        assert nquantity == approx(0.4)
        assert nnew_load == approx(0.5)
        assert exact_completion
    
    def test_check_load_not_higher_than_max_p__adjusted(self):
        quantity = 0.5
        new_load = 0.6
        self.cc.max_p = 0.5
        self.cc.load = 0.1
        
        nquantity, nnew_load, exact_completion, _ = self.cc._check_load_not_higher_than_max_p(
            quantity, new_load, ""
        )
        
        assert nquantity == approx(0.4)
        assert nnew_load == approx(0.5)
        assert not exact_completion
    
    def test_check_reduction_quantity_not_higher_than_ramp_down__exact(self):
        quantity = 0.5
        self.cc.ramp_down = 0.5
        
        nquantity, exact_completion, _ = self.cc._check_reduction_quantity_not_higher_than_ramp_down(
            quantity, ""
        )
        
        assert nquantity == approx(0.5)
        assert exact_completion
    
    def test_check_reduction_quantity_not_higher_than_ramp_down__adjusted(self):
        quantity = 0.6
        self.cc.ramp_down = 0.5
        
        nquantity, exact_completion, _ = self.cc._check_reduction_quantity_not_higher_than_ramp_down(
            quantity, ""
        )
        
        assert nquantity == approx(0.5)
        assert not exact_completion
    
    def test_check_load_not_lower_than_min_p__exact(self):
        quantity = 0.3
        new_load = 0.2
        self.cc.load = 0.5
        self.cc.min_p = 0.2
        
        nquantity, nnew_load, exact_completion, _ = self.cc._check_load_not_lower_than_min_p(
            quantity, new_load, ""
        )
        
        assert nquantity == approx(0.3)
        assert nnew_load == approx(0.2)
        assert exact_completion
    
    def test_check_load_not_lower_than_min_p__adjusted(self):
        quantity = 0.4
        new_load = 0.1
        self.cc.load = 0.5
        self.cc.min_p = 0.2
        
        nquantity, nnew_load, exact_completion, _ = self.cc._check_load_not_lower_than_min_p(
            quantity, new_load, ""
        )
        
        assert nquantity == approx(0.3)
        assert nnew_load == approx(0.2)
        assert not exact_completion
    
    def test_check_enough_inputs_available__exact(self):
        quantity = 0.5
        new_load = 1
        self.ptx.commodities["Electricity"].available_quantity = 10
        self.ptx.commodities["Water"].available_quantity = 5
        input_commodities = list(self.ptx.commodities.values())[:2]
        input_ratios = self.cc.inputs.values()
        self.cc.fixed_capacity = 10
        self.cc.load = 0.5
        self.cc.ramp_down = 0.5
        self.cc.min_p = 0.1
        
        nquantity, nnew_load, exact_completion, _ = self.cc._check_enough_inputs_available(
            quantity, new_load, input_commodities, input_ratios, ""
        )
        
        assert nquantity == approx(0.5)
        assert nnew_load == 1
        assert exact_completion
    
    def test_check_enough_inputs_available__adjusted(self):
        quantity = 0.5
        new_load = 1
        self.ptx.commodities["Electricity"].available_quantity = 10
        self.ptx.commodities["Water"].available_quantity = 4
        input_commodities = list(self.ptx.commodities.values())[:2]
        input_ratios = self.cc.inputs.values()
        self.cc.fixed_capacity = 10
        self.cc.load = 0.5
        self.cc.ramp_down = 0.5
        self.cc.min_p = 0.1
        
        nquantity, nnew_load, exact_completion, _ = self.cc._check_enough_inputs_available(
            quantity, new_load, input_commodities, input_ratios, ""
        )
        
        assert nquantity == approx(0.3)
        assert nnew_load == approx(0.8)
        assert not exact_completion


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

import copy

from ptx.core import Element


class BaseComponent(Element):
    """Abstract base class for components which cannot be instantiated directly."""
    
    def __init__(self, name, variable_om, fixed_capacity=0., total_variable_costs=0.):
        """
        Defines basic component class

        :param name: [string] - abbreviation of component
        :param variable_om: [float] - variable operation and maintenance
        """
        
        self.name = str(name)
        self.component_type = None

        self.variable_om = float(variable_om)

        self.fixed_capacity = float(fixed_capacity)

        self.total_variable_costs = float(total_variable_costs)

    def __copy__(self):
        return BaseComponent(name=self.name, variable_om=self.variable_om,
                             fixed_capacity=self.fixed_capacity,
                             total_variable_costs=self.total_variable_costs)


class ConversionComponent(BaseComponent):
    
    def __init__(self, name, variable_om=0., ramp_down=1., ramp_up=1., 
                 min_p=0., max_p=1., inputs=None, outputs=None, main_input=None, 
                 main_output=None, commodities=None, fixed_capacity=0., 
                 consumed_commodities=None, produced_commodities=None):
        """
        Class of conversion units
        
        :param name: [string] - Abbreviation of unit
        :param variable_om: [float] - variable operation and maintenance
        :param ramp_down: [float] - Ramp down between time steps in % / h
        :param ramp_up: [float] - Ramp up between time steps in % / h
        :param inputs: [Dict] - inputs of component
        :param outputs: [Dict] - outputs of component
        :param main_input: [str] - main input of component
        :param main_output: [str] - main output of component
        :param min_p: [float] - Minimal power of the unit when operating
        :param max_p: [float] - Maximal power of the unit when operating
        :param commodities: [list] - Commodities of the unit
        """

        super().__init__(name=name, variable_om=variable_om, fixed_capacity=fixed_capacity)

        self.component_type = 'conversion'

        if inputs is None:
            self.inputs = {}
            self.outputs = {}
            self.main_input = str
            self.main_output = str
        else:
            self.inputs = inputs
            self.outputs = outputs
            self.main_input = main_input
            self.main_output = main_output

        if commodities is None:
            self.commodities = []
        else:
            self.commodities = commodities

        self.min_p = float(min_p)
        self.max_p = float(max_p)
        self.ramp_down = float(ramp_down)
        self.ramp_up = float(ramp_up)

        self.consumed_commodities = consumed_commodities
        self.produced_commodities = produced_commodities
        
        self._initialize_result_dictionaries()

    def add_input(self, input_commodity, coefficient):
        self.inputs.update({input_commodity: float(coefficient)})
        self.add_commodity(input_commodity)
        self._initialize_result_dictionaries()

    def remove_input(self, input_commodity):
        self.inputs.pop(input_commodity)
        self.remove_commodity(input_commodity)
        self._initialize_result_dictionaries()

    def add_output(self, output_commodity, coefficient):
        self.outputs.update({output_commodity: float(coefficient)})
        self.add_commodity(output_commodity)
        self._initialize_result_dictionaries()

    def remove_output(self, output_commodity):
        self.outputs.pop(output_commodity)
        self.remove_commodity(output_commodity)
        self._initialize_result_dictionaries()

    def add_commodity(self, commodity):
        if commodity not in self.commodities:
            self.commodities.append(commodity)

    def remove_commodity(self, commodity):
        if commodity in self.commodities:
            self.commodities.remove(commodity)

    def set_specific_consumed_commodities(self, commodity, quantity):
        self.consumed_commodities.update({commodity: quantity})

    def get_specific_consumed_commodities(self, commodity):
        if commodity not in self.commodities:
            return 0
        else:
            return self.consumed_commodities[commodity]

    def set_specific_produced_commodities(self, commodity, quantity):
        self.produced_commodities.update({commodity: quantity})

    def get_specific_produced_commodities(self, commodity):
        if commodity not in self.commodities:
            return 0
        else:
            return self.produced_commodities[commodity]

    def get_possible_observation_attributes(self, relevant_attributes):
        # all attributes are possible for every conversion component
        return relevant_attributes

    def get_possible_action_methods(self, relevant_methods):
        # all methods are possible for every conversion component
        return relevant_methods

    def _initialize_result_dictionaries(self):
        if self.consumed_commodities is None:
            self.consumed_commodities = {}
        if self.produced_commodities is None:
            self.produced_commodities = {}

        for commodity in self.commodities:
            if (
                commodity in [*self.inputs.keys()] and 
                commodity not in [*self.consumed_commodities.keys()]
            ):
                self.set_specific_consumed_commodities(commodity, 0)
            if (
                commodity in [*self.outputs.keys()] and 
                commodity not in [*self.produced_commodities.keys()]
            ):
                self.set_specific_produced_commodities(commodity, 0)

    def __copy__(self, name=None):
        if name is None:
            name = self.name
        # deepcopy mutable objects
        inputs = copy.deepcopy(self.inputs)
        outputs = copy.deepcopy(self.outputs)
        commodities = copy.deepcopy(self.commodities)
        return ConversionComponent(name=name, ramp_down=self.ramp_down, ramp_up=self.ramp_up,
                                   min_p=self.min_p, max_p=self.max_p, inputs=inputs, outputs=outputs,
                                   main_input=self.main_input, main_output=self.main_output, commodities=commodities,
                                   ixed_capacity=self.fixed_capacity, consumed_commodities=self.consumed_commodities, 
                                   produced_commodities=self.produced_commodities)


class StorageComponent(BaseComponent):
    
    def __init__(self, name, variable_om=0., charging_efficiency=1., discharging_efficiency=1., 
                 min_soc=0., max_soc=1., ratio_capacity_p=1., stored_commodity=None, 
                 charge_state=0., fixed_capacity=0., charged_quantity=0., discharged_quantity=0.):
        """
        Class of Storage component

        :param name: [string] - Abbreviation of unit
        :param variable_om: [float] - variable operation and maintenance
        :param charging_efficiency: [float] - Charging efficiency when charging storage
        :param discharging_efficiency: [float] - Charging efficiency when discharging storage
        :param min_soc: [float] - minimal SOC of storage
        :param max_soc: [float] - maximal SOC of storage
        :param ratio_capacity_p: [float] - Ratio between capacity of storage and charging or discharging power
        """

        super().__init__(name=name, variable_om=variable_om, fixed_capacity=fixed_capacity)

        self.component_type = 'storage'

        self.charging_efficiency = float(charging_efficiency)
        self.discharging_efficiency = float(discharging_efficiency)
        self.ratio_capacity_p = float(ratio_capacity_p)

        self.min_soc = float(min_soc)
        self.max_soc = float(max_soc)
        
        self.stored_commodity = stored_commodity
        self.charge_state = charge_state

        self.charged_quantity = charged_quantity
        self.discharged_quantity = discharged_quantity
    
    def charge_or_discharge_quantity(self, quantity, ptx_system):
        """Positive values mean charge, negative values mean discharge. Quantity is raw 
        storage input, not what is actually stored after applying efficiency coefficient."""
        if quantity == 0:
            return f"Cannot charge/discharge quantity 0 in {self.name}."
        
        commodity = ptx_system.commodities[self.stored_commodity]
        max_charge = self.fixed_capacity * self.max_soc
        min_charge = self.fixed_capacity * self.min_soc
        free_storage = max_charge - self.charge_state
        dischargeable_quantity = max(0, self.charge_state - min_charge)
        
        # for charging, it must be checked if there is enough available commodity to charge, 
        # if the storage has enough free capacity, and if the cost of charging isn't higher 
        # than the balance. If one of these three conditions is not fulfilled, the values 
        # have to be changed which in turn affects the other conditions which have to be 
        # evaluated again. An if-else structure would be too large to check for all three 
        # conditions in every branch. Therefore, three helper functions are used which call 
        # each other in a recursive way, until all conditions are met and the new values 
        # satisfying all conditions are returned. _handle_cost is always called last and 
        # returns the input quantity, charging quantity, as well as the charging cost.
        
        def _handle_available(_quantity, _actual_quantity, _status):
            if _quantity > commodity.available_quantity:
                new_quantity = commodity.available_quantity
                new_actual_quantity = new_quantity * self.charging_efficiency
                _status += (f"Quantity {_quantity} is greater than available quantity "
                            f"{commodity.available_quantity}, charge that much instead. ")
                if new_quantity > free_storage:
                    return _handle_capacity(new_quantity, new_actual_quantity, _status)
                return _handle_cost(new_quantity, new_actual_quantity, _status)
            return _handle_cost(_quantity, _actual_quantity, _status)
        
        def _handle_capacity(_quantity, _actual_quantity, _status):
            if _quantity > free_storage:
                new_actual_quantity = free_storage
                new_quantity = new_actual_quantity / self.charging_efficiency
                _status += (f"Quantity {_quantity} is greater than free storage "
                            f"capacity {free_storage}, charge that much instead. ")
                if new_quantity > commodity.available_quantity:
                    return _handle_available(new_quantity, new_actual_quantity, _status)
                return _handle_cost(new_quantity, new_actual_quantity, _status)
            return _handle_cost(_quantity, _actual_quantity, _status)
        
        def _handle_cost(_quantity, _actual_quantity, _status):
            cost = round(_quantity * self.variable_om, 4)
            if cost > ptx_system.balance:
                new_cost = ptx_system.balance
                new_quantity = new_cost / self.variable_om
                new_actual_quantity = new_quantity * self.charging_efficiency
                _status += (f"Charging cost {cost} is greater than balance {ptx_system.balance}, "
                            f"charge quantity {new_quantity} for that much instead. ")
                if new_quantity > free_storage:
                    return _handle_capacity(new_quantity, new_actual_quantity, _status)
                if new_quantity > commodity.available_quantity:
                    return _handle_available(new_quantity, new_actual_quantity, _status)
                return new_quantity, new_actual_quantity, new_cost
            return _quantity, _actual_quantity, cost, _status
        
        status = ""
        cost = 0
        # charge
        if quantity > 0:
            if self.charge_state >= max_charge:
                return f"Cannot charge quantity {quantity} in {self.name} as it is full."
            if commodity.available_quantity <= 0:
                return f"Cannot charge quantity {quantity} in {self.name} as none is available."
            
            actual_quantity = quantity * self.charging_efficiency
            # go through chained functions until all conditions are met and values are within bounds
            quantity, actual_quantity, cost, status = _handle_available(quantity, actual_quantity, status)
            if status == "":
                status = f"Charge {quantity} {commodity.name} for {cost} in {self.name}."
            else:
                status += f"Finally charge {quantity} {commodity.name} for {cost} in {self.name}."
            
            self.charged_quantity += actual_quantity
            commodity.charged_quantity += actual_quantity
        # discharge
        else: # quantity < 0
            discharge_quantity = -quantity
            if self.charge_state <= min_charge:
                return f"Cannot discharge quantity {discharge_quantity} in {self.name} as it is empty."
            
            # actual output should be specified quantity
            actual_quantity = discharge_quantity
            discharge_quantity = discharge_quantity / self.discharging_efficiency
            # try to discharge as much as possible
            if self.charge_state - discharge_quantity < min_charge:
                actual_quantity = dischargeable_quantity * self.discharging_efficiency
                status = (f"Cannot discharge quantity {discharge_quantity} in {self.name} "
                          f"from {dischargeable_quantity} {commodity.name} in storage. "
                          f"Instead, discharge that much.")
                discharge_quantity = dischargeable_quantity
            
            quantity = -discharge_quantity
            actual_quantity = -actual_quantity
            self.discharged_quantity += actual_quantity
            commodity.discharged_quantity += actual_quantity
        
        self.charge_state += actual_quantity
        self.total_variable_costs += cost
        commodity.available_quantity -= quantity
        commodity.total_storage_costs += cost
        ptx_system.balance -= cost
        return status

    def get_possible_observation_attributes(self, relevant_attributes):
        # all attributes are possible for every conversion component
        return relevant_attributes

    def get_possible_action_methods(self, relevant_methods):
        # all methods are possible for every conversion component
        return relevant_methods

    def __copy__(self):
        return StorageComponent(name=self.name, charging_efficiency=self.charging_efficiency,
                                discharging_efficiency=self.discharging_efficiency,
                                min_soc=self.min_soc, max_soc=self.max_soc,
                                ratio_capacity_p=self.ratio_capacity_p,
                                stored_commodity=self.stored_commodity,
                                fixed_capacity=self.fixed_capacity, 
                                charged_quantity=self.charged_quantity, 
                                discharged_quantity=self.discharged_quantity)


class GenerationComponent(BaseComponent):
    
    def __init__(self, name, variable_om=0., generated_commodity='Electricity', 
                 curtailment_possible=True, fixed_capacity=0.,
                 potential_generation_quantity=0., generated_quantity=0., curtailment=0.):
        """
        Class of Generator component

        :param name: [string] - Abbreviation of unit
        :param variable_om: [float] - variable operation and maintenance
        :param generated_commodity: [string] - Stream, which is generated by generator
        """
        
        super().__init__(name=name, variable_om=variable_om, fixed_capacity=fixed_capacity)

        self.component_type = 'generator'

        self.generated_commodity = generated_commodity
        self.curtailment_possible = bool(curtailment_possible)
        self.fixed_capacity = float(fixed_capacity)

        self.potential_generation_quantity = potential_generation_quantity
        self.generated_quantity = generated_quantity
        self.curtailment = curtailment

    def apply_or_strip_curtailment(self, quantity, ptx_system):
        """Change curtailment quantity and then generate as much as possible 
        of the commodity based on curtailment and the current weather."""
        if quantity == 0:
            return f"Cannot curtail quantity 0 in {self.name}."
        
        status = None
        # how much the generator is allowed to generate at most
        potential_max_generation = self.fixed_capacity - self.curtailment
        # how much the generator can actually generate at most
        possible_current_generation = (ptx_system.get_current_weather_coefficient(self.name)
                                       * self.fixed_capacity)
        # decrease production
        if quantity > 0:
            # try to curtail as much as possible, limit at stopping generation
            if quantity > potential_max_generation:
                generated = 0
                status = (f"Cannot curtail {quantity} from current capacity {potential_max_generation} "
                          f"in {self.name}. Instead, curtail completely, generating 0 MWh.")
                quantity = potential_max_generation
            else:
                new_potential_max_generation = potential_max_generation - quantity
                generated = min(possible_current_generation, new_potential_max_generation)
                status = (f"Curtail {quantity} from {potential_max_generation} current potential "
                          f"production, generating {generated} MWh in {self.name}.")
        # increase production
        else: # quantity < 0
            curtail_strip_quantity = -quantity
            # try to remove curtailment as much as possible, limit at max possible generation
            if curtail_strip_quantity > self.curtailment:
                generated = possible_current_generation
                status = (f"Cannot remove curtailment {curtail_strip_quantity} from current "
                          f"curtailment {self.curtailment} in {self.name}. Instead, remove "
                          f"curtailment completely, generating {generated} MWh.")
                quantity = -self.curtailment
            else:
                generated = possible_current_generation - self.curtailment + curtail_strip_quantity
                status = (f"Remove curtailment {curtail_strip_quantity} from {self.curtailment} "
                          f"curtailment, generating {generated} MWh in {self.name}.")
        
        self.generated_quantity += generated
        self.potential_generation_quantity += possible_current_generation
        self.curtailment += quantity
        cost = round(generated * self.variable_om, 4)
        self.total_variable_costs += cost
        commodity = ptx_system.commodities[self.generated_commodity]
        commodity.generated_quantity += generated
        commodity.total_generation_costs += cost
        ptx_system.balance -= cost
        return status

    def get_possible_observation_attributes(self, relevant_attributes):
        possible_attributes = []
        for attribute in relevant_attributes:
            if attribute == "curtailment" and self.curtailment_possible:
                possible_attributes.append(attribute)
        return possible_attributes

    def get_possible_action_methods(self, relevant_methods):
        possible_methods = []
        for method in relevant_methods:
            if method == GenerationComponent.apply_or_strip_curtailment and self.curtailment_possible:
                possible_methods.append(method)
        return possible_methods

    def __copy__(self):
        return GenerationComponent(name=self.name, generated_commodity=self.generated_commodity,
                                   curtailment_possible=self.curtailment_possible,
                                   fixed_capacity=self.fixed_capacity,
                                   potential_generation_quantity=self.potential_generation_quantity,
                                   generated_quantity=self.generated_quantity, curtailment=self.curtailment)

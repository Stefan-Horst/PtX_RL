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
                 min_p=0., max_p=1., load=0., inputs=None, outputs=None, 
                 main_input=None, main_output=None, commodities=None, fixed_capacity=0., 
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
        self.load = load

        self.consumed_commodities = consumed_commodities
        self.produced_commodities = produced_commodities
        
        self._initialize_result_dictionaries()
    
    def ramp_up_or_down(self, quantity, ptx_system):
        """Increase/decrease the current load and then convert that much of the main input plus 
        other inputs to the outputs of the conversion. If the load would be increased too much or 
        decreased too little so that the conversion would consume more inputs than available or the 
        cost would be higher than the available balance, it is attempted to reduce the load as much 
        as possible. If the conversion then still attempts to consume more inputs than available or 
        costs too much, the conversion fails completely.
        Positive quantity means ramp up, negative quantity means ramp down."""
        if quantity == 0:
            return f"Cannot ramp up/down 0 in {self.name}."
        
        main_input_conversion_coefficient = self.inputs[self.main_input]
        current_capacity = self.get_current_capacity_level()
        
        input_commodities = list(map(ptx_system.commodities.get, [list(self.inputs.keys())]))
        input_ratios = list(self.inputs.values())
        other_output_commodities = list(map(ptx_system.commodities.get, [list(self.outputs.keys())]))
        output_ratios = list(self.outputs.values())
        
        status = f"In {self.name}:"
        
        # set quantity so conversion cannot cost more than balance
        potential_max_cost = round(
            current_capacity * main_input_conversion_coefficient * self.variable_om, 4
        )
        if potential_max_cost > ptx_system.balance:
            new_capacity = ptx_system.balance / (main_input_conversion_coefficient * self.variable_om)
            new_load = new_capacity / self.fixed_capacity
            new_quantity = new_load - self.load
            status += (f" Potential cost is higher than balance, set "
                        f"quantity from {quantity} to {new_quantity}.")
            quantity = new_quantity
        
        # ramp up
        if quantity > 0:
            if quantity > self.ramp_up:
                status += (f" Quantity {quantity} is higher than max ramp up "
                           f"{self.ramp_up}, set quantity to that value.")
                quantity = self.ramp_up
                
            new_load = self.load + quantity    
            if new_load > self.max_p:
                new_quantity = self.max_p - self.load
                status += (f" New load {new_load} of quantity {quantity} is higher than max "
                           f"power, set load to that value with quantity {new_quantity}.")
                new_load = self.load + new_quantity
                quantity = new_quantity
            
            new_capacity = self.fixed_capacity * new_load
            # don't set production higher than available input quantities if possible
            for input, input_ratio in zip(input_commodities, input_ratios):
                if new_capacity * input_ratio > input.available_quantity:
                    adapted_capacity = min(input.available_quantity / input_ratio, current_capacity)
                    adapted_load = adapted_capacity / self.fixed_capacity
                    adapted_quantity = adapted_load - self.load
                    status += (f" Ramp up to {new_load} in {self.name} would use "
                               f"more {input.name} than available. Instead, ramp up "
                               f"quantity {adapted_quantity} to {adapted_load} load.")
                    new_capacity = adapted_capacity
                    new_load = adapted_load
                    quantity = adapted_quantity
            
            if status == "":
                status = f"Ramp up {quantity} quantity to {new_load} load."
        # ramp down
        else: # quantity < 0
            reduction_quantity = -quantity
            if reduction_quantity > self.ramp_down:
                status += (f" Quantity {reduction_quantity} is higher than max ramp "
                           f"down {self.ramp_down}, set quantity to that value.")
                reduction_quantity = self.ramp_down
            
            new_load = self.load - reduction_quantity
            if new_load < self.min_p:
                new_reduction_quantity = self.load - self.min_p
                status += (f" New load {new_load} of quantity {reduction_quantity} is lower than min "
                           f"power, set load to that value with quantity {new_reduction_quantity}.")
                new_load = self.load - reduction_quantity
                reduction_quantity = new_reduction_quantity
            
            new_capacity = self.fixed_capacity * new_load
            potential_min_capacity = min(self.load - self.ramp_down, self.min_p) * self.fixed_capacity
            # try to set production even lower if available input quantities are too low
            for input, input_ratio in zip(input_commodities, input_ratios):
                if new_capacity * input_ratio > input.available_quantity:
                    adapted_capacity = min(input.available_quantity / input_ratio, potential_min_capacity)
                    adapted_load = adapted_capacity / self.fixed_capacity
                    adapted_quantity = adapted_load - self.load
                    status += (f" Ramp down to {new_load} in {self.name} would use "
                               f"more {input.name} than available. Instead, ramp down "
                               f"quantity {adapted_quantity} to {adapted_load} load.")
                    new_capacity = adapted_capacity
                    new_load = adapted_load
                    reduction_quantity = adapted_quantity
            
            if status == "":
                status = f"Ramp down {reduction_quantity} quantity to {new_load} load."
            quantity = -reduction_quantity
        
        current_capacity = new_load * self.fixed_capacity
        # calculate and check cost
        cost = round(current_capacity * main_input_conversion_coefficient * self.variable_om, 4)
        if cost > ptx_system.balance:
            status += (f" Conversion failed. Cost {cost} is higher than "
                       f"available balance {ptx_system.balance}.")
            return status, False # false as failure flag
        
        # convert commodities
        convert_status = ""
        for input, input_ratio in zip(input_commodities, input_ratios):
            amount = input_ratio * current_capacity
            # failure if not enough commodity for conversion available
            if amount > input.available_quantity:
                status += (f" Conversion failed for {self.name}. {amount} {input.name} "
                           f"required, but only {input.available_quantity} available.")
                return status, False # false as failure flag
            
            input.available_quantity -= amount
            input.consumed_quantity += amount
            if input.name == self.main_input:
                input.total_prodution_costs += cost
            self.consumed_commodities[input.name] += amount
            convert_status += f" {amount} {input.name} consumed in conversion."
        for output, output_ratio in zip(other_output_commodities, output_ratios):
            amount = output_ratio * current_capacity
            output.available_quantity += amount
            output.produced_quantity += amount
            self.produced_commodities[output.name] += amount
            convert_status += f" {amount} {output.name} produced in conversion."
        status += convert_status
        
        self.load += quantity
        self.total_variable_costs += cost
        ptx_system.balance -= cost
        return status, True # true as conversion success flag

    def get_current_capacity_level(self):
        return self.load * self.fixed_capacity

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
        """Charge/discharge quantity or as much as possible based on available commodity 
        and current state of charge as well as the available balance. 
        Positive values mean charge, negative values mean discharge. Quantity is raw storage 
        input, not what is actually stored after applying efficiency coefficient."""
        if quantity == 0:
            return f"Cannot charge/discharge quantity 0 in {self.name}."
        
        commodity = ptx_system.commodities[self.stored_commodity]
        max_charge = self.fixed_capacity * self.max_soc
        min_charge = self.fixed_capacity * self.min_soc
        free_storage = max_charge - self.charge_state
        dischargeable_quantity = max(0, self.charge_state - min_charge)
        
        status = ""
        # charge
        if quantity > 0:
            if self.charge_state >= max_charge:
                return f"Cannot charge quantity {quantity} in {self.name} as it is full."
            if commodity.available_quantity <= 0:
                return f"Cannot charge quantity {quantity} in {self.name} as none is available."
            
            # while quantity is raw input used, actual_quantity is what is actually stored
            actual_quantity = quantity * self.charging_efficiency
            if actual_quantity > free_storage:
                new_actual_quantity = free_storage
                quantity = new_actual_quantity / self.charging_efficiency
                status += (f"Quantity to be stored {actual_quantity} is greater than free "
                           f"storage capacity {free_storage}, charge {quantity} instead. ")
                actual_quantity = new_actual_quantity
            
            if quantity > commodity.available_quantity:
                new_quantity = commodity.available_quantity
                actual_quantity = new_quantity * self.charging_efficiency
                status += (f"Quantity {quantity} is greater than available quantity "
                           f"{commodity.available_quantity}, charge that much instead. ")
                quantity = new_quantity
            
            cost = round(quantity * self.variable_om, 4)
            if cost > ptx_system.balance:
                new_cost = ptx_system.balance
                quantity = new_cost / self.variable_om
                actual_quantity = quantity * self.charging_efficiency
                status += (f"Charging cost {cost} is greater than balance {ptx_system.balance}, "
                           f"charge quantity {quantity} for that much instead. ")
                cost = new_cost
            
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
            cost = .0 # discharging has no cost
        
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

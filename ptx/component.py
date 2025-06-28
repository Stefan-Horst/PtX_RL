import copy


class Component:
    
    def __init__(self, name, variable_om, has_fixed_capacity=False, 
                 fixed_capacity=0., total_variable_costs=0.):
        """
        Defines basic component class

        :param name: [string] - abbreviation of component
        :param variable_om: [float] - variable operation and maintenance
        """
        
        self.name = str(name)
        self.component_type = None

        self.variable_om = float(variable_om)

        self.has_fixed_capacity = bool(has_fixed_capacity)
        self.fixed_capacity = float(fixed_capacity)

        self.total_variable_costs = float(total_variable_costs)

    def __copy__(self):
        return Component(name=self.name, variable_om=self.variable_om,
                         has_fixed_capacity=self.has_fixed_capacity, 
                         fixed_capacity=self.fixed_capacity,
                         total_variable_costs=self.total_variable_costs)


class ConversionComponent(Component):
    
    def __init__(self, name, variable_om=0., ramp_down=1., ramp_up=1., start_up_time=0., 
                 start_up_costs=0, hot_standby_ability=False, hot_standby_demand=None, 
                 hot_standby_startup_time=0, min_p=0., max_p=1., inputs=None, outputs=None, 
                 main_input=None, main_output=None, commodities=None, has_fixed_capacity=False, 
                 fixed_capacity=0., consumed_commodity=None, produced_commodity=None, 
                 standby_quantity=0., total_startup_costs=0.):
        """
        Class of conversion units
        
        :param name: [string] - Abbreviation of unit
        :param variable_om: [float] - variable operation and maintenance
        :param ramp_down: [float] - Ramp down between time steps in % / h
        :param ramp_up: [float] - Ramp up between time steps in % / h
        :param start_up_time: [int] - Time to start up component
        :param inputs: [Dict] - inputs of component
        :param outputs: [Dict] - outputs of component
        :param main_input: [str] - main input of component
        :param main_output: [str] - main output of component
        :param min_p: [float] - Minimal power of the unit when operating
        :param max_p: [float] - Maximal power of the unit when operating
        :param commodities: [list] - Commodities of the unit
        """

        super().__init__(name=name, variable_om=variable_om,
                         has_fixed_capacity=has_fixed_capacity, fixed_capacity=fixed_capacity)

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

        self.start_up_time = int(start_up_time)
        self.start_up_costs = float(start_up_costs)

        self.hot_standby_ability = bool(hot_standby_ability)
        if hot_standby_demand is None:
            self.hot_standby_demand = {}
        else:
            self.hot_standby_demand = hot_standby_demand
        self.hot_standby_startup_time = int(hot_standby_startup_time)

        self.consumed_commodity = consumed_commodity
        self.produced_commodity = produced_commodity
        self.standby_quantity = standby_quantity

        self.total_startup_costs = total_startup_costs
        
        self.initialize_result_dictionaries()

    def initialize_result_dictionaries(self):
        if self.consumed_commodity is None:
            self.consumed_commodity = {}
        if self.produced_commodity is None:
            self.produced_commodity = {}

        for commodity in self.commodities:
            if commodity not in [*self.consumed_commodity.keys()]:
                self.set_specific_consumed_commodity(commodity, 0)
            if commodity not in [*self.produced_commodity.keys()]:
                self.set_specific_produced_commodity(commodity, 0)

    def set_hot_standby_demand(self, commodity, demand=None):
        if demand is not None:
            hot_standby_demand = {commodity: demand}
            self.hot_standby_demand.clear()
            self.hot_standby_demand = hot_standby_demand
        else:
            self.hot_standby_demand = commodity

    def add_input(self, input_commodity, coefficient):
        self.inputs.update({input_commodity: float(coefficient)})
        self.add_commodity(input_commodity)
        self.initialize_result_dictionaries()

    def remove_input(self, input_commodity):
        self.inputs.pop(input_commodity)
        self.remove_commodity(input_commodity)
        self.initialize_result_dictionaries()

    def add_output(self, output_commodity, coefficient):
        self.outputs.update({output_commodity: float(coefficient)})
        self.add_commodity(output_commodity)
        self.initialize_result_dictionaries()

    def remove_output(self, output_commodity):
        self.outputs.pop(output_commodity)
        self.remove_commodity(output_commodity)
        self.initialize_result_dictionaries()

    def add_commodity(self, commodity):
        if commodity not in self.commodities:
            self.commodities.append(commodity)

    def remove_commodity(self, commodity):
        if commodity in self.commodities:
            self.commodities.remove(commodity)

    def set_specific_consumed_commodity(self, commodity, quantity):
        self.consumed_commodity.update({commodity: quantity})

    def get_specific_consumed_commodity(self, commodity):
        if commodity not in self.commodities:
            return 0
        else:
            return self.consumed_commodity[commodity]

    def set_specific_produced_commodity(self, commodity, quantity):
        self.produced_commodity.update({commodity: quantity})

    def get_specific_produced_commodity(self, commodity):
        if commodity not in self.commodities:
            return 0
        else:
            return self.produced_commodity[commodity]

    def get_total_costs(self):
        return self.total_variable_costs + self.total_startup_costs

    def __copy__(self, name=None):
        if name is None:
            name = self.name
        # deepcopy mutable objects
        inputs = copy.deepcopy(self.inputs)
        outputs = copy.deepcopy(self.outputs)
        commodities = copy.deepcopy(self.commodities)
        hot_standby_demand = copy.deepcopy(self.hot_standby_demand)
        return ConversionComponent(name=name, ramp_down=self.ramp_down, ramp_up=self.ramp_up,
                                   start_up_time=self.start_up_time, hot_standby_ability=self.hot_standby_ability,
                                   hot_standby_demand=hot_standby_demand,
                                   hot_standby_startup_time=self.hot_standby_startup_time,
                                   min_p=self.min_p, max_p=self.max_p, inputs=inputs, outputs=outputs,
                                   main_input=self.main_input, main_output=self.main_output, commodities=commodities,
                                   has_fixed_capacity=self.has_fixed_capacity, fixed_capacity=self.fixed_capacity,
                                   consumed_commodity=self.consumed_commodity,
                                   produced_commodity=self.produced_commodity, standby_quantity=self.standby_quantity,
                                   total_startup_costs=self.total_startup_costs)


class StorageComponent(Component):
    
    def __init__(self, name, variable_om=0., charging_efficiency=1., discharging_efficiency=1., 
                 min_soc=0., max_soc=1., ratio_capacity_p=1., has_fixed_capacity=False, 
                 fixed_capacity=0., charged_quantity=0., discharged_quantity=0.):
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

        super().__init__(name=name, variable_om=variable_om,
                         has_fixed_capacity=has_fixed_capacity, 
                         fixed_capacity=fixed_capacity)

        self.component_type = 'storage'

        self.charging_efficiency = float(charging_efficiency)
        self.discharging_efficiency = float(discharging_efficiency)
        self.ratio_capacity_p = float(ratio_capacity_p)

        self.min_soc = float(min_soc)
        self.max_soc = float(max_soc)

        self.charged_quantity = charged_quantity
        self.discharged_quantity = discharged_quantity

    def get_total_costs(self):
        return self.total_variable_costs

    def __copy__(self):
        return StorageComponent(name=self.name, charging_efficiency=self.charging_efficiency,
                                discharging_efficiency=self.discharging_efficiency,
                                min_soc=self.min_soc, max_soc=self.max_soc,
                                ratio_capacity_p=self.ratio_capacity_p,
                                has_fixed_capacity=self.has_fixed_capacity, fixed_capacity=self.fixed_capacity,
                                charged_quantity=self.charged_quantity, discharged_quantity=self.discharged_quantity)


class GenerationComponent(Component):
    
    def __init__(self, name, variable_om=0., generated_commodity='Electricity', 
                 curtailment_possible=True, has_fixed_capacity=False, fixed_capacity=0.,
                 potential_generation_quantity=0., potential_capacity_factor=0., potential_lcoe=0.,
                 generated_quantity=0., actual_capacity_factor=0., actual_lcoe=0., curtailment=0.):
        """
        Class of Generator component

        :param name: [string] - Abbreviation of unit
        :param variable_om: [float] - variable operation and maintenance
        :param generated_commodity: [string] - Stream, which is generated by generator
        """
        
        super().__init__(name=name, variable_om=variable_om,
                         has_fixed_capacity=has_fixed_capacity, 
                         fixed_capacity=fixed_capacity)

        self.component_type = 'generator'

        self.generated_commodity = generated_commodity
        self.curtailment_possible = bool(curtailment_possible)
        self.has_fixed_capacity = bool(has_fixed_capacity)
        self.fixed_capacity = float(fixed_capacity)

        self.potential_generation_quantity = potential_generation_quantity
        self.potential_capacity_factor = potential_capacity_factor
        self.potential_lcoe = potential_lcoe
        self.generated_quantity = generated_quantity
        self.actual_capacity_factor = actual_capacity_factor
        self.actual_lcoe = actual_lcoe
        self.curtailment = curtailment

    def get_total_costs(self):
        return self.total_variable_costs

    def __copy__(self):
        return GenerationComponent(name=self.name, generated_commodity=self.generated_commodity,
                                   curtailment_possible=self.curtailment_possible,
                                   has_fixed_capacity=self.has_fixed_capacity, fixed_capacity=self.fixed_capacity,
                                   potential_generation_quantity=self.potential_generation_quantity,
                                   potential_capacity_factor=self.potential_capacity_factor,
                                   potential_lcoe=self.potential_lcoe, generated_quantity=self.generated_quantity,
                                   actual_capacity_factor=self.actual_capacity_factor, 
                                   actual_lcoe=self.actual_lcoe, curtailment=self.curtailment)

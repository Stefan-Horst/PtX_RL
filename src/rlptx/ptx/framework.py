import copy
from copy import deepcopy


class PtxSystem:
    
    def __init__(self, project_name='', starting_budget=0, weather_provider=None, 
                 current_step=0, commodities=None, components=None):
        """
        Object which stores all components, commodities, settings, etc.
        
        :param project_name: [string] - name of PtxSystem
        :param commodities: [dict] - Dictionary with abbreviations as keys and commodity objects as values
        :param components: [dict] - Dictionary with abbreviations as keys and component objects as values
        """
        
        self.project_name = project_name
        
        # keep track of all costs and revenues here
        self.starting_budget = starting_budget
        self.set_initial_balance(starting_budget)

        self.current_step = current_step
        
        self.weather_provider = weather_provider

        if commodities is None:
            commodities = {}
        if components is None:
            components = {}
        self.commodities = commodities
        self.components = components
    
    def set_initial_balance(self, balance):
        self.balance = balance
        self.starting_budget = balance
    
    def next_step(self):
        """Go to the next step and return the change in balance since the last step."""
        self.current_step += 1
        old_balance = self.previous_balance
        self.previous_balance = self.balance
        return self.balance - old_balance
    
    def get_current_weather_coefficient(self, source_name):
        weather_data = self.weather_provider.get_weather_of_tick(self.current_step)
        weather_of_source = weather_data[source_name]
        return weather_of_source
    
    def get_component_variable_om_parameters(self):
        variable_om = {}
        for component_object in self.get_all_components():
            component_name = component_object.name
            variable_om[component_name] = component_object.variable_om
        return variable_om

    def get_component_minimal_power_parameters(self):
        min_p_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.name
            min_p_dict[component_name] = component_object.min_p
        return min_p_dict

    def get_component_maximal_power_parameters(self):
        max_p_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.name
            max_p_dict[component_name] = component_object.max_p
        return max_p_dict

    def get_component_ramp_up_parameters(self):
        ramp_up_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.name
            ramp_up_dict[component_name] = component_object.ramp_up
        return ramp_up_dict

    def get_component_ramp_down_parameters(self):
        ramp_down_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.name
            ramp_down_dict[component_name] = component_object.ramp_down
        return ramp_down_dict

    def get_storage_component_charging_efficiency(self):
        charging_efficiency_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.name
            charging_efficiency_dict[component_name] = component_object.charging_efficiency
        return charging_efficiency_dict

    def get_storage_component_discharging_efficiency(self):
        discharging_efficiency_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.name
            discharging_efficiency_dict[component_name] = component_object.discharging_efficiency
        return discharging_efficiency_dict

    def get_storage_component_minimal_soc(self):
        min_soc_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.name
            min_soc_dict[component_name] = component_object.min_soc
        return min_soc_dict

    def get_storage_component_maximal_soc(self):
        max_soc_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.name
            max_soc_dict[component_name] = component_object.max_soc
        return max_soc_dict

    def get_storage_component_ratio_capacity_power(self):
        ratio_capacity_power_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.name
            ratio_capacity_power_dict[component_name] = component_object.ratio_capacity_p
        return ratio_capacity_power_dict

    def get_fixed_capacities(self):
        fixed_capacities_dict = {}
        for component_object in self.get_all_components():
            component_name = component_object.name
            fixed_capacities_dict[component_name] = component_object.fixed_capacity
        return fixed_capacities_dict

    def get_all_technical_component_parameters(self):
        variable_om_dict = self.get_component_variable_om_parameters()
        minimal_power_dict = self.get_component_minimal_power_parameters()
        maximal_power_dict = self.get_component_maximal_power_parameters()
        ramp_up_dict = self.get_component_ramp_up_parameters()
        ramp_down_dict = self.get_component_ramp_down_parameters()
        charging_efficiency_dict = self.get_storage_component_charging_efficiency()
        discharging_efficiency_dict = self.get_storage_component_discharging_efficiency()
        minimal_soc_dict = self.get_storage_component_minimal_soc()
        maximal_soc_dict = self.get_storage_component_maximal_soc()
        ratio_capacity_power_dict = self.get_storage_component_ratio_capacity_power()
        fixed_capacity_dict = self.get_fixed_capacities()

        return (variable_om_dict, minimal_power_dict, maximal_power_dict, ramp_up_dict, 
                ramp_down_dict, charging_efficiency_dict, discharging_efficiency_dict, 
                minimal_soc_dict, maximal_soc_dict, ratio_capacity_power_dict, fixed_capacity_dict)

    def get_commodity_sets(self):
        commodities = []
        available_commodities = []
        emittable_commodities = []
        purchasable_commodities = []
        saleable_commodities = []
        demanded_commodities = []
        total_demand_commodities = []

        for commodity in self.commodities:
            commodity_name = commodity.name
            commodities.append(commodity_name)
            if commodity.available:
                available_commodities.append(commodity_name)
            if commodity.emittable:
                emittable_commodities.append(commodity_name)
            if commodity.purchasable:
                purchasable_commodities.append(commodity_name)
            if commodity.saleable:
                saleable_commodities.append(commodity_name)
            if commodity.demanded:
                demanded_commodities.append(commodity_name)
                if commodity.is_total_demand:
                    total_demand_commodities.append(commodity_name)

        generated_commodities = []
        for generator in self.get_generator_components_objects():
            if generator.generated_commodity not in generated_commodities:
                generated_commodities.append(generator.generated_commodity)

        all_inputs = []
        all_outputs = []
        for component in self.get_conversion_components_objects():
            inputs = component.inputs
            outputs = component.outputs
            for i in inputs:
                if i not in all_inputs:
                    all_inputs.append(i)
            for o in outputs:
                if o not in all_outputs:
                    all_outputs.append(o)

        return (commodities, available_commodities, emittable_commodities, purchasable_commodities, 
                saleable_commodities, demanded_commodities, total_demand_commodities, 
                generated_commodities, all_inputs, all_outputs)

    def get_main_input_to_input_conversions(self):
        # main input to other inputs
        input_tuples = []
        main_input_to_input_conversion_tuples = []
        main_input_to_input_conversion_tuples_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.name
            inputs = component_object.inputs
            main_input = component_object.main_input
            for current_input in [*inputs.keys()]:
                input_tuples.append((component_name, current_input))
                if current_input != main_input:
                    main_input_to_input_conversion_tuples.append(
                        (component_name, main_input, current_input)
                    )
                    main_input_to_input_conversion_tuples_dict.update(
                        {(component_name, main_input, current_input): 
                            float(inputs[current_input]) / float(inputs[main_input])}
                    )
        return (input_tuples, main_input_to_input_conversion_tuples, 
                main_input_to_input_conversion_tuples_dict)

    def get_main_input_to_output_conversions(self):
        output_tuples = []
        main_input_to_output_conversion_tuples = []
        main_input_to_output_conversion_tuples_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.name
            inputs = component_object.inputs
            outputs = component_object.outputs
            main_input = component_object.main_input
            for current_output in [*outputs.keys()]:
                main_input_to_output_conversion_tuples.append(
                    (component_name, main_input, current_output)
                )
                main_input_to_output_conversion_tuples_dict.update(
                    {(component_name, main_input, current_output): 
                        float(outputs[current_output]) / float(inputs[main_input])}
                )
                output_tuples.append((component_name, current_output))
        return (output_tuples, main_input_to_output_conversion_tuples, 
                main_input_to_output_conversion_tuples_dict)

    def get_all_conversions(self):
        input_tuples, main_input_to_input_conversion_tuples, main_input_to_input_conversion_tuples_dict \
            = self.get_main_input_to_input_conversions()
        output_tuples, input_to_output_conversion_tuples, input_to_output_conversion_tuples_dict \
            = self.get_main_input_to_output_conversions()
        return (input_tuples, main_input_to_input_conversion_tuples, 
                main_input_to_input_conversion_tuples_dict, output_tuples, 
                input_to_output_conversion_tuples, input_to_output_conversion_tuples_dict)

    def get_conversion_components_names(self):
        conversion_components_names = []
        for c in self.get_all_component_names():
            if self.components[c].component_type == 'conversion':
                conversion_components_names.append(self.components[c].name)
        return conversion_components_names

    def get_conversion_components_objects(self):
        conversion_components_objects = []
        for c in self.get_all_component_names():
            if self.components[c].component_type == 'conversion':
                conversion_components_objects.append(self.components[c])
        return conversion_components_objects

    def get_storage_components_names(self):
        storage_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.components[c].component_type == 'storage':
                storage_components_names.append(self.components[c].name)
        return storage_components_names

    def get_storage_components_objects(self):
        storage_components_objects = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.components[c].component_type == 'storage':
                storage_components_objects.append(self.components[c])
        return storage_components_objects

    def get_generator_components_names(self):
        generator_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.components[c].component_type == 'generator':
                generator_components_names.append(self.components[c].name)
        return generator_components_names

    def get_generator_components_objects(self):
        generator_components_objects = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.components[c].component_type == 'generator':
                generator_components_objects.append(self.components[c])
        return generator_components_objects

    def adjust_commodity(self, name, commodity_object):
        components = self.get_component_by_commodity(name)
        for c in components:
            inputs = self.components[c].inputs
            inputs[commodity_object.name] = inputs.pop(name)
            self.components[c].inputs = inputs

            if name == self.components[c].main_input:
                self.components[c].main_input = commodity_object.name

            outputs = self.components[c].outputs
            outputs[commodity_object.name] = outputs.pop(name)
            self.components[c].outputs = outputs

            if name == self.components[c].main_output:
                self.components[c].main_output = commodity_object.name

        for g in self.get_generator_components_objects():
            if g.generated_commodity == name:
                g.generated_commodity = commodity_object.name

        for s in self.get_storage_components_objects():
            if s.name == name:
                new_storage = deepcopy(s)
                new_storage.name = commodity_object.name
                self.remove_component_entirely(name)
                self.add_component(commodity_object.name, new_storage)

        self.add_commodity(commodity_object.name, commodity_object)

    def add_component(self, name, component):
        self.components.update({name: component})

    def get_all_component_names(self):
        return [*self.components.keys()]

    def get_all_components(self):
        components = []
        for c in self.get_all_component_names():
            components.append(self.components[c])
        return components

    def remove_component_entirely(self, name):
        self.components.pop(name)

    def add_commodity(self, name, commodity):
        self.commodities.update({name: commodity})

    def remove_commodity_entirely(self, name):
        self.commodities.pop(name)

    def get_all_commodity_names(self):
        return [*self.commodities.keys()]
    
    def get_all_commodities(self):
        commodities = []
        for c in self.get_all_commodity_names():
            commodities.append(self.commodities[c])
        return commodities

    def get_commodities_by_component(self, component):
        return self.components[component].commodities

    def get_components_by_commodity(self, commodity):
        components = []
        for c in self.components:
            if self.components[c].component_type == 'conversion':
                if commodity in self.get_commodity_by_component(c):
                    components.append(c)
        return components

    def __str__(self):
        if self.weather_provider is not None:
            weather_data = self.weather_provider.get_weather_of_tick(self.current_step).to_dict()
            weather = "{" + ", ".join([
                                        f'{k}={v:{".4f" if isinstance(v, float) else ""}}' 
                                        for k, v in weather_data.items()
                                      ]) + "}"
        else:
            weather = "None"
        commodities = "; ".join([str(commodity) for commodity in self.commodities.values()])
        components_ordered = (self.get_generator_components_objects() 
                              + self.get_storage_components_objects() 
                              + self.get_conversion_components_objects())
        components = "; ".join([str(component) for component in components_ordered])
        return (f"PtxSystem: step={self.current_step}, balance={self.balance:.4f}, weather: {weather}\n"
                f"\tcommodities: {commodities},\n\tcomponents: {components}")

    def __repr__(self):
        return (f"PtxSystem(project_name={self.project_name!r}, starting_budget={self.starting_budget!r}, "
                f"weather_provider={self.weather_provider!r}, current_step={self.current_step!r}, "
                f"balance={self.balance!r}, previous_balance={self.previous_balance!r}, "
                f"commodities={self.commodities!r}, components={self.components!r})")

    def __copy__(self):
        # deepcopy mutable objects
        components = copy.deepcopy(self.components)
        commodities = copy.deepcopy(self.commodities)
        return PtxSystem(project_name=self.project_name, starting_budget=self.starting_budget, 
                         weather_provider=self.weather_provider, current_step=self.current_step, 
                         commodities=commodities, components=components)

import copy
from copy import deepcopy
import pandas as pd

from ptx.component import ConversionComponent
from ptx.commodity import Commodity


idx = pd.IndexSlice


class ParameterObject:
    
    def __init__(self, project_name='', integer_steps=5, facility_lifetime=20,
                 names_dict=None, commodities=None, components=None,
                 profile_data=False, single_or_multiple_profiles='single',
                 uses_representative_periods=False, representative_periods_length=0,
                 covered_period=8760, monetary_unit='€', path_data=None,
                 instance=None, operation_time_series=None,
                 copy_object=False):
        """
        Object, which stores all components, commodities, settings etc.
        
        :param project_name: [string] - name of parameter object
        :param integer_steps: [int] - number of integer steps (used to split capacity)
        :param names_dict: [dict] - List of abbreviations of components, commodities etc.
        :param commodities: [dict] - Dictionary with abbreviations as keys and commodity objects as values
        :param components: [dict] - Dictionary with abbreviations as keys and component objects as values
        :param copy_object: [boolean] - Boolean if object is copy
        """
        
        self.project_name = project_name

        if not copy_object:
            # Initiate as default values
            self.facility_lifetime = facility_lifetime

            self.names_dict = {}

            self.commodities = {}
            self.components = {}
        else:
            # Object is copied if components have parallel units.
            # It is copied so that the original pm_object is not changed
            self.names_dict = names_dict

            self.commodities = commodities
            self.components = components

        self.covered_period = covered_period
        self.uses_representative_periods = uses_representative_periods
        self.representative_periods_length = representative_periods_length
        self.integer_steps = integer_steps
        self.monetary_unit = str(monetary_unit)

        self.single_or_multiple_profiles = single_or_multiple_profiles
        self.profile_data = profile_data
        self.path_data = path_data

        self.instance = instance
        self.operation_time_series = operation_time_series

        self.objective_function_value = None

    def create_new_project(self):
        """ Create new project """
        # Set general parameters
        c = 'dummy'
        conversion_component = ConversionComponent(name=c, final_unit=True)
        self.add_component(c, conversion_component)

        input_commodity = 'Electricity'
        output_commodity = 'Electricity'

        self.get_component(c).add_input(input_commodity, 1)
        self.get_component(c).add_output(output_commodity, 1)

        self.get_component(c).set_main_input(input_commodity)
        self.get_component(c).set_main_output(output_commodity)

        s = Commodity('Electricity', 'MWh', final_commodity=True)
        self.add_commodity('Electricity', s)

    def get_number_clusters(self):
        if self.get_uses_representative_periods():
            path = self.get_path_data() + self.get_profile_data()
            if path.split('.')[-1] == 'xlsx':
                generation_profile = pd.read_excel(path, index_col=0)
            else:
                generation_profile = pd.read_csv(path, index_col=0)

            if self.get_uses_representative_periods():
                return int(len(generation_profile.index) / self.get_covered_period())
            else:
                return 1
        else:
            return 1

    def get_component_variable_om_parameters(self):
        variable_om = {}
        for component_object in self.get_all_components():
            component_name = component_object.get_name()
            variable_om[component_name] = component_object.get_variable_OM()
        return variable_om

    def get_component_minimal_power_parameters(self):
        min_p_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.get_name()
            min_p_dict[component_name] = component_object.get_min_p()
        return min_p_dict

    def get_component_maximal_power_parameters(self):
        max_p_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.get_name()
            max_p_dict[component_name] = component_object.get_max_p()
        return max_p_dict

    def get_component_ramp_up_parameters(self):
        ramp_up_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.get_name()
            ramp_up_dict[component_name] = component_object.get_ramp_up()
        return ramp_up_dict

    def get_component_ramp_down_parameters(self):
        ramp_down_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.get_name()
            ramp_down_dict[component_name] = component_object.get_ramp_down()
        return ramp_down_dict

    def get_shut_down_component_down_time_parameters(self):
        down_time_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.get_name()
            if int(component_object.get_start_up_time()) == 0:
                # shut down time of 0 is not possible (division). Therefore, set it to 1
                down_time_dict[component_name] = 1
            else:
                down_time_dict[component_name] = int(component_object.get_start_up_time())
        return down_time_dict

    def get_shut_down_component_start_up_costs_parameters(self):
        start_up_costs_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.get_name()
            start_up_costs_dict[component_name] = component_object.get_start_up_costs()
        return start_up_costs_dict

    def get_standby_component_down_time_parameters(self):
        standby_time_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.get_name()
            if component_object.get_hot_standby_ability():
                if int(component_object.get_hot_standby_startup_time()) == 0:
                    # shut down time of 0 is not possible (division). Therefore, set it to 1
                    standby_time_dict[component_name] = 1
                else:
                    standby_time_dict[component_name] = int(component_object.get_hot_standby_startup_time())
        return standby_time_dict

    def get_storage_component_charging_efficiency(self):
        charging_efficiency_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.get_name()
            charging_efficiency_dict[component_name] = component_object.get_charging_efficiency()
        return charging_efficiency_dict

    def get_storage_component_discharging_efficiency(self):
        discharging_efficiency_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.get_name()
            discharging_efficiency_dict[component_name] = component_object.get_discharging_efficiency()
        return discharging_efficiency_dict

    def get_storage_component_minimal_soc(self):
        min_soc_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.get_name()
            min_soc_dict[component_name] = component_object.get_min_soc()
        return min_soc_dict

    def get_storage_component_maximal_soc(self):
        max_soc_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.get_name()
            max_soc_dict[component_name] = component_object.get_max_soc()
        return max_soc_dict

    def get_storage_component_ratio_capacity_power(self):
        ratio_capacity_power_dict = {}
        for component_object in self.get_storage_components_objects():
            component_name = component_object.get_name()
            ratio_capacity_power_dict[component_name] = component_object.get_ratio_capacity_p()
        return ratio_capacity_power_dict

    def get_fixed_capacities(self):
        fixed_capacities_dict = {}
        for component_object in self.get_all_components():
            component_name = component_object.get_name()
            fixed_capacities_dict[component_name] = component_object.get_fixed_capacity()
        return fixed_capacities_dict

    def get_all_technical_component_parameters(self):
        variable_om_dict = self.get_component_variable_om_parameters()
        minimal_power_dict = self.get_component_minimal_power_parameters()
        maximal_power_dict = self.get_component_maximal_power_parameters()
        ramp_up_dict = self.get_component_ramp_up_parameters()
        ramp_down_dict = self.get_component_ramp_down_parameters()
        shut_down_down_time_dict = self.get_shut_down_component_down_time_parameters()
        shut_down_start_up_costs = self.get_shut_down_component_start_up_costs_parameters()
        standby_down_time_dict = self.get_standby_component_down_time_parameters()
        charging_efficiency_dict = self.get_storage_component_charging_efficiency()
        discharging_efficiency_dict = self.get_storage_component_discharging_efficiency()
        minimal_soc_dict = self.get_storage_component_minimal_soc()
        maximal_soc_dict = self.get_storage_component_maximal_soc()
        ratio_capacity_power_dict = self.get_storage_component_ratio_capacity_power()
        fixed_capacity_dict = self.get_fixed_capacities()

        return variable_om_dict, minimal_power_dict, maximal_power_dict,\
            ramp_up_dict, ramp_down_dict, shut_down_down_time_dict, shut_down_start_up_costs, \
            standby_down_time_dict, charging_efficiency_dict, discharging_efficiency_dict, \
            minimal_soc_dict, maximal_soc_dict, ratio_capacity_power_dict, fixed_capacity_dict

    def get_all_financial_component_parameters(self):
        variable_om_dict = self.get_component_variable_om_parameters()
        return variable_om_dict

    def get_conversion_component_sub_sets(self):
        standby_components = []
        no_standby_components = []
        for component_object in self.get_all_components():
            component_name = component_object.get_name()
            if component_object.get_component_type() == 'conversion':
                if component_object.get_hot_standby_ability():
                    standby_components.append(component_name)
                else:
                    no_standby_components.append(component_name)
        return standby_components, no_standby_components

    def get_commodity_sets(self):
        commodities = []
        available_commodities = []
        emittable_commodities = []
        purchasable_commodities = []
        saleable_commodities = []
        demanded_commodities = []
        total_demand_commodities = []

        for commodity in self.get_all_commodities():
            commodity_name = commodity.get_name()
            commodities.append(commodity_name)
            if commodity.is_available():
                available_commodities.append(commodity_name)
            if commodity.is_emittable():
                emittable_commodities.append(commodity_name)
            if commodity.is_purchasable():
                purchasable_commodities.append(commodity_name)
            if commodity.is_saleable():
                saleable_commodities.append(commodity_name)
            if commodity.is_demanded():
                demanded_commodities.append(commodity_name)
                if commodity.is_total_demand():
                    total_demand_commodities.append(commodity_name)

        generated_commodities = []
        for generator in self.get_generator_components_objects():
            if generator.get_generated_commodity() not in generated_commodities:
                generated_commodities.append(generator.get_generated_commodity())

        all_inputs = []
        all_outputs = []
        for component in self.get_conversion_components_objects():
            inputs = component.get_inputs()
            outputs = component.get_outputs()
            for i in inputs:
                if i not in all_inputs:
                    all_inputs.append(i)
            for o in outputs:
                if o not in all_outputs:
                    all_outputs.append(o)

        return commodities, available_commodities, emittable_commodities, purchasable_commodities, \
            saleable_commodities, demanded_commodities, total_demand_commodities, generated_commodities, \
            all_inputs, all_outputs

    def get_main_input_to_input_conversions(self):
        # main input to other inputs
        input_tuples = []
        main_input_to_input_conversion_tuples = []
        main_input_to_input_conversion_tuples_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.get_name()
            inputs = component_object.get_inputs()
            main_input = component_object.get_main_input()
            for current_input in [*inputs.keys()]:
                input_tuples.append((component_name, current_input))
                if current_input != main_input:
                    main_input_to_input_conversion_tuples.append((component_name, main_input, current_input))
                    main_input_to_input_conversion_tuples_dict.update(
                        {(component_name, main_input, current_input): float(inputs[current_input]) / float(inputs[main_input])})
        return input_tuples, main_input_to_input_conversion_tuples, main_input_to_input_conversion_tuples_dict

    def get_main_input_to_output_conversions(self):
        output_tuples = []
        main_input_to_output_conversion_tuples = []
        main_input_to_output_conversion_tuples_dict = {}
        for component_object in self.get_conversion_components_objects():
            component_name = component_object.get_name()
            inputs = component_object.get_inputs()
            outputs = component_object.get_outputs()
            main_input = component_object.get_main_input()
            for current_output in [*outputs.keys()]:
                main_input_to_output_conversion_tuples.append((component_name, main_input, current_output))
                main_input_to_output_conversion_tuples_dict.update(
                    {(component_name, main_input, current_output): float(outputs[current_output]) / float(inputs[main_input])})
                output_tuples.append((component_name, current_output))
        return output_tuples, main_input_to_output_conversion_tuples, main_input_to_output_conversion_tuples_dict

    def get_all_conversions(self):
        input_tuples, main_input_to_input_conversion_tuples, main_input_to_input_conversion_tuples_dict\
            = self.get_main_input_to_input_conversions()
        output_tuples, input_to_output_conversion_tuples, input_to_output_conversion_tuples_dict\
            = self.get_main_input_to_output_conversions()
        return input_tuples, main_input_to_input_conversion_tuples, main_input_to_input_conversion_tuples_dict,\
            output_tuples, input_to_output_conversion_tuples, input_to_output_conversion_tuples_dict

    def get_generation_time_series(self):
        generation_profiles_dict = {}
        if len(self.get_generator_components_objects()) > 0:
            path = self.get_path_data() + self.get_profile_data()
            if path.split('.')[-1] == 'xlsx':
                profile = pd.read_excel(path, index_col=0)
            else:
                profile = pd.read_csv(path, index_col=0)

            for generator in self.get_generator_components_objects():
                generator_name = generator.get_name()
                ind = 0
                for cl in range(self.get_number_clusters()):
                    for t in range(self.get_covered_period()):
                        generation_profiles_dict.update({(generator_name, cl, t):
                                                         float(profile.loc[profile.index[ind], generator.get_name()])})
                        ind += 1
        return generation_profiles_dict

    def get_demand_time_series(self):
        hourly_demand_dict = {}
        total_demand_dict = {}
        for commodity in self.get_all_commodities():
            commodity_name = commodity.get_name()
            if commodity.is_demanded():
                if not commodity.is_total_demand():
                    for cl in range(self.get_number_clusters()):
                        for t in range(self.get_covered_period()):
                            hourly_demand_dict.update({(commodity_name, cl, t): float(commodity.get_demand())})
                else:
                    total_demand_dict.update({commodity_name: float(commodity.get_demand())})
        return hourly_demand_dict, total_demand_dict

    def get_purchase_price_time_series(self):
        purchase_price_dict = {}
        for commodity in self.get_all_commodities():
            commodity_name = commodity.get_name()
            if commodity.is_purchasable():
                for cl in range(self.get_number_clusters()):
                    for t in range(self.get_covered_period()):
                        purchase_price_dict.update({(commodity_name, cl, t): float(commodity.get_purchase_price())})
        return purchase_price_dict

    def get_sale_price_time_series(self):
        sell_price_dict = {}
        for commodity in self.get_all_commodities():
            commodity_name = commodity.get_name()
            if commodity.is_saleable():
                for cl in range(self.get_number_clusters()):
                    for t in range(self.get_covered_period()):
                        sell_price_dict.update({(commodity_name, cl, t): float(commodity.get_sale_price())})
        return sell_price_dict

    def get_conversion_components_names(self):
        conversion_components_names = []
        for c in self.get_all_component_names():
            if self.get_component(c).get_component_type() == 'conversion':
                conversion_components_names.append(self.get_component(c).get_name())
        return conversion_components_names

    def get_conversion_components_objects(self):
        conversion_components_objects = []
        for c in self.get_all_component_names():
            if self.get_component(c).get_component_type() == 'conversion':
                conversion_components_objects.append(self.get_component(c))
        return conversion_components_objects

    def get_storage_components_names(self):
        storage_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'storage':
                storage_components_names.append(self.get_component(c).get_name())
        return storage_components_names

    def get_storage_components_objects(self):
        storage_components_objects = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'storage':
                storage_components_objects.append(self.get_component(c))
        return storage_components_objects

    def get_generator_components_names(self):
        generator_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'generator':
                generator_components_names.append(self.get_component(c).get_name())
        return generator_components_names

    def get_generator_components_objects(self):
        generator_components_objects = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'generator':
                generator_components_objects.append(self.get_component(c))
        return generator_components_objects

    def adjust_commodity(self, name, commodity_object):
        components = self.get_component_by_commodity(name)
        for c in components:
            inputs = self.get_component(c).get_inputs()
            inputs[commodity_object.get_name()] = inputs.pop(name)
            self.get_component(c).set_inputs(inputs)

            if name == self.get_component(c).get_main_input():
                self.get_component(c).set_main_input(commodity_object.get_name())

            outputs = self.get_component(c).get_outputs()
            outputs[commodity_object.get_name()] = outputs.pop(name)
            self.get_component(c).set_outputs(outputs)

            if name == self.get_component(c).get_main_output():
                self.get_component(c).set_main_output(commodity_object.get_name())

        for g in self.get_generator_components_objects():
            if g.get_generated_commodity() == name:
                g.set_generated_commodity(commodity_object.get_name())

        for s in self.get_storage_components_objects():
            if s.get_name() == name:
                new_storage = deepcopy(s)
                new_storage.set_name(commodity_object.get_name())
                self.remove_component_entirely(name)
                self.add_component(commodity_object.get_name(), new_storage)

        self.add_commodity(commodity_object.get_name(), commodity_object)

    def add_component(self, name, component):
        self.components.update({name: component})

    def get_all_component_names(self):
        return [*self.components.keys()]

    def get_all_components(self):
        components = []
        for c in self.get_all_component_names():
            components.append(self.get_component(c))
        return components

    def get_component(self, name):
        return self.components[name]

    def remove_component_entirely(self, name):
        self.components.pop(name)

    def add_commodity(self, name, commodity):
        self.commodities.update({name: commodity})

    def remove_commodity_entirely(self, name):
        self.commodities.pop(name)

    def get_all_commodities(self):
        return self.commodities

    def get_all_commodity_names(self):
        all_commodities = []
        for s in [*self.get_all_commodities().keys()]:
            if s not in all_commodities:
                all_commodities.append(s)
        return all_commodities

    def get_commodity(self, name):
        return self.commodities[name]

    def get_commodity_by_component(self, component):
        return self.components[component].get_commodities()

    def get_component_by_commodity(self, commodity):
        components = []
        for c in self.components:
            if self.get_component(c).get_component_type() == 'conversion':
                if commodity in self.get_commodity_by_component(c):
                    components.append(c)
        return components

    def set_integer_steps(self, integer_steps):
        self.integer_steps = integer_steps

    def get_integer_steps(self):
        return self.integer_steps

    def set_uses_representative_periods(self, uses_representative_periods):
        self.uses_representative_periods = bool(uses_representative_periods)

    def get_uses_representative_periods(self):
        return self.uses_representative_periods

    def set_covered_period(self, covered_period):
        self.covered_period = int(covered_period)

    def get_covered_period(self):
        return self.covered_period

    def set_facility_lifetime(self, facility_lifetime):
        self.facility_lifetime = facility_lifetime

    def get_facility_lifetime(self):
        return self.facility_lifetime

    def set_single_or_multiple_profiles(self, status):
        self.single_or_multiple_profiles = status

    def get_single_or_multiple_profiles(self):
        return self.single_or_multiple_profiles

    def set_profile_data(self, profile_data):
        self.profile_data = profile_data

    def get_profile_data(self):
        return self.profile_data

    def set_path_data(self, path_data):
        self.path_data = path_data

    def get_path_data(self):
        return self.path_data

    def get_project_name(self):
        return self.project_name

    def set_project_name(self, project_name):
        self.project_name = project_name

    def set_monetary_unit(self, monetary_unit):
        self.monetary_unit = monetary_unit

    def get_monetary_unit(self):
        return self.monetary_unit

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

    def set_operation_time_series(self, operation_time_series):
        self.operation_time_series = operation_time_series

    def get_operation_time_series(self):
        return self.operation_time_series

    def set_objective_function_value(self, objective_function_value):
        self.objective_function_value = objective_function_value

    def get_objective_function_value(self):
        return self.objective_function_value

    def __copy__(self):
        # deepcopy mutable objects
        names_dict = copy.deepcopy(self.names_dict)
        components = copy.deepcopy(self.components)
        commodities = copy.deepcopy(self.commodities)
        instance = copy.deepcopy(self.instance)
        operation_time_series = copy.deepcopy(self.operation_time_series)

        return ParameterObject(project_name=self.project_name,
                               integer_steps=self.integer_steps, facility_lifetime=self.facility_lifetime,
                               names_dict=names_dict, commodities=commodities,
                               components=components, profile_data=self.profile_data,
                               single_or_multiple_profiles=self.single_or_multiple_profiles,
                               uses_representative_periods=self.uses_representative_periods,
                               representative_periods_length=self.representative_periods_length,
                               covered_period=self.covered_period,
                               monetary_unit=self.monetary_unit, instance=instance,
                               operation_time_series=operation_time_series,
                               copy_object=True)


ParameterObjectCopy = type('CopyOfB', ParameterObject.__bases__, dict(ParameterObject.__dict__))

from rlptx.ptx.component import ConversionComponent, StorageComponent, GenerationComponent
from rlptx.ptx.commodity import Commodity
from rlptx.ptx.framework import PtxSystem
from rlptx.util import DATA_DIR, open_yaml_file


def load_project(path_data=DATA_DIR, config_file="not_robust_FT_all_data_no_scaling.yaml"):
    """Load project data into PtxSystem."""
    empty_ps = PtxSystem()
    ptx_config = open_yaml_file(path_data / config_file)
    initialized_ps = init_project(empty_ps, ptx_config)
    return initialized_ps

def init_project(ptx_system, case_data):
    """Initialize PtxSystem with data from config file. Works for version 0.1.1"""
    assert case_data['version'] == '0.1.1', "This function only works for config files with version 0.1.1"
    
    # Set general parameters
    ptx_system.project_name = case_data['project_name']

    # Allocate components and parameters
    for component in [*case_data['component'].keys()]:
        name = case_data['component'][component]['name']
        variable_om = case_data['component'][component]['variable_om']
        fixed_capacity = case_data['component'][component]['fixed_capacity']

        if case_data['component'][component]['component_type'] == 'conversion':
            min_p = case_data['component'][component]['min_p']
            max_p = case_data['component'][component]['max_p']

            ramp_up = case_data['component'][component]['ramp_up']
            ramp_down = case_data['component'][component]['ramp_down']

            conversion_component = ConversionComponent(name=name, variable_om=variable_om,
                                                       min_p=min_p, max_p=max_p, 
                                                       ramp_up=ramp_up, ramp_down=ramp_down, 
                                                       fixed_capacity=fixed_capacity)
            ptx_system.add_component(name, conversion_component)

        elif case_data['component'][component]['component_type'] == 'storage':
            min_soc = case_data['component'][component]['min_soc']
            max_soc = case_data['component'][component]['max_soc']
            charging_efficiency = case_data['component'][component]['charging_efficiency']
            discharging_efficiency = case_data['component'][component]['discharging_efficiency']
            ratio_capacity_p = case_data['component'][component]['ratio_capacity_p']
            stored_commodity = case_data['component'][component]['stored_commodity']

            storage_component = StorageComponent(name=name, variable_om=variable_om, 
                                                 charging_efficiency=charging_efficiency,
                                                 discharging_efficiency=discharging_efficiency,
                                                 min_soc=min_soc, max_soc=max_soc, 
                                                 ratio_capacity_p=ratio_capacity_p,
                                                 stored_commodity=stored_commodity,
                                                 fixed_capacity=fixed_capacity)
            ptx_system.add_component(name, storage_component)

        elif case_data['component'][component]['component_type'] == 'generator':
            generated_commodity = case_data['component'][component]['generated_commodity']
            curtailment_possible = case_data['component'][component]['curtailment_possible']

            generator = GenerationComponent(name=name, variable_om=variable_om,
                                            generated_commodity=generated_commodity,
                                            curtailment_possible=curtailment_possible,
                                            fixed_capacity=fixed_capacity)
            ptx_system.add_component(name, generator)

    # Conversions
    for c in [*case_data['conversions'].keys()]:
        component = ptx_system.components[c]
        for i in [*case_data['conversions'][c]['input'].keys()]:
            component.add_input(i, case_data['conversions'][c]['input'][i])

        for o in [*case_data['conversions'][c]['output'].keys()]:
            component.add_output(o, case_data['conversions'][c]['output'][o])

        component.main_input = case_data['conversions'][c]['main_input']
        component.main_output = case_data['conversions'][c]['main_output']

    # Commodities
    for c in [*case_data['commodity'].keys()]:
        name = case_data['commodity'][c]['name']
        commodity_unit = case_data['commodity'][c]['unit']

        available = case_data['commodity'][c]['available']
        emittable = case_data['commodity'][c]['emitted']
        purchasable = case_data['commodity'][c]['purchasable']
        saleable = case_data['commodity'][c]['saleable']
        demanded = case_data['commodity'][c]['demanded']
        is_total_demand = case_data['commodity'][c]['total_demand']
        
        # Purchasable commodities
        purchase_price = case_data['commodity'][c]['purchase_price']

        # Saleable commodities
        selling_price = case_data['commodity'][c]['selling_price']

        # Demand
        demand = case_data['commodity'][c]['demand']

        commodity = Commodity(name=name, commodity_unit=commodity_unit, 
                              available=available, purchasable=purchasable, 
                              saleable=saleable, emittable=emittable,
                              demanded=demanded, is_total_demand=is_total_demand, demand=demand,
                              purchase_price=purchase_price, sale_price=selling_price)
        ptx_system.add_commodity(name, commodity)
    
    return ptx_system

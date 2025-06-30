from ptx.core import Element


class Commodity(Element):
    
    def __init__(self, name, commodity_unit,
                 emittable=False, available=False, purchasable=False, 
                 purchase_price=0, saleable=False, sale_price=0,
                 demanded=False, demand=0, is_total_demand=False,
                 purchased_quantity=0., purchase_costs=0., sold_quantity=0., 
                 selling_revenue=0., emitted_quantity=0., available_quantity=0., 
                 demanded_quantity=0., charged_quantity=0., discharged_quantity=0., 
                 total_storage_costs=0., consumed_quantity=0.,
                 produced_quantity=0., total_production_costs=0.,
                 generated_quantity=0., total_generation_costs=0.):
        """
        Class for commodities
        
        :param name: [string] - Abbreviation of commodity
        :param commodity_unit: [string] - Unit of commodity
        :param emittable: [boolean] - can be emitted?
        :param available: [boolean] - is freely available without limitation or price?
        :param purchasable: [boolean] - can be purchased?
        :param purchase_price: [float or list] - fixed price or time varying price
        :param saleable: [boolean] - can be sold?
        :param sale_price: [float or list] - fixed price or time varying price
        :param demanded: [boolean] - is demanded?
        :param demand: [float] - Demand
        :param is_total_demand: [boolean] - Demand over all time steps or for each time step
        """

        self.name = name
        self.commodity_unit = commodity_unit

        self.emittable = bool(emittable)
        self.available = bool(available)

        self.purchasable = bool(purchasable)
        self.purchase_price = float(purchase_price)
        
        self.saleable = bool(saleable)
        self.sale_price = float(sale_price)

        self.demanded = bool(demanded)
        self.is_total_demand = bool(is_total_demand)
        self.demand = float(demand)

        self.purchased_quantity = purchased_quantity
        self.purchase_costs = purchase_costs

        self.sold_quantity = sold_quantity
        self.selling_revenue = selling_revenue

        self.emitted_quantity = emitted_quantity
        self.available_quantity = available_quantity
        self.demanded_quantity = demanded_quantity

        self.charged_quantity = charged_quantity
        self.discharged_quantity = discharged_quantity
        self.total_storage_costs = total_storage_costs

        self.produced_quantity = produced_quantity
        self.consumed_quantity = consumed_quantity
        # Important: total production costs only derive from conversion components where commodity is main output
        self.total_production_costs = total_production_costs

        self.generated_quantity = generated_quantity
        self.total_generation_costs = total_generation_costs

    def get_possible_observation_attributes(self, relevant_attributes):
        possible_attributes = []
        for attribute in relevant_attributes:
            if attribute == "purchased_quantity" and self.purchasable or \
               attribute == "sold_quantity" and self.saleable or \
               attribute == "selling_revenue" and self.saleable or \
               attribute == "demanded_quantity" and self.demanded or \
               attribute == "emitted_quantity" and self.emittable:
                possible_attributes.append(attribute)
        return possible_attributes

    def get_possible_action_methods(self, relevant_methods):
        possible_methods = []
        for method in relevant_methods:
            if method == Commodity.purchase_commodity and self.purchasable or \
               method == Commodity.sell_commodity and self.saleable or \
               method == Commodity.emit_commodity and self.emittable:
                possible_methods.append(method)
        return possible_methods

    def __copy__(self):
        return Commodity(name=self.name, commodity_unit=self.commodity_unit, emittable=self.emittable, 
            available=self.available, purchasable=self.purchasable, purchase_price=self.purchase_price, 
            saleable=self.saleable, sale_price=self.sale_price, demanded=self.demanded, demand=self.demand, 
            is_total_demand=self.is_total_demand, purchased_quantity=self.purchased_quantity, 
            purchase_costs=self.purchase_costs, sold_quantity=self.sold_quantity, 
            selling_revenue=self.selling_revenue, emitted_quantity=self.emitted_quantity, 
            available_quantity=self.available_quantity, demanded_quantity=self.demanded_quantity, 
            charged_quantity=self.charged_quantity, discharged_quantity=self.discharged_quantity, 
            total_storage_costs=self.total_storage_costs, consumed_quantity=self.consumed_quantity, 
            produced_quantity=self.produced_quantity, total_production_costs=self.total_production_costs, 
            generated_quantity=self.generated_quantity, total_generation_costs=self.total_generation_costs)

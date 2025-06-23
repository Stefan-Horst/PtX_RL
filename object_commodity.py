class Commodity:

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_unit(self, unit):
        self.commodity_unit = unit

    def get_unit(self):
        return self.commodity_unit

    def set_energy_content(self, energy_content):
        self.energy_content = energy_content

    def get_energy_content(self):
        return self.energy_content

    def set_purchasable(self, status):
        self.purchasable = status

    def is_purchasable(self):
        return self.purchasable

    def set_purchase_price(self, purchase_price):
        self.purchase_price = float(purchase_price)

    def get_purchase_price(self):
        return self.purchase_price

    def set_saleable(self, status):
        self.saleable = status

    def is_saleable(self):
        return self.saleable

    def set_sale_price(self, sale_price):
        self.sale_price = float(sale_price)

    def get_sale_price(self):
        return self.sale_price

    def set_available(self, status):
        self.available = status

    def is_available(self):
        return self.available

    def set_emittable(self, status):
        self.emittable = status

    def is_emittable(self):
        return self.emittable

    def set_demanded(self, status):
        self.demanded = status

    def is_demanded(self):
        return self.demanded

    def set_demand(self, demand):
        self.demand = float(demand)

    def get_demand(self):
        return self.demand

    def set_total_demand(self, status):
        self.total_demand = status

    def is_total_demand(self):
        return self.total_demand

    def set_purchased_quantity(self, purchased_quantity):
        self.purchased_quantity = purchased_quantity

    def get_purchased_quantity(self):
        return self.purchased_quantity

    def set_purchase_costs(self, purchase_costs):
        self.purchase_costs = purchase_costs

    def get_purchase_costs(self):
        return self.purchase_costs

    def set_sold_quantity(self, sold_quantity):
        self.sold_quantity = sold_quantity

    def get_sold_quantity(self):
        return self.sold_quantity

    def set_selling_revenue(self, selling_revenue):
        self.selling_revenue = selling_revenue

    def get_selling_revenue(self):
        return self.selling_revenue

    def set_available_quantity(self, available_quantity):
        self.available_quantity = available_quantity

    def get_available_quantity(self):
        return self.purchased_quantity

    def set_emitted_quantity(self, emitted_quantity):
        self.emitted_quantity = emitted_quantity

    def get_emitted_quantity(self):
        return self.emitted_quantity

    def set_demanded_quantity(self, demanded_quantity):
        self.demanded_quantity = demanded_quantity

    def get_demanded_quantity(self):
        return self.demanded_quantity

    def set_charged_quantity(self, charged_quantity):
        self.charged_quantity = charged_quantity

    def get_charged_quantity(self):
        return self.charged_quantity

    def set_discharged_quantity(self, discharged_quantity):
        self.discharged_quantity = discharged_quantity

    def get_discharged_quantity(self):
        return self.discharged_quantity

    def set_total_storage_costs(self, total_storage_costs):
        self.total_storage_costs = total_storage_costs

    def get_total_storage_costs(self):
        return self.total_storage_costs

    def set_standby_quantity(self, standby_quantity):
        self.standby_quantity = standby_quantity

    def get_standby_quantity(self):
        return self.standby_quantity

    def set_consumed_quantity(self, consumed_quantity):
        self.consumed_quantity = consumed_quantity

    def get_consumed_quantity(self):
        return self.consumed_quantity

    def set_produced_quantity(self, produced_quantity):
        self.produced_quantity = produced_quantity

    def get_produced_quantity(self):
        return self.produced_quantity

    def set_total_production_costs(self, total_production_costs):
        # Important: Total production costs only derive from conversion components where commodity is main output
        self.total_production_costs = total_production_costs

    def get_total_production_costs(self):
        return self.total_production_costs

    def set_generated_quantity(self, generated_quantity):
        self.generated_quantity = generated_quantity

    def get_generated_quantity(self):
        return self.generated_quantity

    def set_total_generation_costs(self, total_generation_costs):
        self.total_generation_costs = total_generation_costs

    def get_total_generation_costs(self):
        return self.total_generation_costs

    def __copy__(self):
        return Commodity(
            name=self.name, commodity_unit=self.commodity_unit,
            energy_content=self.energy_content,
            emittable=self.emittable, available=self.available,
            purchasable=self.purchasable, purchase_price=self.purchase_price,
            saleable=self.saleable, sale_price=self.sale_price, demanded=self.demanded,
            demand=self.demand, total_demand=self.total_demand,
            purchased_quantity=self.purchased_quantity, purchase_costs=self.purchase_costs,
            sold_quantity=self.sold_quantity, selling_revenue=self.selling_revenue,
            emitted_quantity=self.emitted_quantity, available_quantity=self.available_quantity,
            demanded_quantity=self.demanded_quantity, charged_quantity=self.charged_quantity,
            discharged_quantity=self.discharged_quantity, total_storage_costs=self.total_storage_costs,
            standby_quantity=self.standby_quantity, consumed_quantity=self.consumed_quantity,
            produced_quantity=self.produced_quantity, total_production_costs=self.total_production_costs,
            generated_quantity=self.generated_quantity, total_generation_costs=self.total_generation_costs)

    def __init__(self, name, commodity_unit, energy_content=None,
                 emittable=False, available=False,
                 purchasable=False, purchase_price=0, saleable=False, sale_price=0,
                 demanded=False, demand=0, total_demand=False,
                 purchased_quantity=0., purchase_costs=0., sold_quantity=0., selling_revenue=0.,
                 emitted_quantity=0., available_quantity=0., demanded_quantity=0.,
                 charged_quantity=0., discharged_quantity=0., total_storage_costs=0.,
                 standby_quantity=0., consumed_quantity=0.,
                 produced_quantity=0., total_production_costs=0.,
                 generated_quantity=0., total_generation_costs=0.):

        """
        Class for commodities
        
        :param name: [string] - Abbreviation of commodity
        :param commodity_unit: [string] - Unit of commodity
        :param energy_content: [float] - Energy content per unit
        :param emittable: [boolean] - can be emitted?
        :param available: [boolean] - is freely available without limitation or price?
        :param purchasable: [boolean] - can be purchased?
        :param purchase_price: [float or list] - fixed price or time varying price
        :param saleable: [boolean] - can be sold?
        :param sale_price: [float or list] - fixed price or time varying price
        :param demanded: [boolean] - is demanded?
        :param demand: [float] - Demand
        :param total_demand: [boolean] - Demand over all time steps or for each time step
        """

        self.name = name
        self.commodity_unit = commodity_unit
        if energy_content is not None:
            self.energy_content = float(energy_content)
        elif self.commodity_unit == 'kWh':
            self.energy_content = 0.001
        elif self.commodity_unit == 'MWh':
            self.energy_content = 1
        elif self.commodity_unit == 'GWh':
            self.energy_content = 1000
        elif self.commodity_unit == 'kJ':
            self.energy_content = 2.7777e-7
        elif self.commodity_unit == 'MJ':
            self.energy_content = 2.7777e-4
        elif self.commodity_unit == 'GJ':
            self.energy_content = 2.7777e-1
        else:
            self.energy_content = 0

        self.emittable = bool(emittable)
        self.available = bool(available)

        self.purchasable = bool(purchasable)
        self.purchase_price = float(purchase_price)
        
        self.saleable = bool(saleable)
        self.sale_price = float(sale_price)

        self.demanded = bool(demanded)
        self.total_demand = bool(total_demand)
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

        self.standby_quantity = standby_quantity

        self.produced_quantity = produced_quantity
        self.consumed_quantity = consumed_quantity
        self.total_production_costs = total_production_costs

        self.generated_quantity = generated_quantity
        self.total_generation_costs = total_generation_costs

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

    def apply_action_method(self, method, ptx_system, values):
        """Actually apply the values returned by the action method to this component."""
        if method == Commodity.purchase_commodity:
            quantity, cost = values
            self.purchased_quantity += quantity
            self.available_quantity += quantity
            self.purchase_costs += cost
            ptx_system.balance -= cost
            return True
        if method == Commodity.sell_commodity:
            quantity, revenue = values
            self.available_quantity -= quantity
            self.sold_quantity += quantity
            self.selling_revenue += revenue
            ptx_system.balance += revenue
            return True
        if method == Commodity.emit_commodity:
            quantity = values[0]
            self.available_quantity -= quantity
            self.emitted_quantity += quantity
            return True
        return False

    def purchase_commodity(self, quantity, ptx_system):
        """Purchase quantity of commodity if available balance is sufficient. 
        Otherwise purchase as much as possible. 
        Note that this method only calculates the new values, but does not apply them to this component. 
        Returns new values to be applied, status, whether purchasing the commodity succeeded, 
        and whether this action could be completed exactly as requested."""
        if quantity < 0:
            return (0,0), f"Cannot purchase quantity {quantity:.4f} of {self.name}.", True, False
        
        status = None
        exact_completion = True
        cost = quantity * self.purchase_price
        if cost > ptx_system.balance:
            # try to purchase as much as possible
            new_quantity = ptx_system.balance / self.purchase_price
            new_cost = new_quantity * self.purchase_price
            status = (f"Tried to purchase {quantity:.4f} {self.name} for {cost:.4f}€, "
                      f"but only {ptx_system.balance:.4f}€ available. "
                      f"Instead, purchase {new_quantity:.4f} for {new_cost:.4f}€.")
            exact_completion = False
            quantity = new_quantity
            cost = new_cost
        else:
            status = f"Purchased {quantity:.4f} {self.name} for {cost:.4f}€."
        
        values = (quantity, cost)
        return values, status, True, exact_completion
    
    def sell_commodity(self, quantity, ptx_system):
        """Sell quantity of commodity. If quantity is greater than available quantity, 
        sell as much as possible. 
        Note that this method only calculates the new values, but does not apply them to this component. 
        Returns new values to be applied, status, whether selling the commodity succeeded, 
        and whether this action could be completed exactly as requested."""
        if quantity < 0:
            return (0,0), f"Cannot sell quantity {quantity:.4f} of {self.name}.", True, False
        
        status = None
        exact_completion = True
        if quantity > self.available_quantity:
            # try to sell as much as possible
            revenue = self.available_quantity * self.sale_price
            status = (f"Tried to sell {quantity:.4f} {self.name}, but only "
                      f"{self.available_quantity:.4f} available. Instead, "
                      f"sell {self.available_quantity:.4f} for {revenue:.4f}€.")
            exact_completion = False
            quantity = self.available_quantity
        else:
            revenue = quantity * self.sale_price
            status = f"Sold {quantity:.4f} {self.name} for {revenue:.4f}€."
        
        values = (quantity, revenue)
        return values, status, True, exact_completion
    
    def emit_commodity(self, quantity, ptx_system):
        """Emit quantity of commodity. If quantity is greater than available quantity, 
        emit as much as possible.
        Note that this method only calculates the new values, but does not apply them to this component. 
        Returns new values to be applied, status, whether emitting the commodity succeeded, 
        and whether this action could be completed exactly as requested."""
        if quantity < 0:
            return (0,), f"Cannot emit quantity {quantity:.4f} of {self.name}.", True, False
        
        status = None
        exact_completion = True
        if quantity > self.available_quantity:
            # try to emit as much as possible
            status = (f"Tried to emit {quantity:.4f} {self.name}, but only "
                      f"{self.available_quantity:.4f} available. Instead, emit that much.")
            exact_completion = False
            quantity = self.available_quantity
        else:
            status = f"Emit {quantity:.4f} {self.name}."
        
        values = (quantity,)
        return values, status, True, exact_completion

    def get_possible_observation_attributes(self, relevant_attributes):
        possible_attributes = []
        for attribute in relevant_attributes:
            if (
                attribute == "purchased_quantity" and self.purchasable or 
                attribute == "sold_quantity" and self.saleable or 
                attribute == "selling_revenue" and self.saleable or 
                attribute == "demanded_quantity" and self.demanded or 
                attribute == "emitted_quantity" and self.emittable
            ):
                possible_attributes.append(attribute)
        return possible_attributes

    def get_possible_action_methods(self, relevant_method_tuples):
        possible_methods = []
        for method_tuple in relevant_method_tuples:
            if (
                method_tuple[0] == Commodity.purchase_commodity and self.purchasable or 
                method_tuple[0] == Commodity.sell_commodity and self.saleable or 
                method_tuple[0] == Commodity.emit_commodity and self.emittable
            ):
                possible_methods.append(method_tuple)
        return possible_methods

    def __str__(self):
        return (f"--{self.name}--(purchased_quantity={self.purchased_quantity:.4f}, "
                f"purchase_costs={self.purchase_costs:.4f}, sold_quantity={self.sold_quantity:.4f}, "
                f"selling_revenue={self.selling_revenue:.4f}, emitted_quantity={self.emitted_quantity:.4f}, "
                f"available_quantity={self.available_quantity:.4f}, demanded_quantity={self.demanded_quantity:.4f}, "
                f"charged_quantity={self.charged_quantity:.4f}, discharged_quantity={self.discharged_quantity:.4f}, "
                f"total_storage_costs={self.total_storage_costs:.4f}, consumed_quantity={self.consumed_quantity:.4f}, "
                f"produced_quantity={self.produced_quantity:.4f}, total_production_costs={self.total_production_costs:.4f}, "
                f"generated_quantity={self.generated_quantity:.4f}, total_generation_costs={self.total_generation_costs:.4f})")

    def __repr__(self):
        return (f"Commodity(name={self.name!r}, commodity_unit={self.commodity_unit!r}, "
                f"emittable={self.emittable!r}, available={self.available!r}, "
                f"purchasable={self.purchasable!r}, purchase_price={self.purchase_price!r}, "
                f"saleable={self.saleable!r}, sale_price={self.sale_price}, demanded={self.demanded!r}, "
                f"demand={self.demand!r}, is_total_demand={self.is_total_demand!r}, "
                f"purchased_quantity={self.purchased_quantity!r}, purchase_costs={self.purchase_costs!r}, "
                f"sold_quantity={self.sold_quantity!r}, selling_revenue={self.selling_revenue!r}, "
                f"emitted_quantity={self.emitted_quantity!r}, available_quantity={self.available_quantity!r}, "
                f"demanded_quantity={self.demanded_quantity!r}, charged_quantity={self.charged_quantity!r}, "
                f"discharged_quantity={self.discharged_quantity!r}, total_storage_costs={self.total_storage_costs!r}, "
                f"consumed_quantity={self.consumed_quantity!r}, produced_quantity={self.produced_quantity!r}, "
                f"total_production_costs={self.total_production_costs!r}, generated_quantity={self.generated_quantity!r}, "
                f"total_generation_costs={self.total_generation_costs!r})")

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

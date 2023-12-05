from player import Player, defaultdict, Colors, OwnershipDegree, TradeOffer
import heapq
from copy import copy, deepcopy


# TODO: don't print colors if one of them is mortgaged
# TODO: something about the unmortgages happening all together
# TODO: somehow ai players building on properties they don't have monopolies for

class AIPlayer(Player):
    def __init__(self, player_number, token, trade_threshold=1000):
        super().__init__(player_number, token)
        self.trade_threshold = trade_threshold # the dollar limit of negative difference in gains that the player is willing to allow in a trade.
        # the lower the limit, the less likely the player will be willing to trade. if negative, the player will only trade when they gain more than the other player gains
        self.analyzed_properties = set() # used for deciding trades
        self.analyzed_sales = set() # used for deciding mortgages
        self.analyzed_builds = set() # used for deciding builds
        self.marginal_income_gains = self.init_marginal_income_gains()

    def init_marginal_income_gains(self):
        marginal_income = defaultdict(int) # dictionary of colors keyed to array where index+1 is marginal gain for that house
        marginal_income[Colors.BROWN] = [0.34, 1.14, 3.43, 3.99, 4.56]
        marginal_income[Colors.LIGHTBLUE] = [1.35, 4.13, 12.81, 9.36, 10.32]
        marginal_income[Colors.PINK] = [2.39, 7.97, 23.04, 13.74, 10.76]
        marginal_income[Colors.ORANGE] = [3.85, 11.71, 31.58, 17.60, 17.60]
        marginal_income[Colors.RED] = [4.86, 14.86, 39.23, 15.26, 15.26]
        marginal_income[Colors.YELLOW] = [5.41, 18.04, 37.97, 13.94, 13.94]
        marginal_income[Colors.GREEN] = [6.46, 21.25, 40.79, 15.60, 14.26]
        marginal_income[Colors.DARKBLUE] = [4.90, 16.96, 32.31, 11.25, 11.25]
        return marginal_income
        
    def calculate_available_capital(self, mortgage_degree):
        # doesn't calculate money gained from selling houses, maybe add option to do so
        return self.money + self.calculate_mortgage_yield(mortgage_degree)[0]

    def calculate_mortgage_yield(self, max_degree):
        # doesn't think about houses
        total = 0
        properties = []
        for property in self.properties.values():
            degree = self.get_degree_of_ownership(property.color)
            if property.is_mortgaged or degree.value > max_degree.value or (property.can_develop and property.num_houses > 0):
                continue
            total += property.mortgage_amount
            properties.append(property)
        return total, properties


    def decide_mortgage(self, amount):
        if len(self.properties) == 0 or len(self.mortgaged_property_names) == len(self.properties) or self.money >= amount:
            return
        
        # first, mortgage properties without houses
        mortgage_degrees = [OwnershipDegree.ONE, OwnershipDegree.ALMOST_MONOPOLY, OwnershipDegree.MONOPOLY]
        for degree in mortgage_degrees:
            mortgage_yield, properties = self.calculate_mortgage_yield(degree)
            if mortgage_yield + self.money >= amount or degree == OwnershipDegree.MONOPOLY: # if at final degree, must mortgage
                properties_to_mortgage, _ = self.decide_mortgage_recurse(set(properties), defaultdict(list), amount - self.money, 0)
                for property_set in properties_to_mortgage.values():
                    for property in property_set:
                        self.properties[property.name].mortgage()
                break
        if self.money >= amount:
            return
        
        # then, sell houses
        self.analyzed_sales = set()
        _, houses_by_color, _ = self.sell_houses_recurse(amount - self.money, defaultdict(int), 0)
        for color in houses_by_color.keys():
            properties = self.properties_by_set[color]
            for _ in range(houses_by_color[color]):
                for property in properties:
                    property.sell_house()
        if self.money >= amount:
            return
        
        # then, mortgage properties that have had their houses sold
        _, properties = self.calculate_mortgage_yield(OwnershipDegree.MONOPOLY)
        properties_to_mortgage, _ = self.decide_mortgage_recurse(set(properties), defaultdict(list), amount - self.money, 0)
        for property_set in properties_to_mortgage.values():
            for property in property_set:
                self.properties[property.name].mortgage()


    def decide_mortgage_recurse(self, available_properties, properties_to_mortgage, amount, loss_in_worth):
        if amount <= 0 or len(available_properties) == 0:
            return properties_to_mortgage, loss_in_worth
        
        min_loss_in_worth = float('inf')
        best_properties_to_mortgage = deepcopy(properties_to_mortgage)

        for property in available_properties:
            new_available_properties = set(available_properties)
            new_available_properties.remove(property)
            new_loss_in_worth = loss_in_worth + self.calculate_property_worth(self.player_number, property, -len(properties_to_mortgage[property.color]))
            new_properties_to_mortgage = deepcopy(properties_to_mortgage)
            new_properties_to_mortgage[property.color].append(property)
            new_amount = amount - property.mortgage_amount
            properties_to_mortgage_result, loss_in_worth_result = self.decide_mortgage_recurse(new_available_properties, new_properties_to_mortgage, new_amount, new_loss_in_worth)
            if loss_in_worth_result < min_loss_in_worth:
                min_loss_in_worth = loss_in_worth_result
                best_properties_to_mortgage = deepcopy(properties_to_mortgage_result)

        return best_properties_to_mortgage, min_loss_in_worth
    
    # houses_by_color: number of houses to sell by color
    # marginal_income: negative number indicating how much income will change from sale of houses
    # amount_left: positive number indicating how much money is still needed
    def sell_houses_recurse(self, amount_left, houses_by_color, marginal_income):
        if amount_left <= 0:
            return amount_left, houses_by_color, marginal_income
        if self.sell_already_analyzed(houses_by_color):
            return amount_left, best_houses_by_color, -float('inf')
                
        best_houses_by_color = copy(houses_by_color)
        max_marginal_income = marginal_income
        min_amount_left = amount_left
        self.add_to_analyzed_sales(houses_by_color)

        for color in self.get_buildable_colors():
            property = self.properties_by_set[color][0]
            num_houses = property.num_houses - houses_by_color[color]
            if num_houses == 0: # already sold all we can
                continue
            sell_amount = (property.build_cost // 2) * len(self.properties_by_set[color])

            new_houses_by_color = copy(houses_by_color)
            new_houses_by_color[color] += 1
            new_marginal_income = marginal_income - self.marginal_income_gains[color][property.num_houses - new_houses_by_color[color]]
            amount_left_result, houses_by_color_result, marginal_income_result = self.sell_houses_recurse(amount_left - sell_amount, new_houses_by_color, new_marginal_income)
            # want to minimize amount_left until 0 - once past zero, maximize marginal_income
            if (min_amount_left <= 0 and amount_left_result <= 0) or min_amount_left == amount_left_result:
                if marginal_income_result > max_marginal_income:
                    amount_left = amount_left_result
                    max_marginal_income = marginal_income_result
                    best_houses_by_color = copy(houses_by_color_result)
            elif amount_left_result < min_amount_left:
                amount_left = amount_left_result
                max_marginal_income = marginal_income_result
                best_houses_by_color = copy(houses_by_color_result)

        return min_amount_left, best_houses_by_color, max_marginal_income

    def add_to_analyzed_sales(self, houses_by_color):
        sale_combo = "".join([f"{color.value}{houses_by_color[color]}" for color in houses_by_color.keys()])
        self.analyzed_sales.add(sale_combo)
    def sell_already_analyzed(self, houses_by_color):
        sale_combo = "".join([f"{color.value}{houses_by_color[color]}" for color in houses_by_color.keys()])
        return sale_combo in self.analyzed_sales

    def decide_unmortgage(self):
        budget = self.money - 300
        if budget < 0: 
            return
        
        # check if there are properties that can be built on; if so, don't unmortgage
        for color in self.get_buildable_colors():
            properties = self.properties_by_set[color]
            for property in properties:
                if not property.is_mortgaged and property.num_houses < 5:
                    return
        
        mortgaged_properties = [self.properties[name] for name in self.mortgaged_property_names]
        # unmortgage in worth descending
        properties_to_unmortgage = self.get_highest_worth_properties_for_player(self.player_number, mortgaged_properties)
        while budget > 0 and len(properties_to_unmortgage) > 0:
            _, property = heapq.heappop(properties_to_unmortgage)
            self.properties[property.name].unmortgage()


    def decide_purchase(self, property):
        # if property final piece to monopoly set or railroad, be willing to mortgage for purchase
        if self.get_degree_of_ownership(property.color) == OwnershipDegree.ALMOST_MONOPOLY or property.color == Colors.RR:
            if self.calculate_available_capital(OwnershipDegree.ONE) >= property.cost:
                return True
        if property.cost > self.money or property.color == Colors.UTILITY:
            return False
        return True
    
    def decide_bid(self, property, current_bid):
        bid = current_bid + 10
        # if property final piece to monopoly set or railroad, be willing to mortgage for bid
        if self.get_degree_of_ownership(property.color) == OwnershipDegree.ALMOST_MONOPOLY or property.color == Colors.RR:
            if self.calculate_available_capital(OwnershipDegree.ONE) >= bid:
                return bid
            
        if bid > self.money:
            return 0
        
        if property.color == Colors.UTILITY:
            # willing to pay half price or less for utility
            return bid if bid <= property.cost // 2 else 0
        
        worth = self.calculate_property_worth(self.player_number, property)
        return bid if bid <= worth else 0

    
    def resolve_development(self):
        if self.money < 200 or len(self.get_buildable_colors()) == 0:
            return
        self.analyzed_builds = set()
        houses_by_color, marginal_income = self.resolve_development_recurse(self.money, defaultdict(int), 0)
        if marginal_income < 0:
            return
        for color in houses_by_color.keys():
            properties = self.properties_by_set[color]
            for _ in range(houses_by_color[color]):
                for property in properties:
                    property.build_house()

    def resolve_development_recurse(self, money_left, houses_by_color, marginal_income):
        best_houses_by_color = copy(houses_by_color)
        max_marginal_income = -float('inf')

        # not sure if this is best way to do it, but returns negative marginal income at base cases
        if self.build_already_analyzed(houses_by_color) or money_left < 0:
            return best_houses_by_color, max_marginal_income
        
        max_marginal_income = marginal_income
        self.add_to_analyzed_builds(houses_by_color)
        
        for color in self.get_buildable_colors():
            properties = self.properties_by_set[color]
            # check to see if any are mortgaged
            mortgaged = False
            for property in properties:
                if property.is_mortgaged:
                    mortgaged = True
                    break
            if mortgaged:
                continue

            property = properties[0]
            num_houses = property.num_houses + houses_by_color[color]
            if num_houses == 5: # already built all we can
                continue
            build_cost = property.build_cost * len(self.properties_by_set[color])

            new_houses_by_color = copy(houses_by_color)
            new_houses_by_color[color] += 1
            new_marginal_income = marginal_income + self.marginal_income_gains[color][property.num_houses + new_houses_by_color[color] - 1]
            houses_by_color_result, marginal_income_result = self.resolve_development_recurse(money_left - build_cost, new_houses_by_color, new_marginal_income)
            if marginal_income_result > max_marginal_income:
                max_marginal_income = marginal_income_result
                best_houses_by_color = copy(houses_by_color_result)

        return best_houses_by_color, max_marginal_income
        
    def add_to_analyzed_builds(self, houses_by_color):
        build_combo = "".join([f"{color.value}{houses_by_color[color]}" for color in houses_by_color.keys()])
        self.analyzed_builds.add(build_combo)
    def build_already_analyzed(self, houses_by_color):
        build_combo = "".join([f"{color.value}{houses_by_color[color]}" for color in houses_by_color.keys()])
        return build_combo in self.analyzed_builds
    
    def decide_trade(self):
        property_queue = []
        # find properties to request
        for color in self.properties_by_set.keys():
            properties = self.trade_matrix.get_other_player_color_properties(color, self)
            for property in properties:
                worth = self.calculate_property_worth(self.player_number, property)
                heapq.heappush(property_queue, (-worth, property))
        
        while len(property_queue) > 0:
            gain, property_to_request = heapq.heappop(property_queue)
            # switch gain back from negative (since using a minheap)
            gain *= -1
            recipient = property_to_request.owner.player_number
            trade_offer = TradeOffer(self.player_number, recipient)
            trade_offer.recipient_bundle.properties.append(property_to_request)
            recipient_gain = -1 * self.calculate_property_worth(recipient, property_to_request)
            properties_to_offer = set(self.properties.values())
            self.analyzed_properties = set()
            
            properties_to_offer, total_gain, total_recipient_gain = self.decide_trade_recurse(recipient, properties_to_offer, defaultdict(list), gain, recipient_gain)
            
            # see if trade is bad
            if total_gain <= 0 or total_recipient_gain < -100:
                continue
            if total_recipient_gain >= -100 and total_recipient_gain <= 0:
                if self.money < 100:
                    # don't have enough money to make it a good deal
                    continue
                trade_offer.initiator_bundle.money += 100

            for properties in properties_to_offer.values():
                for property in properties:
                    trade_offer.initiator_bundle.properties.append(property)
            
            # if their end of the deal is way better, add money to their side
            gain_difference = total_recipient_gain - gain
            if gain_difference > self.trade_threshold:
                adjustment = ((gain_difference - self.trade_threshold) / 2) + 10
                trade_offer.recipient_bundle.money += adjustment
            if self.trade_matrix.has_been_declined_previously(trade_offer):
                continue
            if self.trade_matrix.resolve_trade(trade_offer):
                return # make a request until a trade happens or all options are expended
            
    # available_properties: set
    # properties_to_offer: dict of properties organized by color
    def decide_trade_recurse(self, recipient, available_properties, properties_to_offer, gain, recipient_gain):
        if gain <= 0 or recipient_gain >= -100 or len(available_properties) == 0 or self.trade_already_analyzed(properties_to_offer):
            return properties_to_offer, gain, recipient_gain
        
        self.add_to_analyzed_trades(properties_to_offer)
        
        # want to add properties to trade until opponent gain is at least above -100
        # want to minimize gain difference
        min_gain_diff = float('inf')
        best_gain = gain
        best_recipient_gain = recipient_gain
        best_properties_to_offer = properties_to_offer

        for property in available_properties:
            # update new values
            new_available_properties = set(available_properties)
            new_available_properties.remove(property)
            new_gain = gain - self.calculate_property_worth(self.player_number, property, -len(properties_to_offer[property.color]))
            new_recipient_gain = recipient_gain + self.calculate_property_worth(recipient, property, len(properties_to_offer[property.color]))
            new_properties_to_offer = deepcopy(properties_to_offer)
            new_properties_to_offer[property.color].append(property)

            properties_to_offer_result, gain_result, recipient_gain_result = self.decide_trade_recurse(recipient, new_available_properties, new_properties_to_offer, new_gain, new_recipient_gain)
            gain_diff = gain - gain_result
            if recipient_gain_result >= -100 and gain_diff < min_gain_diff:
                min_gain_diff = gain_diff
                best_gain = gain_result
                best_recipient_gain = recipient_gain_result
                best_properties_to_offer = properties_to_offer_result
        
        return best_properties_to_offer, best_gain, best_recipient_gain
    
    def copy_default_dict_list(self, item):
        new_item = defaultdict(list)
        for key in item.keys():
            new_item[key] = item[key]
        return new_item
    
    def add_to_analyzed_trades(self, properties):
        property_names = []
        for property_list in properties.values():
            for property in property_list:
                property_names.append(property.name)
        names = ''.join(property_names)
        self.analyzed_properties.add(names)

    def trade_already_analyzed(self, properties):
        property_names = []
        for property_list in properties.values():
            for property in property_list:
                property_names.append(property.name)
        names = ''.join(property_names)
        return names in self.analyzed_properties

    def attempt_trade_for_goojf_card(self):
        # TODO: add check for how much money. if less than 50, will need to mortgage something anyways probably
        other_players = self.trade_matrix.get_other_players_with_goojf_cards(self)
        for other_player in other_players:
            trade_offer = TradeOffer(self.player_number, other_player)
            trade_offer.recipient_bundle.num_goojf_cards = 1
            trade_offer.initiator_bundle.money = 30
            if self.trade_matrix.resolve_trade(trade_offer):
                break

    def get_highest_worth_properties_for_player(self, player_number, properties_to_offer, color_modifiers=defaultdict(int)):
        properties = []
        for property in properties_to_offer:
            worth = self.calculate_property_worth(player_number, property, color_modifiers[property.color])
            heapq.heappush(properties, (-worth, property))
        return properties

    def will_accept_trade_offer(self, trade_offer: TradeOffer):
        gain = trade_offer.initiator_bundle.money - trade_offer.recipient_bundle.money
        initiator_gain = trade_offer.recipient_bundle.money - trade_offer.initiator_bundle.money

        # check if money exchange would cause bankruptcy
        if self.money + gain < 0:
            return False
        
        # calculate worth of properties
        color_modifiers = defaultdict(int) # used to determine cumulative value of multiple properties when trading more than one
        initiator_color_modifiers = defaultdict(int)
        # first, players lose properties
        for property in trade_offer.recipient_bundle.properties:
            gain -= self.calculate_property_worth(trade_offer.recipient, property, color_modifiers[property.color])
            color_modifiers[property.color] -= 1
        for property in trade_offer.initiator_bundle.properties:
            initiator_gain -= self.calculate_property_worth(trade_offer.initiator, property, initiator_color_modifiers[property.color])
            initiator_color_modifiers[property.color] -= 1
        # then, players gain properties
        for property in trade_offer.initiator_bundle.properties:
            gain += self.calculate_property_worth(trade_offer.recipient, property, color_modifiers[property.color])
            color_modifiers[property.color] += 1
        for property in trade_offer.recipient_bundle.properties:
            initiator_gain += self.calculate_property_worth(trade_offer.initiator, property, initiator_color_modifiers[property.color])
            initiator_color_modifiers[property.color] += 1

        goojf_value = 0 if self.trade_matrix.other_player_has_monopoly(self.player_number) else 50
        gain += goojf_value * trade_offer.initiator_bundle.num_goojf_cards
        gain -= goojf_value * trade_offer.recipient_bundle.num_goojf_cards

        goojf_value = 0 if self.trade_matrix.other_player_has_monopoly(trade_offer.initiator) else 50
        initiator_gain += goojf_value * trade_offer.recipient_bundle.num_goojf_cards
        initiator_gain -= goojf_value * trade_offer.initiator_bundle.num_goojf_cards

        return gain > 0 and initiator_gain - gain < self.trade_threshold

    def calculate_property_worth(self, owner, property, modifier=0):
            # calculates worth of a property for a player if they were to own it
            worth = property.cost
            if property.owner == None or property.owner.player_number != owner:
                # if player doesn't own specified property, assume they do
                modifier += 1
            # check how many other properties of same color other player has
            degree = self.trade_matrix.get_degree_of_ownership(owner, property.color, modifier)
            if degree == OwnershipDegree.MONOPOLY:
                worth *= 10 # always allow them to lose a monopoly, never give up a monopoly
            if degree == OwnershipDegree.ALMOST_MONOPOLY:
                worth *= 2
            if property.is_mortgaged:
                worth -= property.unmortgage_amount
            return worth

    def will_get_out_of_jail(self):
        if self.trade_matrix.other_player_has_monopoly(self.player_number):
            return False
        
        if self.goojf_cards == 0:
            self.attempt_trade_for_goojf_card()
        if self.goojf_cards > 0:
            self.goojf_cards -= 1
            return True
        
        if self.money < 50:
            return False
        self.charge(50)
        return True
        
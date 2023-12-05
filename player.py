import time
from collections import defaultdict
from abc import abstractmethod
from enums import Colors, OwnershipDegree
from trade_matrix import TradeMatrix, TradeOffer
import settings

class Player():
    def __init__(self, player_number, token):
        self.player_number = player_number
        self.token = token
        self.money = 1500
        self.board_space = 0
        self.properties = {} # keyed by property names
        self.properties_by_set = defaultdict(list)
        self.mortgaged_property_names = set()
        self.goojf_cards = 0
        self.jail_counter = 0

    def set_trade_matrix(self, trade_matrix: TradeMatrix):
        self.trade_matrix = trade_matrix

    def charge(self, amount):
        if amount == 0:
            return
        self.decide_mortgage(amount)
        self.money -= amount
        print(f"Player {self.player_number} loses ${amount} (${self.money})")
        if not settings.fast:
            time.sleep(0.5)
    
    def add_money(self, amount, other_actions=True):
        self.money += amount
        print(f"Player {self.player_number} gains ${amount} (${self.money})")
        if not settings.fast:
            time.sleep(0.5)
        
        if other_actions:
            self.decide_trade()
            self.decide_unmortgage()
            self.resolve_development()
    
    def calculate_total_worth(self):    
        total = self.money
        for property in self.properties.values():
            if property.is_mortgaged:
                total += property.mortgage_amount
            else:
                total += property.cost
                if property.can_develop:
                    total += property.num_houses * property.build_cost
        return total

    def gain_real_estate(self, property, can_trade=True):
        property.owner = self
        self.properties[property.name] = property
        self.properties_by_set[property.color].append(property)
        if property.is_mortgaged:
            self.mortgaged_property_names.add(property.name)
            
        if can_trade:
            self.decide_trade()
        self.decide_unmortgage()
        self.resolve_development()

    def lose_real_estate(self, property):
        # what to do about property's owner?
        if property.name in self.mortgaged_property_names:
            self.mortgaged_property_names.remove(property.name)
        del self.properties[property.name]
        self.properties_by_set[property.color].remove(property)

    def has_full_set(self, color: Colors):
        return self.get_degree_of_ownership(color) == OwnershipDegree.MONOPOLY
    
    def get_degree_of_ownership(self, color: Colors, modifier=0):
        monopoly_num = 3
        if color == Colors.BROWN or color == Colors.DARKBLUE or color == Colors.UTILITY:
            monopoly_num -= 1
        if color == Colors.RR:
            monopoly_num += 1

        num_properties = len(self.properties_by_set[color]) + modifier
        if num_properties == monopoly_num:
            return OwnershipDegree.MONOPOLY
        elif num_properties == monopoly_num - 1:
            # don't treat utility as almost monopoly
            if color == Colors.UTILITY:
                return OwnershipDegree.ONE
            return OwnershipDegree.ALMOST_MONOPOLY
        elif num_properties == 0:
            return OwnershipDegree.NONE
        else:
            return OwnershipDegree.ONE
            
    def get_buildable_colors(self):
        colors = self.trade_matrix.get_colors()
        buildable_colors = []
        for color in colors:
            if self.has_full_set(color):
                buildable_colors.append(color)
        return buildable_colors
    
    # def get_full_sets(self):
    #     sets = self.get_buildable_colors()
    #     non_buildable_sets = [Colors.RR, Colors.UTILITY]
    #     for set in non_buildable_sets:
    #         if self.has_full_set(set):
    #             sets.append(set)
    #     return sets
    
    @abstractmethod
    def decide_mortgage(self, amount):
        # player decides which properties to mortgage and which houses to sell
        pass
    @abstractmethod
    def decide_unmortgage(self):
        # player decides which properties to unmortgage
        pass
    @abstractmethod
    def decide_purchase(self, property):
        # player returns boolean about whether or not to make purchase
        return True
    @abstractmethod
    def resolve_development(self):
        # player decides which properties to build on
        pass
    @abstractmethod
    def will_get_out_of_jail(self):
        # player decides whether or not to play card, trade for card, or spend $50
        return False
    @abstractmethod
    def decide_trade(self):
        # player decides whether or not to initiate trade with other player
        pass
    @abstractmethod
    def will_accept_trade_offer(self, trade_offer: TradeOffer):
        # player decides whether or not to accept a trade offer from another player
        pass
    @abstractmethod
    def decide_bid(self, property, current_bid):
        # decide what to bid in an auction
        pass
    
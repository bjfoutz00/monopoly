from enums import OwnershipDegree, Colors
import time

# class MetaProperty():
#     def __init__(self, name, cost, color, owner_player_number, is_mortgaged, unmortgage_amount):
#         self.name = name
#         self.cost = cost
#         self.color = color
#         self.owner_player_number = owner_player_number
#         self.is_mortgaged = is_mortgaged
#         self.unmortgage_amount = unmortgage_amount
#     def __lt__(self,other):
#         return self.name < other.name


class TradeMatrix():
    def __init__(self, players):
        self.players = {}
        for player in players:
            self.players[player.player_number] = player
        self.declined_trade_offers = set()
    
    """
    Trading
    """
    def get_tradeable_property_names(self, player_number, trade_offer):
        names = set()
        properties_in_offer = trade_offer.initiator_bundle.properties if player_number == trade_offer.initiator else trade_offer.recipient_bundle.properties
        names_in_offer = set([property.name for property in properties_in_offer])
        for color in self.players[player_number].properties_by_set.keys():
            # check if any properties have houses; if so, don't add
            if not self.check_if_color_tradeable(player_number, color):
                continue
            for property in self.players[player_number].properties_by_set[color]:
                if property.name in names_in_offer:
                    continue
                names.add(property.name)
        return names
    
    def check_if_color_tradeable(self, player_number, color):
        if self.players[player_number].has_full_set(color):
            for property in self.players[player_number].properties_by_set[color]:
                if property.can_develop and property.num_houses > 0:
                    return False
        return True
    
    def get_player_goojf_cards(self, player_number):
        return self.players[player_number].goojf_cards
    
    def resolve_trade(self, trade_offer):
        initiator = self.players[trade_offer.initiator]
        recipient = self.players[trade_offer.recipient]
        print(f"Player {initiator.player_number} offered to trade with player {recipient.player_number}. Here is the offer:")
        trade_offer.print_offer()

        if not recipient.will_accept_trade_offer(trade_offer):
            print(f"Player {recipient.player_number} declined the trade")
            self.declined_trade_offers.add(trade_offer.get_text())
            return False
        
        print(f"Player {recipient.player_number} accepted the trade")
        
        # exchange properties
        for property in trade_offer.initiator_bundle.properties:
            print(f"Player {initiator.player_number} trades {property.name_colored} to player {recipient.player_number}")
            property = initiator.properties[property.name]
            initiator.lose_real_estate(property)
            recipient.gain_real_estate(property, False)
        for property in trade_offer.recipient_bundle.properties:
            print(f"Player {recipient.player_number} trades {property.name_colored} to player {initiator.player_number}")
            property = recipient.properties[property.name]
            recipient.lose_real_estate(property)
            initiator.gain_real_estate(property, False)

        # exchange money
        initiator.charge(trade_offer.initiator_bundle.money)
        recipient.add_money(trade_offer.initiator_bundle.money, False)
        recipient.charge(trade_offer.recipient_bundle.money)
        initiator.add_money(trade_offer.recipient_bundle.money, False)

        # exchange goojf cards
        initiator.goojf_cards -= trade_offer.initiator_bundle.num_goojf_cards
        recipient.goojf_cards += trade_offer.initiator_bundle.num_goojf_cards
        recipient.goojf_cards -= trade_offer.recipient_bundle.num_goojf_cards
        initiator.goojf_cards += trade_offer.recipient_bundle.num_goojf_cards

        return True

    def has_been_declined_previously(self, trade_offer):
        return trade_offer.get_text() in self.declined_trade_offers
    
    # def add_property_to_bundle(self, bundle, property_name, owner_player_number):
    #     property = self.players[owner_player_number].properties[property_name]
    #     bundle.properties.append()

    """
    Utility
    """
    def get_colors(self):
        # doesn't include rr and utility
        return [Colors.BROWN, Colors.LIGHTBLUE, Colors.PINK, Colors.ORANGE, Colors.RED, Colors.YELLOW, Colors.GREEN, Colors.DARKBLUE]  

    def get_player_property(self, trade_player_number, property_name):
        return self.players[trade_player_number].properties[property_name]
    
    def other_player_has_monopoly(self, active_player_number):
        for player in self.players.values():
            if player.player_number == active_player_number:
                continue
            if len(player.get_buildable_colors()) > 0:
                return True
    
    def get_other_player_color_properties(self, color, active_player):
        properties = []
        for player in self.players.values():
            if player == active_player or color not in player.properties_by_set:
                continue
            # check if any properties have houses; if so, don't add
            if not self.check_if_color_tradeable(player.player_number, color):
                continue

            for property in player.properties_by_set[color]:
                properties.append(property)
        return properties
            
    def get_other_players_with_goojf_cards(self, active_player):
        player_numbers = []
        for player in self.players.values():
            if player == active_player:
                continue
            if player.goojf_cards > 0:
                player_numbers.append(player.player_number)
        return player_numbers
                

    # gets a player's degree of ownership for a specific color set
    def get_degree_of_ownership(self, player_number, color, modifier):
        return self.players[player_number].get_degree_of_ownership(color, modifier)
            
    def get_player_money(self, player_number):
        return self.players[player_number].money

    def find_player_with_property(self, property_name):
        for player in self.players.values():
            if property_name in player.properties:
                return player.player_number
 
    """
    Printing
    """
    def print_tradeable_properties(self, player_number, trade_offer):
        print(f"Here are player {player_number}'s tradeable properties:")
        time.sleep(0.5)
        properties_in_offer = set(trade_offer.initiator_bundle.properties) if player_number == trade_offer.initiator else set(trade_offer.recipient_bundle.properties)
        
        for property in self.players[player_number].properties.values():
            if (property.can_develop and property.num_houses > 0) or property in properties_in_offer:
                continue
            print(f"{property.name_colored} (value: {property.cost})")
            time.sleep(0.5)
    
    def print_other_players(self, active_player):
        for player in self.players.values():
            if player == active_player:
                continue
            self.print_player_state(player.player_number)

    def print_player_state(self, player_number):
        player = self.players[player_number]
        print(f"Player {player.player_number} ({player.token}):")
        time.sleep(0.5)
        print(f"\twealth: {player.money}")
        time.sleep(0.5)
        print("\tproperties:")
        time.sleep(0.5)
        properties = ""
        for property in player.properties.values():
            properties += f"{property.name_colored}, "
        properties = properties[:-2]
        print(f"\t\t{properties}")
        time.sleep(0.5)


class TradeOffer():
    def __init__(self, initiator, recipient):
        # player numbers
        self.initiator = initiator
        self.recipient = recipient
        self.initiator_bundle = TradeBundle()
        self.recipient_bundle = TradeBundle()

    def print_offer(self):
        print(f"What player {self.initiator} is offering:")
        time.sleep(0.5)
        self.initiator_bundle.print_bundle()
        print(f"What player {self.initiator} is requesting:")
        time.sleep(0.5)
        self.recipient_bundle.print_bundle()
    
    def get_text(self):
        text = ""
        text += str(self.initiator)
        text += str(self.recipient)
        text += self.initiator_bundle.get_text()
        text += self.recipient_bundle.get_text()
        return text


class TradeBundle():
    def __init__(self):
        self.properties = [] # list of properties with necessary information only so player can't mutate fields
        self.money = 0
        self.num_goojf_cards = 0

    def print_bundle(self):
        if len(self.properties) > 0:
            info = "\t Properties: "
            for property in self.properties:
                info += f"{property.name_colored}"
                if property.is_mortgaged:
                    info += "(mortgaged)"
                info += ", "
            info = info[:-2]
            print(info)
            time.sleep(0.5)
        if self.money > 0:
            print(f"\tMoney: {self.money}")
            time.sleep(0.5)
        if self.num_goojf_cards > 0:
            print(f"Get Out of Jail Free cards: {self.num_goojf_cards}")
            time.sleep(0.5)
        time.sleep(0.5)

    def get_text(self):
        text = ""
        text += "".join([property.name_colored for property in self.properties])
        text += str(self.money)
        text += str(self.num_goojf_cards)
        return text
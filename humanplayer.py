from player import Player, TradeOffer, time
import settings

class HumanPlayer(Player):
    def __init__(self, player_number, token):
        super().__init__(player_number, token)

    def decide_unmortgage(self):
        while len(self.mortgaged_property_names) > 0 and \
                input(f"(Player {self.player_number}) You have {len(self.mortgaged_property_names)} mortgaged properties. Would you like to unmortgage any? (y/n): ") == "y":
            
            print("Here are the available properties to unmortgage: ")
            if not settings.fast:
                time.sleep(0.5)
            for name in self.mortgaged_property_names:
                property = self.properties[name]
                print(f"{property.name_colored}, unmortgage cost: {property.unmortgage_amount}")
                if not settings.fast:
                    time.sleep(0.5)

            done = False
            while not done:
                command = input("Enter name of property to unmortgage (or press 'x' to cancel umortgage action): ")
                if command == 'x':
                    return
                if command not in self.mortgaged_property_names:
                    print("Sorry, you can't unmortgage that property.")
                    if not settings.fast:
                        time.sleep(0.5)
                    continue
                property_to_unmortgage = self.properties[command]
                confirm = input(f"Unmortgaging {property_to_unmortgage.name_colored} for {property_to_unmortgage.unmortgage_amount}. Press enter to confirm or 'x' to cancel: ")
                if confirm == 'x':
                    continue
                done = True
                property_to_unmortgage.unmortgage()


    def decide_mortgage(self, amount):
        if len(self.properties) == 0 or len(self.mortgaged_property_names) == len(self.properties):
            return
        
        print(f"(Player {self.player_number}) You are being charged ${amount}. You have ${self.money}.")
        if not settings.fast:
            time.sleep(0.5)
        while input("Would you like to mortgage anything? (y/n): ") == "y" and len(self.mortgaged_property_names) < len(self.properties):
            print("Here are the available properties to mortgage: ")
            if not settings.fast:
                time.sleep(0.5)
            available_properties = set()
            for property_set in self.properties_by_set.values():
                for property in property_set:
                    if property.is_mortgaged:
                        continue
                    if property.can_develop and property.num_houses > 0:
                        # don't allow sale of house if has less houses than other properties in the same set
                        even_sale = True
                        for set_property in self.properties_by_set[property.color]:
                            if set_property.num_houses > property.num_houses:
                                even_sale = False
                                break
                        if not even_sale:
                            continue
                        available_properties.add(property.name)
                        print(f"{property.name_colored} ({property.num_houses} houses): ${property.build_cost // 2}/house")
                        if not settings.fast:
                            time.sleep(0.5)
                    else:
                        # don't allow property to be mortgaged if other properties in the same set have houses
                        if property.can_develop:
                            can_mortgage = True
                            for set_property in self.properties_by_set[property.color]:
                                if set_property.num_houses > 0:
                                    can_mortgage = False
                                    break
                            if not can_mortgage:
                                continue
                        available_properties.add(property.name)
                        print(f"{property.name_colored}: ${property.mortgage_amount}")
                        if not settings.fast:
                            time.sleep(0.5)
            
            done = False
            while not done:
                command = input("Enter name of property to mortgage or sell a house on (or press 'x' to cancel mortgage action): ")
                if command == 'x':
                    return
                if command not in available_properties:
                    print("Sorry, you can't mortgage that property.")
                    if not settings.fast:
                        time.sleep(0.5)
                    continue
                property_to_mortgage = self.properties[command]
                if property_to_mortgage.can_develop and property_to_mortgage.num_houses > 0:
                    confirm = input(f"Selling 1 of {property_to_mortgage.num_houses} houses from {property_to_mortgage.name_colored}. Press enter to confirm or 'x' to cancel: ")
                    if confirm == 'x':
                        continue
                    done = True
                    property_to_mortgage.sell_house()
                else:
                    confirm = input(f"Mortgaging {property_to_mortgage.name_colored}. Press enter to confirm or 'x' to cancel: ")
                    if confirm == 'x':
                        continue
                    done = True
                    property_to_mortgage.mortgage()

    def decide_purchase(self, property):
        return input(f"(Player {self.player_number}) Would you like to buy {property.name_colored} for ${property.cost}? You have ${self.money} (y/n): ") == "y"
    
    def decide_bid(self, property, current_bid):
        command = ""
        while True:
            command = input(f"(Player {self.player_number}) Enter your bid for {property.name_colored}. You must bid at least $10 more than ${current_bid} to stay in the auction: ")
            if not command.isdigit():
                print("Error: enter a number")
                if not settings.fast:
                    time.sleep(0.5)
                continue
            break
        return int(command)
    

    def resolve_development(self):
        buildable_colors = self.get_buildable_colors()
        if len(buildable_colors) == 0:
            return
        while input("(Player {self.player_number}) Would you like to build a house? (y/n): ") == "y":
            print("Here are the available properties to build on: ")
            if not settings.fast:
                time.sleep(0.5)
            available_properties = set()
            for color in buildable_colors:
                for property in self.properties_by_set[color]:
                    if property.is_mortgaged or property.num_houses >= 5:
                        continue
                    # don't allow build of house if has more houses than other properties in the same set
                    even_build = True
                    for set_property in self.properties_by_set[property.color]:
                        if set_property.num_houses < property.num_houses:
                            even_build = False
                            break
                    if not even_build:
                        continue
                    available_properties.add(property.name)
                    print(f"{property.name_colored} ({property.num_houses} houses): ${property.build_cost}/house")
                    if not settings.fast:
                        time.sleep(0.5)
            done = False
            while not done:
                command = input("Enter the name of the property you would like to build on (or press 'x' to cancel build action): ")
                if command == 'x':
                    return
                if command not in available_properties:
                    print("Sorry, you can't build on that property.")
                    if not settings.fast:
                        time.sleep(0.5)
                    continue
                property_to_develop = self.properties[command]
                confirm = input(f"Building 1 house on {property_to_develop.name_colored}. Press enter to confirm or 'x' to cancel: ")
                if confirm == 'x':
                    continue
                done = True
                property_to_develop.build_house()


    def decide_trade(self):
        while input(f"(Player {self.player_number}) Would you like to make a trade? (y/n): ") == "y":
            print("Here are the other player states:")
            if not settings.fast:
                time.sleep(0.5)
            self.trade_matrix.print_other_players(self)
            trade_player_number = ""
            while True:
                command = input("Which player would you like to make a trade with? (enter number): ")
                if not command.isdigit():
                    print("Error: enter a number")
                    if not settings.fast:
                        time.sleep(0.5)
                    continue
                break
            trade_player_number = int(command)
            trade_offer = TradeOffer(self.player_number, int(trade_player_number))

            # your side of offer
            if input("Are you offering any properties to trade? (y/n): ") == "y":
                done = False
                while not done:
                    self.trade_matrix.print_tradeable_properties(self.player_number, trade_offer)
                    command = input(f"Enter the name of the property you would like to offer player {trade_player_number} (or press 'x' to finish adding properties): ")
                    if command == 'x':
                        done = True
                        continue
                    if command not in self.trade_matrix.get_tradeable_property_names(self.player_number, trade_offer):
                        print("Sorry, you can't trade that property.")
                        if not settings.fast:
                            time.sleep(0.5)
                        continue
                    trade_offer.initiator_bundle.properties.append(self.properties[command])
                    print(f"Added {command} to trade offer")
                    if not settings.fast:
                        time.sleep(0.5)
            if input("Are you offering any money? (y/n): ") == "y":
                done = False
                while not done:
                    command = input(f"You have ${self.money}. Enter how much you would like to trade: ")
                    if not command.isdigit():
                        print("Error: enter a number")
                        if not settings.fast:
                            time.sleep(0.5)
                        continue
                    command = int(command)
                    if command > self.money:
                        print(f"WARNING: you are offering ${command - self.money} more than you currently have. If you don't mortgage enough properties to satisfy this difference at the time of trade, you will lose the game.")
                        if not settings.fast:
                            time.sleep(0.5)
                        confirm = input("If you would like to enter a different amount of money, press 'x', else press enter to confirm: ")
                        if confirm == 'x':
                            continue
                    done = True
                    trade_offer.initiator_bundle.money = command
                    print(f"Added ${command} to the trade offer")
                    if not settings.fast:
                        time.sleep(0.5)
            if self.goojf_cards > 0 and input("Are you offering any Get Out of Jail Free cards? (y/n): ") == "y":
                done = False
                while not done:
                    command = input(f"You have {self.goojf_cards} Get Out of Jail Free card(s). How many would you like to offer?")
                    if not command.isdigit():
                        print("Error: enter a number")
                        if not settings.fast:
                            time.sleep(0.5)
                        continue
                    command = int(command)
                    if command > self.goojf_cards:
                        print("Error: you don't have that many cards.")
                        if not settings.fast:
                            time.sleep(0.5)
                        continue
                    trade_offer.initiator_bundle.num_goojf_cards = command
                    done = True
                    print(f"Added {command} Get Out of Jail Free card(s) to the trade offer")
                    if not settings.fast:
                        time.sleep(0.5)

            # other player's side of offer
            if input(f"Are you requesting any properties from player {trade_player_number}? (y/n): ") == "y":
                done = False
                while not done:
                    self.trade_matrix.print_tradeable_properties(trade_player_number, trade_offer)
                    command = input(f"Enter the name of the property you would like to request from player {trade_player_number} (or press 'x' to finish adding properties): ")
                    if command == 'x':
                        done = True
                        continue
                    if command not in self.trade_matrix.get_tradeable_property_names(trade_player_number, trade_offer):
                        print("Sorry, you can't request that property.")
                        if not settings.fast:
                            time.sleep(0.5)
                        continue
                    trade_offer.recipient_bundle.properties.append(self.trade_matrix.get_player_property(trade_player_number, command))
                    print(f"Added {command} to trade offer")
                    if not settings.fast:
                        time.sleep(0.5)
            if input("Are you requesting any money? (y/n): ") == "y":
                done = False
                while not done:
                    trade_player_money = self.trade_matrix.get_player_money(trade_player_number)
                    command = input(f"They have ${trade_player_money}. Enter how much you would like to request: ")
                    if not command.isdigit():
                        print("Error: enter a number")
                        if not settings.fast:
                            time.sleep(0.5)
                        continue
                    command = int(command)
                    if command > trade_player_money:
                        print(f"WARNING: you are requesting ${command - trade_player_money} more than they currently have.")
                        if not settings.fast:
                            time.sleep(0.5)
                        confirm = input("If you would like to enter a different amount of money, press 'x', else press enter to confirm: ")
                        if confirm == 'x':
                            continue
                    done = True
                    trade_offer.recipient_bundle.money = command
                    print(f"Added ${command} to the trade offer")
                    if not settings.fast:
                        time.sleep(0.5)
            trade_player_goojf_cards = self.trade_matrix.get_player_goojf_cards(trade_player_number)
            if trade_player_goojf_cards > 0 and input("Are you requesting any Get Out of Jail Free cards? (y/n): ") == "y":
                done = False
                while not done:
                    command = input(f"They have {trade_player_goojf_cards} Get Out of Jail Free card(s). How many would you like to request?")
                    if not command.isdigit():
                        print("Error: enter a number")
                        if not settings.fast:
                            time.sleep(0.5)
                        continue
                    command = int(command)
                    if command > self.goojf_cards:
                        print("Error: they don't have that many cards.")
                        if not settings.fast:
                            time.sleep(0.5)
                        continue
                    trade_offer.recipient_bundle.num_goojf_cards = command
                    done = True
                    print(f"Added {command} Get Out of Jail Free card(s) to the trade offer")
                    if not settings.fast:
                        time.sleep(0.5)
            
            print("Here is the trade offer you've created:")
            trade_offer.print_offer()
            confirm = input("Press enter to continue or 'x' to cancel the offer: ")
            if confirm == 'x':
                continue
            self.trade_matrix.resolve_trade(trade_offer)

    def will_accept_trade_offer(self, trade_offer: TradeOffer):
        print("\nHere are the player states:")
        self.trade_matrix.print_player_state(trade_offer.initiator)
        self.trade_matrix.print_player_state(self.player_number)
        command = input(f"(Player {self.player_number}) Do you accept the trade? (y/n): ")
        if command == "y":
            return True
        return False

    def will_get_out_of_jail(self):
        command = input(f"(Player {self.player_number}) You have {self.jail_counter} turns left in jail. Would you like to get out now? (y/n): ")
        if command == "y":
            if self.goojf_cards > 0:
                if input(f"Would you like to use a Get Out of Jail Free card? You have {self.goojf_cards}. (y/n): ") == "y":
                    self.goojf_cards -= 1
                    return True
            # TODO: add check to buy goojf card from other players using trade matrix
            if input("Would you like to pay $50 to get out? (y/n): ") == "y":
                self.charge(50)
                return True
        else:
            return False

import os
import random
import time
import math
import NotRouge_game_core # Import the core game logic

# --- Game Constants (Launcher Specific) ---
SAVE_FILE = "NotRouge_save.json"
# ITEMS_FILE and ENEMIES_FILE are implicitly used by NotRouge_game_core's internal loading,
# so they are not directly used here for file loading.

# --- Utility Functions (Terminal Specific) ---

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_input(prompt, valid_choices=None):
    """Gets validated input from the user."""
    while True:
        choice = input(f"\n{prompt} ").strip().lower()
        if valid_choices:
            if choice in valid_choices:
                return choice
            else:
                print("Invalid choice. Please try again.")
        else:
            return choice

def display_message(message, delay=1.5):
    """Displays a message to the user with a delay."""
    print(f"\n--- {message} ---")
    time.sleep(delay)

def display_stats(player):
    """Prints the player's current stats and equipment to the terminal."""
    clear_screen()
    print(f"--- {player.name}'s Stats ---")
    print(f"Level: {player.level} (EXP: {player.experience}/{NotRouge_game_core.calculate_level_up_exp(player.level)})")
    print(f"Health: {player.current_health}/{player.max_health}")
    print(f"Attack: {player.attack}")
    print(f"Defense: {player.defense}")
    print(f"Gold: {player.gold}")
    print("\n--- Equipped Gear ---")
    for slot, item in player.equipped.items():
        print(f"{slot.capitalize()}: {item.name if item else 'None'}")
    print("\n--- Inventory ---")
    if not player.inventory:
        print("Empty")
    else:
        for i, item in enumerate(player.inventory):
            print(f"{i+1}. {item.name} (Type: {item.item_type})")
    print("-" * 30)

# --- Game Logic Functions (Adapted for Terminal) ---

def combat_encounter(player, enemy):
    """Handles a turn-based combat encounter."""
    display_message(f"A wild {enemy.name} appears!", delay=1.5)
    time.sleep(1)

    while player.current_health > 0 and enemy.health > 0:
        clear_screen()
        print(f"--- Combat: {player.name} vs {enemy.name} ---")
        print(f"{player.name} Health: {player.current_health}/{player.max_health} | Attack: {player.attack} | Defense: {player.defense}")
        print(f"{enemy.name} Health: {enemy.health}/{enemy.health_full} | Attack: {enemy.attack} | Defense: {enemy.defense}")
        print("\nWhat will you do?")
        print("1. Attack")
        print("2. Use Item")
        print("3. Flee (50% chance)")
        print("4. Auto-Attack (until enemy dies or 1 HP remaining)")


        choice = get_input("Enter choice (1-4): ", ['1', '2', '3', '4'])

        if choice == '1': # Attack
            player_damage = max(1, player.attack + random.randint(-5, 5)) # Add some variance
            enemy_dead = enemy.take_damage(player_damage, display_message) # Pass display_message for logging
            print(f"You attack the {enemy.name} for {player_damage} damage!")
            time.sleep(0.5)
            if enemy_dead:
                display_message(f"You defeated the {enemy.name}!", delay=1.5)
                player.gold += enemy.gold_drop
                player.gain_exp(enemy.exp_drop, display_message) # Pass display_message for logging
                print(f"You gained {enemy.gold_drop} gold and {enemy.exp_drop} experience.")
                time.sleep(2)
                return True # Combat ended, player won

        elif choice == '2': # Use Item
            consumables = [item for item in player.inventory if item.item_type == "consumable"]
            if not consumables:
                print("You have no usable items.")
                time.sleep(1)
                continue # Skip enemy turn if no item to use

            print("\n--- Your Consumable Items ---")
            for i, item in enumerate(consumables):
                print(f"{i+1}. {item.name} (Heals: {item.heal_amount})")
            print("0. Back")

            item_choice_idx = get_input("Enter item number to use (or 0 to go back): ", [str(i) for i in range(len(consumables) + 1)])
            if item_choice_idx == '0':
                continue # Go back to combat menu

            chosen_item_idx = int(item_choice_idx) - 1
            item_to_use = consumables[chosen_item_idx]

            if item_to_use.heal_amount > 0:
                player.heal(item_to_use.heal_amount, display_message) # Pass display_message for logging
                player.inventory.remove(item_to_use)
                display_message(f"You used a {item_to_use.name}.", delay=1.5)
            else:
                display_message("This item cannot be used in combat.")
                time.sleep(1)
                continue # Skip enemy turn if item not usable

        elif choice == '3': # Flee
            if random.random() < 0.5:
                display_message("You successfully fled from combat!", delay=1.5)
                return False # Combat ended, player fled
            else:
                display_message("You failed to flee!", delay=1.5)

        elif choice == '4': # Auto-Attack
            print("\nInitiating auto-attack...")
            # Auto-attack loop
            while player.current_health > 1 and enemy.health > 0:
                # Player's turn
                player_damage = max(1, player.attack + random.randint(-5, 5))
                enemy_dead = enemy.take_damage(player_damage, display_message) # Pass display_message for logging
                print(f"Auto-attack: You hit the {enemy.name} for {player_damage} damage! ({enemy.name} HP: {enemy.health}/{enemy.health_full})")
                time.sleep(0.1) # Short delay for faster auto-combat

                if enemy_dead:
                    display_message(f"You defeated the {enemy.name}!", delay=1.0)
                    player.gold += enemy.gold_drop
                    player.gain_exp(enemy.exp_drop, display_message) # Pass display_message for logging
                    print(f"You gained {enemy.gold_drop} gold and {enemy.exp_drop} experience.")
                    time.sleep(1.0)
                    return True # Combat ended, player won

                # Enemy's turn (if still alive)
                if enemy.health > 0:
                    enemy_damage = max(1, enemy.attack + random.randint(-3, 3))
                    player_dead = player.take_damage(enemy_damage, display_message) # Pass display_message for logging
                    print(f"Auto-attack: The {enemy.name} hits you for {enemy_damage} damage! (Your HP: {player.current_health}/{player.max_health})")
                    time.sleep(0.1)

                    if player_dead or player.current_health <= 1:
                        if player_dead:
                            # Player died, handle_death will be called by dungeon_adventure
                            return True # Combat ended, player lost
                        else:
                            print("\nYour health is critically low (1 HP remaining)! Auto-attack stopped.")
                            time.sleep(1.5)
                            # Return to the main combat loop for manual action
                            break # Break auto-attack loop to allow player to choose next action
            if player.current_health > 0 and enemy.health > 0: # If auto-attack stopped early but combat not over
                continue # Go back to the main combat menu options

        # Enemy's turn (if still alive and player didn't win or flee or auto-attack finished)
        if enemy.health > 0 and player.current_health > 0 and choice != '4': # Only enemy turn if not auto-attacking or auto-attack didn't finish the combat
            enemy_damage = max(1, enemy.attack + random.randint(-3, 3)) # Add some variance
            player_dead = player.take_damage(enemy_damage, display_message) # Pass display_message for logging
            print(f"The {enemy.name} attacks you for {enemy_damage} damage!")
            time.sleep(0.5)
            if player_dead:
                return True # Combat ended, player lost (handled by NotRouge_game_core.handle_death)
        
        time.sleep(1) # Small pause between turns if not auto-attacking

    return False # Should not be reached if combat ends correctly

def dungeon_adventure(player):
    """Simulates a dungeon exploration."""
    clear_screen()
    display_message("You enter the dark and winding dungeon...", delay=2)
    display_stats(player) # Updated call
    time.sleep(2)

    num_encounters = random.randint(3, 7) # Number of rooms/encounters in this dungeon run
    for i in range(num_encounters):
        if player.current_health <= 0:
            NotRouge_game_core.handle_death(player, display_message)
            return # Exit dungeon if player dies

        clear_screen()
        print(f"--- Dungeon Depth: {i+1}/{num_encounters} ---")
        print(f"Current Health: {player.current_health}/{player.max_health}")
        print("You explore deeper...")
        time.sleep(1)

        encounter_type = random.choices(["combat", "nothing", "treasure", "healing"], weights=[0.6, 0.2, 0.15, 0.05], k=1)[0]

        if encounter_type == "combat":
            if not NotRouge_game_core.DUNGEON_ENEMIES:
                print("No enemies defined in NotRouge_Enemies.txt. Skipping combat.")
                time.sleep(1)
                continue # Skip to next encounter if no enemies loaded
            enemy = random.choice(NotRouge_game_core.DUNGEON_ENEMIES)
            # Create a copy to ensure changes to health are specific to this encounter
            current_enemy = NotRouge_game_core.Enemy(enemy.name, enemy.health_full, enemy.attack, enemy.defense, enemy.gold_drop, enemy.exp_drop)
            combat_result = combat_encounter(player, current_enemy)
            if player.current_health <= 0:
                NotRouge_game_core.handle_death(player, display_message)
                return # Player died, return to main loop
            if not combat_result: # Combat ended without player death or win (e.g., fled, or auto-attack stopped at 1 HP)
                choice = get_input("Continue exploring the dungeon? (y/n): ", ['y', 'n'])
                if choice == 'n':
                    display_message("You retreat from the dungeon.", delay=1.5)
                    display_stats(player) # Updated call
                    return # Player chose to exit dungeon

        elif encounter_type == "treasure":
            gold_found = random.randint(20, 100)
            player.gold += gold_found
            display_message(f"You found a hidden chest with {gold_found} gold!", delay=1.5)
            display_stats(player) # Updated call
            time.sleep(1)
            choice = get_input("Continue exploring the dungeon? (y/n): ", ['y', 'n'])
            if choice == 'n':
                display_message("You retreat from the dungeon.", delay=1.5)
                display_stats(player) # Updated call
                return

        elif encounter_type == "healing":
            heal_amount = random.randint(20, 60)
            player.heal(heal_amount, display_message) # Pass display_message for logging
            display_message(f"You found a refreshing spring and healed {heal_amount} health!", delay=1.5)
            display_stats(player) # Updated call
            time.sleep(1)
            choice = get_input("Continue exploring the dungeon? (y/n): ", ['y', 'n'])
            if choice == 'n':
                display_message("You retreat from the dungeon.", delay=1.5)
                display_stats(player) # Updated call
                return

        else: # "nothing"
            display_message("You found nothing of interest in this area.", delay=1.5)
            display_stats(player) # Updated call
            time.sleep(1)
            choice = get_input("Continue exploring the dungeon? (y/n): ", ['y', 'n'])
            if choice == 'n':
                display_message("You retreat from the dungeon.", delay=1.5)
                display_stats(player) # Updated call
                return

    display_message("You have cleared this section of the dungeon! You return to town.", delay=2)
    display_stats(player) # Updated call
    time.sleep(2)


def shop_menu(player):
    """Handles the shop interface."""
    while True:
        clear_screen()
        print(f"--- Welcome to the Shop! (Gold: {player.gold}) ---")
        
        # Select up to 5 random items to display for buying
        items_to_display_buy = random.sample(NotRouge_game_core.SHOP_ITEMS, min(5, len(NotRouge_game_core.SHOP_ITEMS))) if NotRouge_game_core.SHOP_ITEMS else []

        print("--- Buy Items ---")
        if not items_to_display_buy:
            print("No items available to buy.")
        else:
            for i, item in enumerate(items_to_display_buy):
                item_desc = f"{i+1}. {item.name} ({item.item_type}) - Cost: {item.cost} gold"
                if item.attack_bonus: item_desc += f" | ATK: +{item.attack_bonus}"
                if item.defense_bonus: item_desc += f" | DEF: +{item.defense_bonus}"
                if item.health_bonus: item_desc += f" | HP: +{item.health_bonus}"
                if item.heal_amount: item_desc += f" | Heals: {item.heal_amount}"
                print(item_desc)

        print("\n--- Options ---")
        print("B. Buy Item (enter item number)")
        print("S. Sell Item (enter 's')")
        print("0. Back to Town")

        choice = get_input("Enter your choice: ", [str(i) for i in range(len(items_to_display_buy) + 1)] + ['b', 's'])

        if choice == '0':
            break
        elif choice == 'b':
            if not items_to_display_buy:
                display_message("No items to buy.", delay=1)
                continue
            item_num_str = get_input("Enter item number to buy: ", [str(i+1) for i in range(len(items_to_display_buy))])
            if item_num_str == '0': # User wants to go back to shop options
                continue
            
            item_index = int(item_num_str) - 1
            chosen_item = items_to_display_buy[item_index]

            if player.gold >= chosen_item.cost:
                player.gold -= chosen_item.cost
                # Create a new instance of the item from NotRouge_game_core.Item
                player.inventory.append(NotRouge_game_core.Item(chosen_item.name, chosen_item.item_type, chosen_item.cost,
                                             chosen_item.attack_bonus, chosen_item.defense_bonus,
                                             chosen_item.health_bonus, chosen_item.heal_amount))
                display_message(f"You bought {chosen_item.name} for {chosen_item.cost} gold!", delay=1.5)
                display_stats(player) # Updated call
                time.sleep(1)
            else:
                display_message("You don't have enough gold!", delay=1.5)
                time.sleep(1)
        elif choice == 's':
            sell_items_menu(player)
        else: # Direct item number entry for buying
            item_index = int(choice) - 1
            if 0 <= item_index < len(items_to_display_buy):
                chosen_item = items_to_display_buy[item_index]
                if player.gold >= chosen_item.cost:
                    player.gold -= chosen_item.cost
                    # Create a new instance of the item from NotRouge_game_core.Item
                    player.inventory.append(NotRouge_game_core.Item(chosen_item.name, chosen_item.item_type, chosen_item.cost,
                                                 chosen_item.attack_bonus, chosen_item.defense_bonus,
                                                 chosen_item.health_bonus, chosen_item.heal_amount))
                    display_message(f"You bought {chosen_item.name} for {chosen_item.cost} gold!", delay=1.5)
                    display_stats(player) # Updated call
                    time.sleep(1)
                else:
                    display_message("You don't have enough gold!", delay=1.5)
                    time.sleep(1)
            else:
                print("Invalid item selection for buying.")
                time.sleep(1)


def sell_items_menu(player):
    """Allows the player to sell items from their inventory."""
    while True:
        clear_screen()
        print(f"--- Sell Items (Your Gold: {player.gold}) ---")
        sellable_items = [item for item in player.inventory if item not in player.equipped.values()]

        if not sellable_items:
            print("You have no sellable items in your inventory.")
            input("Press Enter to continue...")
            return

        print("Select an item to sell (0 to go back):")
        for i, item in enumerate(sellable_items):
            sell_price = math.floor(item.cost * NotRouge_game_core.SELL_PRICE_MULTIPLIER) # Use SELL_PRICE_MULTIPLIER from core
            item_desc = f"{i+1}. {item.name} (Type: {item.item_type}) - Sell for: {sell_price} gold"
            print(item_desc)

        choice = get_input("Enter item number: ", [str(i) for i in range(len(sellable_items) + 1)])

        if choice == '0':
            break

        item_index = int(choice) - 1
        if 0 <= item_index < len(sellable_items):
            chosen_item = sellable_items[item_index]
            sell_price = math.floor(chosen_item.cost * NotRouge_game_core.SELL_PRICE_MULTIPLIER)

            # Confirm sale
            confirm = get_input(f"Are you sure you want to sell {chosen_item.name} for {sell_price} gold? (y/n): ", ['y', 'n'])
            if confirm == 'y':
                player.gold += sell_price
                player.inventory.remove(chosen_item)
                display_message(f"You sold {chosen_item.name} for {sell_price} gold!", delay=1.5)
            else:
                display_message("Sale cancelled.", delay=1)
        else:
            print("Invalid item selection.")
        time.sleep(1)


def inventory_menu(player):
    """Allows the player to view and manage their inventory."""
    while True:
        display_stats(player) # Updated call
        print("\n--- Inventory Management ---")
        if not player.inventory:
            print("Your inventory is empty.")
            input("Press Enter to continue...")
            return

        print("Select an item to use/equip (or T to Throw Away, 0 to go back):")
        for i, item in enumerate(player.inventory):
            item_desc = f"{i+1}. {item.name} ({item.item_type})"
            if item.attack_bonus: item_desc += f" | ATK: +{item.attack_bonus}"
            if item.defense_bonus: item_desc += f" | DEF: +{item.defense_bonus}"
            if item.health_bonus: item_desc += f" | HP: +{item.health_bonus}"
            if item.heal_amount: item_desc += f" | Heals: {item.heal_amount}"
            print(item_desc)

        valid_choices_base = [str(i) for i in range(len(player.inventory) + 1)]
        choice = get_input("Enter item number, 'T' to Throw Away, or '0' to go back: ", valid_choices_base + ['t'])

        if choice == '0':
            break
        elif choice == 't':
            throw_away_item_menu(player)
            # After throwing away, refresh the inventory menu
            continue 
        else:
            item_index = int(choice) - 1
            if 0 <= item_index < len(player.inventory):
                chosen_item = player.inventory[item_index]

                if chosen_item.item_type == "consumable":
                    if chosen_item.heal_amount > 0:
                        player.heal(chosen_item.heal_amount, display_message) # Pass display_message
                        player.inventory.remove(chosen_item)
                        display_message(f"You used a {chosen_item.name}.", delay=1.5)
                    else:
                        display_message("This item cannot be used.", delay=1.5)
                else: # Equipable item
                    player.equip_item(chosen_item, display_message) # Pass display_message
                    display_message(f"You equipped {chosen_item.name}.", delay=1.5)
            else:
                print("Invalid item selection.")
            
        time.sleep(1)

def throw_away_item_menu(player):
    """Allows the player to permanently discard items."""
    while True:
        clear_screen()
        print("--- Throw Away Items ---")
        throwable_items = [item for item in player.inventory if item not in player.equipped.values()]

        if not throwable_items:
            print("You have no items in your inventory that can be thrown away (equipped items cannot be thrown away).")
            input("Press Enter to continue...")
            return

        print("Select an item to throw away (0 to go back):")
        for i, item in enumerate(throwable_items):
            print(f"{i+1}. {item.name} (Type: {item.item_type})")

        choice = get_input("Enter item number: ", [str(i) for i in range(len(throwable_items) + 1)])

        if choice == '0':
            break

        item_index = int(choice) - 1
        if 0 <= item_index < len(throwable_items):
            chosen_item = throwable_items[item_index]

            # Confirm throwing away
            confirm = get_input(f"Are you sure you want to throw away {chosen_item.name}? This cannot be undone! (y/n): ", ['y', 'n'])
            if confirm == 'y':
                player.inventory.remove(chosen_item)
                display_message(f"You threw away {chosen_item.name}.", delay=1.5)
            else:
                display_message("Action cancelled.", delay=1)
        else:
            print("Invalid item selection.")
        time.sleep(1)


def town_menu(player):
    """Displays the town menu options."""
    while True:
        clear_screen()
        print(f"--- Welcome to {player.name}'s Town ---")
        display_stats(player) # Updated call
        print("\nWhat would you like to do?")
        print("1. Visit Shop")
        print("2. Enter Dungeon")
        print("3. Manage Inventory/Equipment")
        print("4. Save Game")
        print("5. Exit Game")

        choice = get_input("Enter choice (1-5): ", ['1', '2', '3', '4', '5'])

        if choice == '1':
            shop_menu(player)
        elif choice == '2':
            # Check if there are enemies to fight before entering dungeon
            if not NotRouge_game_core.DUNGEON_ENEMIES:
                display_message("The dungeon seems eerily quiet... (No enemies loaded).", delay=2)
            else:
                dungeon_adventure(player)
                # If player died in dungeon, handle_death will have saved, we restart town menu
                if player.current_health <= 0:
                    print("You've been revived and returned to town!")
                    display_stats(player) # Updated call
                    time.sleep(2)
        elif choice == '3':
            inventory_menu(player)
        elif choice == '4':
            NotRouge_game_core.save_game(player, SAVE_FILE, display_message) # Pass SAVE_FILE and display_message
        elif choice == '5':
            NotRouge_game_core.save_game(player, SAVE_FILE, display_message) # Always save before exiting
            display_message("Thanks for playing! Goodbye.", delay=2)
            return False # Exit game loop
    return True # Stay in town menu

def main_menu():
    """Displays the main game menu."""
    while True:
        clear_screen()
        print("--- NotRouge by Gobytego ---") # Updated game title
        print("1. New Game")
        print("2. Load Game")
        print("3. Exit")

        choice = get_input("Enter choice (1-3): ", ['1', '2', '3'])

        if choice == '1':
            player_name = get_input("Enter your hero's name: ")
            player = NotRouge_game_core.Player(player_name) # Use Player from NotRouge_game_core
            display_message(f"Welcome, {player.name}!", delay=1.5)
            town_menu(player)
        elif choice == '2':
            player = NotRouge_game_core.load_game(SAVE_FILE, display_message) # Pass SAVE_FILE and display_message
            if player:
                town_menu(player)
            else:
                display_message("No saved game found. Please start a new game.", delay=2)
        elif choice == '3':
            display_message("Exiting game. Goodbye!", delay=1.5)
            break

if __name__ == "__main__":
    main_menu()

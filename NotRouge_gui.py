import os
import random
import time
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit,
    QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer

import NotRouge_game_core # Import the core game logic

# --- Game Constants (Launcher Specific) ---
SAVE_FILE = "NotRouge_save.json"
# ITEMS_FILE and ENEMIES_FILE are implicitly used by NotRouge_game_core's internal loading
# so they are not directly used here for file loading.


class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NotRouge by Gobytego GUI") # Updated window title
        self.setGeometry(100, 100, 1000, 700) # Increased window size for split view

        # Set the main window background color to dark purple
        self.setStyleSheet("background-color: #330033;") # Dark purple color

        self.player = None
        self.current_enemy = None
        self.auto_attack_timer = QTimer(self)
        self.auto_attack_timer.timeout.connect(self._auto_attack_turn)

        self._setup_ui()
        # NotRouge_game_core automatically loads data when imported,
        # but we can log that it has happened.
        self.update_game_log("Core game data (items, enemies) loaded.")
        self.show_main_menu()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout for the split window
        main_h_layout = QHBoxLayout(central_widget)

        # --- Left Panel: Player Stats ---
        # Using a QWidget for the panel to apply a distinct background/border
        stats_panel = QWidget()
        stats_panel.setStyleSheet("background-color: #1a001a; border: 1px solid #660066; border-radius: 5px; padding: 5px;")
        stats_v_layout = QVBoxLayout(stats_panel)
        stats_v_layout.setContentsMargins(10, 10, 10, 10) # Add some inner padding
        stats_v_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft) # Align content to top-left

        self.stats_label = QLabel("Loading player stats...")
        self.stats_label.setStyleSheet("font-weight: bold; color: yellow; font-size: 16px;")
        self.stats_label.setWordWrap(True) # Allow text to wrap
        stats_v_layout.addWidget(self.stats_label)
        stats_v_layout.addStretch(1) # Push content to the top of its panel

        main_h_layout.addWidget(stats_panel, 1) # Give stats panel 1 part of the width (e.g., 1/3 of total)


        # --- Right Panel: Game Log and Actions ---
        game_interaction_panel = QWidget()
        game_interaction_panel.setStyleSheet("background-color: #000000; border: 1px solid #660066; border-radius: 5px; padding: 5px;")
        game_interaction_v_layout = QVBoxLayout(game_interaction_panel)
        game_interaction_v_layout.setContentsMargins(10, 10, 10, 10) # Add some inner padding

        self.game_log = QTextEdit()
        self.game_log.setReadOnly(True)
        self.game_log.setStyleSheet("background-color: black; color: green; font-family: 'Consolas', 'Monospace'; font-size: 14px; padding: 5px;")
        game_interaction_v_layout.addWidget(self.game_log, 1) # Game log takes available vertical space in this panel

        self.button_layout = QHBoxLayout() # This will hold the action buttons dynamically
        self.button_layout.setSpacing(5) # Space between buttons
        game_interaction_v_layout.addLayout(self.button_layout)
        game_interaction_v_layout.addStretch(0) # Don't stretch the buttons to the bottom, keep them grouped

        main_h_layout.addWidget(game_interaction_panel, 2) # Give game interaction panel 2 parts of the width (e.g., 2/3 of total)

        # Define buttons
        self.buttons = {}
        # Main Menu Buttons
        self._create_button("New Game", self._handle_new_game, "main_menu")
        self._create_button("Load Game", self._handle_load_game, "main_menu")
        self._create_button("Exit", self.close, "main_menu")
        # Town Buttons
        self._create_button("Visit Shop", lambda: self.show_shop_menu(display_items=True), "town")
        self._create_button("Enter Dungeon", self._start_dungeon, "town")
        self._create_button("Inventory", self.show_inventory_menu, "town")
        self._create_button("Save Game", self._save_current_game, "town")
        self._create_button("Exit Game", self.close, "town")
        # Combat Buttons
        self._create_button("Attack", lambda: self._combat_action("attack"), "combat")
        self._create_button("Use Item", lambda: self._combat_action("use_item"), "combat")
        self._create_button("Flee", lambda: self._combat_action("flee"), "combat")
        self._create_button("Auto-Attack", lambda: self._combat_action("auto_attack"), "combat")
        # Shop/Inventory dynamic buttons will be created as needed

        self.set_button_visibility("none") # Hide all buttons initially

    def _create_button(self, text, handler, group):
        button = QPushButton(text)
        button.clicked.connect(handler)
        button.setProperty("button_group", group) # Custom property to group buttons
        button.setStyleSheet("color: white;") # Set button text color to white
        self.button_layout.addWidget(button)
        self.buttons[text] = button # Store button by its text

    def set_button_visibility(self, group_name):
        """Sets visibility for a specific group of buttons and hides others."""
        for name, button in self.buttons.items():
            if button.property("button_group") == group_name:
                button.show()
                button.setEnabled(True)
            else:
                button.hide()
                button.setEnabled(False)
        # Clear dynamically added buttons
        for i in reversed(range(self.button_layout.count())): 
            widget = self.button_layout.itemAt(i).widget()
            if widget and widget not in self.buttons.values():
                widget.setParent(None) # Remove and delete

    def update_game_log(self, message):
        """Appends a message to the game log."""
        self.game_log.append(message)
        self.game_log.verticalScrollBar().setValue(self.game_log.verticalScrollBar().maximum()) # Scroll to bottom

    def update_stats_display(self):
        """Updates the player stats display."""
        if self.player:
            stats_text = (
                f"Name: {self.player.name} | Level: {self.player.level} "
                f"(EXP: {self.player.experience}/{NotRouge_game_core.calculate_level_up_exp(self.player.level)}) | "
                f"HP: {self.player.current_health}/{self.player.max_health} | "
                f"ATK: {self.player.attack} | DEF: {self.player.defense} | "
                f"Gold: {self.player.gold}\n"
                f"Weapon: {self.player.equipped['weapon'].name if self.player.equipped['weapon'] else 'None'} | "
                f"Armor: {self.player.equipped['armor'].name if self.player.equipped['armor'] else 'None'} | "
                f"Accessory: {self.player.equipped['accessory'].name if self.player.equipped['accessory'] else 'None'}"
            )
        else:
            stats_text = "No player data."
        self.stats_label.setText(stats_text)


    # --- Main Menu Handling ---
    def show_main_menu(self):
        self.set_button_visibility("main_menu")
        self.update_game_log("--- NotRouge by Gobytego ---") # Updated title
        self.update_game_log("Welcome, adventurer!")

    def _handle_new_game(self):
        text, ok = QInputDialog.getText(self, 'New Game', 'Enter your hero\'s name:')
        if ok and text:
            self.player = NotRouge_game_core.Player(text)
            self.update_game_log(f"Welcome, {self.player.name}!")
            self.update_stats_display()
            self.show_town_menu()
        else:
            self.update_game_log("New game cancelled.")

    def _handle_load_game(self):
        self.player = NotRouge_game_core.load_game(SAVE_FILE, self.update_game_log)
        if self.player:
            self.update_game_log("Game loaded. Returning to town.")
            self.update_stats_display()
            self.show_town_menu()
        else:
            self.update_game_log("No saved game found. Please start a new game.")
            self.show_main_menu() # Stay on main menu

    def _save_current_game(self):
        if self.player:
            NotRouge_game_core.save_game(self.player, SAVE_FILE, self.update_game_log)
        else:
            self.update_game_log("No game in progress to save.")

    # --- Town Menu Handling ---
    def show_town_menu(self):
        self.set_button_visibility("town")
        self.update_game_log(f"\n--- Welcome to {self.player.name}'s Town ---")
        self.update_stats_display()
        self.update_game_log("What would you like to do?")

    # --- Shop Menu Handling ---
    def show_shop_menu(self, display_items=True):
        self.set_button_visibility("none") # Hide all main buttons
        self.update_game_log(f"\n--- Welcome to the Shop! (Gold: {self.player.gold}) ---")

        if not NotRouge_game_core.SHOP_ITEMS:
            self.update_game_log("The shop is currently empty. No items to display.")
            self._add_back_button(self.show_town_menu)
            return

        self.shop_items_display = random.sample(NotRouge_game_core.SHOP_ITEMS, min(5, len(NotRouge_game_core.SHOP_ITEMS)))
        self.update_game_log("--- Buy Items ---")
        
        for i, item in enumerate(self.shop_items_display):
            item_desc = f"{i+1}. {item.name} ({item.item_type}) - Cost: {item.cost} gold"
            if item.attack_bonus: item_desc += f" | ATK: +{item.attack_bonus}"
            if item.defense_bonus: item_desc += f" | DEF: +{item.defense_bonus}"
            if item.health_bonus: item_desc += f" | HP: +{item.health_bonus}"
            if item.heal_amount: item_desc += f" | Heals: {item.heal_amount}"
            self.update_game_log(item_desc)
            
            button = QPushButton(f"Buy {item.name} ({item.cost}g)")
            button.clicked.connect(lambda _, idx=i: self._buy_shop_item(idx))
            self.button_layout.addWidget(button)
            button.show() # Make sure new buttons are visible
            button.setStyleSheet("color: white;") # Set button text color to white

        sell_button = QPushButton("Sell Item")
        sell_button.clicked.connect(self._show_sell_items_menu)
        sell_button.setStyleSheet("color: white;") # Set button text color to white
        self.button_layout.addWidget(sell_button)
        sell_button.show()

        self._add_back_button(self.show_town_menu)

    def _buy_shop_item(self, index):
        chosen_item = self.shop_items_display[index]
        if self.player.gold >= chosen_item.cost:
            self.player.gold -= chosen_item.cost
            self.player.inventory.append(NotRouge_game_core.Item(chosen_item.name, chosen_item.item_type, chosen_item.cost,
                                             chosen_item.attack_bonus, chosen_item.defense_bonus,
                                             chosen_item.health_bonus, chosen_item.heal_amount))
            self.update_game_log(f"You bought {chosen_item.name} for {chosen_item.cost} gold!")
            self.update_stats_display()
            self.show_shop_menu(display_items=False) # Refresh shop display
        else:
            self.update_game_log("You don't have enough gold!")
        self.update_stats_display()

    def _show_sell_items_menu(self):
        self.set_button_visibility("none")
        self.update_game_log(f"--- Sell Items (Your Gold: {self.player.gold}) ---")
        sellable_items = [item for item in self.player.inventory if item not in self.player.equipped.values()]

        if not sellable_items:
            self.update_game_log("You have no sellable items in your inventory.")
            self._add_back_button(lambda: self.show_shop_menu(display_items=False)) # Back to main shop
            return

        self.update_game_log("Select an item to sell:")
        for i, item in enumerate(sellable_items):
            sell_price = math.floor(item.cost * NotRouge_game_core.SELL_PRICE_MULTIPLIER)
            item_desc = f"{i+1}. {item.name} (Type: {item.item_type}) - Sell for: {sell_price} gold"
            self.update_game_log(item_desc)
            
            button = QPushButton(f"Sell {item.name} ({sell_price}g)")
            button.clicked.connect(lambda _, itm=item: self._sell_item_action(itm))
            button.setStyleSheet("color: white;") # Set button text color to white
            self.button_layout.addWidget(button)
            button.show()

        self._add_back_button(lambda: self.show_shop_menu(display_items=False)) # Back to main shop

    def _sell_item_action(self, item_to_sell):
        reply = QMessageBox.question(self, 'Confirm Sale', 
                                    f"Are you sure you want to sell {item_to_sell.name} for {math.floor(item_to_sell.cost * NotRouge_game_core.SELL_PRICE_MULTIPLIER)} gold?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            sell_price = math.floor(item_to_sell.cost * NotRouge_game_core.SELL_PRICE_MULTIPLIER)
            self.player.gold += sell_price
            self.player.inventory.remove(item_to_sell)
            self.update_game_log(f"You sold {item_to_sell.name} for {sell_price} gold!")
            self.update_stats_display()
        else:
            self.update_game_log("Sale cancelled.")
        self._show_sell_items_menu() # Refresh sell menu


    # --- Inventory Menu Handling ---
    def show_inventory_menu(self):
        self.set_button_visibility("none")
        self.update_game_log("\n--- Inventory Management ---")
        if not self.player.inventory:
            self.update_game_log("Your inventory is empty.")
            self._add_back_button(self.show_town_menu)
            return

        self.update_game_log("Select an item to use/equip or throw away:")
        for i, item in enumerate(self.player.inventory):
            item_desc = f"{i+1}. {item.name} ({item.item_type})"
            if item.attack_bonus: item_desc += f" | ATK: +{item.attack_bonus}"
            if item.defense_bonus: item_desc += f" | DEF: +{item.defense_bonus}"
            if item.health_bonus: item_desc += f" | HP: +{item.health_bonus}"
            if item.heal_amount: item_desc += f" | Heals: {item.heal_amount}"
            self.update_game_log(item_desc)
            
            button_text = f"Use {item.name}" if item.item_type == "consumable" else f"Equip {item.name}"
            button = QPushButton(button_text)
            button.clicked.connect(lambda _, itm=item: self._handle_inventory_item_action(itm))
            button.setStyleSheet("color: white;") # Set button text color to white
            self.button_layout.addWidget(button)
            button.show()

            # Add throw away button for each item
            throw_button = QPushButton(f"Throw Away {item.name}")
            throw_button.clicked.connect(lambda _, itm=item: self._throw_away_item_action(itm))
            throw_button.setStyleSheet("color: white;") # Set button text color to white
            self.button_layout.addWidget(throw_button)
            throw_button.show()

        self._add_back_button(self.show_town_menu)

    def _handle_inventory_item_action(self, chosen_item):
        if chosen_item.item_type == "consumable":
            if chosen_item.heal_amount > 0:
                self.player.heal(chosen_item.heal_amount, self.update_game_log)
                self.player.inventory.remove(chosen_item)
                self.update_game_log(f"You used a {chosen_item.name}.")
            else:
                self.update_game_log("This item cannot be used.")
        else: # Equipable item
            self.player.equip_item(chosen_item, self.update_game_log)
            self.update_game_log(f"You equipped {chosen_item.name}.")
        self.show_inventory_menu() # Refresh inventory display

    def _throw_away_item_action(self, item_to_throw):
        # Prevent throwing away equipped items directly
        if item_to_throw in self.player.equipped.values():
            self.update_game_log(f"You cannot throw away {item_to_throw.name} while it is equipped. Unequip it first.")
            return

        reply = QMessageBox.question(self, 'Confirm Discard', 
                                    f"Are you sure you want to throw away {item_to_throw.name}? This cannot be undone!",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.player.inventory.remove(item_to_throw)
            self.update_game_log(f"You threw away {item_to_throw.name}.")
        else:
            self.update_game_log("Discard cancelled.")
        self.show_inventory_menu() # Refresh inventory display


    def _add_back_button(self, callback):
        back_button = QPushButton("Back")
        back_button.clicked.connect(callback)
        back_button.setStyleSheet("color: white;") # Set button text color to white
        self.button_layout.addWidget(back_button)
        back_button.show()


    # --- Dungeon Handling ---
    def _start_dungeon(self):
        if not NotRouge_game_core.DUNGEON_ENEMIES:
            self.update_game_log("The dungeon seems eerily quiet... (No enemies loaded).")
            self.show_town_menu()
            return
        self.update_game_log("You enter the dark and winding dungeon...")
        self.dungeon_room_count = 0
        self.max_dungeon_rooms = random.randint(3, 7)
        self._dungeon_next_room()

    def _dungeon_next_room(self):
        if self.player.current_health <= 0:
            NotRouge_game_core.handle_death(self.player, self.update_game_log)
            self.show_town_menu() # After death, return to town
            return

        if self.dungeon_room_count >= self.max_dungeon_rooms:
            self.update_game_log("You have cleared this section of the dungeon! You return to town.")
            self.show_town_menu()
            return

        self.dungeon_room_count += 1
        self.update_game_log(f"\n--- Dungeon Depth: {self.dungeon_room_count}/{self.max_dungeon_rooms} ---")
        self.update_game_log("You explore deeper...")
        
        encounter_type = random.choices(["combat", "nothing", "treasure", "healing"], weights=[0.6, 0.2, 0.15, 0.05], k=1)[0]

        if encounter_type == "combat":
            enemy_template = random.choice(NotRouge_game_core.DUNGEON_ENEMIES)
            self.current_enemy = NotRouge_game_core.Enemy(enemy_template.name, enemy_template.health_full, enemy_template.attack,
                                       enemy_template.defense, enemy_template.gold_drop, enemy_template.exp_drop)
            self.update_game_log(f"A wild {self.current_enemy.name} appears!")
            self._start_combat()
        elif encounter_type == "treasure":
            gold_found = random.randint(20, 100)
            self.player.gold += gold_found
            self.update_game_log(f"You found a hidden chest with {gold_found} gold!")
            self.update_stats_display()
            self._add_continue_dungeon_button()
        elif encounter_type == "healing":
            heal_amount = random.randint(20, 60)
            self.player.heal(heal_amount, self.update_game_log)
            self.update_game_log(f"You found a refreshing spring and healed {heal_amount} health!")
            self.update_stats_display()
            self._add_continue_dungeon_button()
        else: # "nothing"
            self.update_game_log("You found nothing of interest in this area.")
            self._add_continue_dungeon_button()

    def _add_continue_dungeon_button(self):
        self.set_button_visibility("none")
        continue_button = QPushButton("Continue Exploring")
        continue_button.clicked.connect(self._dungeon_next_room)
        continue_button.setStyleSheet("color: white;") # Set button text color to white
        self.button_layout.addWidget(continue_button)
        continue_button.show()

        retreat_button = QPushButton("Retreat to Town")
        retreat_button.clicked.connect(self.show_town_menu)
        retreat_button.setStyleSheet("color: white;") # Set button text color to white
        self.button_layout.addWidget(retreat_button)
        retreat_button.show()


    # --- Combat Handling ---
    def _start_combat(self):
        self.set_button_visibility("combat")
        self.update_game_log(f"--- Combat: {self.player.name} vs {self.current_enemy.name} ---")
        self.update_game_log(f"{self.player.name} HP: {self.player.current_health}/{self.player.max_health} | ATK: {self.player.attack} | DEF: {self.player.defense}")
        self.update_game_log(f"{self.current_enemy.name} HP: {self.current_enemy.health}/{self.current_enemy.health_full} | ATK: {self.current_enemy.attack} | DEF: {self.current_enemy.defense}")
        self.update_game_log("What will you do?")


    def _combat_action(self, action_type):
        if self.player.current_health <= 0 or self.current_enemy.health <= 0:
            return # Combat already over

        self.auto_attack_timer.stop() # Stop auto-attack if a manual action is chosen

        if action_type == "attack":
            self._perform_player_attack()
            if self.current_enemy and self.current_enemy.health > 0: # Check if enemy still alive after player's attack
                self._perform_enemy_attack()
            self._check_combat_end()
        elif action_type == "use_item":
            self._show_combat_item_menu()
        elif action_type == "flee":
            self._perform_flee_attempt()
            self._check_combat_end()
        elif action_type == "auto_attack":
            self.update_game_log("Initiating auto-attack...")
            self._auto_attack_turn() # Start immediately
            if self.player.current_health > 1 and self.current_enemy and self.current_enemy.health > 0:
                 self.auto_attack_timer.start(100) # Faster turns in auto-attack


    def _perform_player_attack(self):
        player_damage = max(1, self.player.attack + random.randint(-5, 5))
        enemy_dead = self.current_enemy.take_damage(player_damage, self.update_game_log)
        self.update_game_log(f"You hit the {self.current_enemy.name} for {player_damage} damage!")
        if enemy_dead:
            self.update_game_log(f"You defeated the {self.current_enemy.name}!")
            self.player.gold += self.current_enemy.gold_drop
            self.player.gain_exp(self.current_enemy.exp_drop, self.update_game_log)
            self.update_game_log(f"You gained {self.current_enemy.gold_drop} gold and {self.current_enemy.exp_drop} experience.")
            self.current_enemy = None # Mark enemy as defeated

    def _perform_enemy_attack(self):
        if self.current_enemy and self.current_enemy.health > 0:
            enemy_damage = max(1, self.current_enemy.attack + random.randint(-3, 3))
            player_dead = self.player.take_damage(enemy_damage, self.update_game_log)
            self.update_game_log(f"The {self.current_enemy.name} hits you for {enemy_damage} damage!")
            if player_dead:
                self.current_enemy = None # Player died, combat ends

    def _check_combat_end(self):
        self.update_stats_display() # Update player stats after each action
        if self.player.current_health <= 0:
            self.auto_attack_timer.stop()
            NotRouge_game_core.handle_death(self.player, self.update_game_log) # Pass log function
            # show_town_menu is now called by _handle_player_death
        elif self.current_enemy is None: # Enemy defeated
            self.auto_attack_timer.stop()
            self._add_continue_dungeon_button() # Back to dungeon flow
        else:
            # If combat not ended, display current state for next turn (unless auto-attacking)
            self.update_game_log(f"--- Combat: {self.player.name} HP: {self.player.current_health}/{self.player.max_health} vs {self.current_enemy.name} HP: {self.current_enemy.health}/{self.current_enemy.health_full} ---")
            self.update_game_log("What will you do next?")


    def _show_combat_item_menu(self):
        self.set_button_visibility("none")
        consumables = [item for item in self.player.inventory if item.item_type == "consumable"]
        if not consumables:
            self.update_game_log("You have no usable items.")
            self._start_combat() # Return to combat menu
            return

        self.update_game_log("\n--- Your Consumable Items ---")
        for i, item in enumerate(consumables):
            self.update_game_log(f"{i+1}. {item.name} (Heals: {item.heal_amount})")
            button = QPushButton(f"Use {item.name} (Heals: {item.heal_amount})")
            button.clicked.connect(lambda _, itm=item: self._use_combat_item(itm))
            button.setStyleSheet("color: white;") # Set button text color to white
            self.button_layout.addWidget(button)
            button.show()
        
        back_button = QPushButton("Back to Combat")
        back_button.clicked.connect(self._start_combat)
        back_button.setStyleSheet("color: white;") # Set button text color to white
        self.button_layout.addWidget(back_button)
        back_button.show()

    def _use_combat_item(self, item_to_use):
        if item_to_use.heal_amount > 0:
            self.player.heal(item_to_use.heal_amount, self.update_game_log)
            self.player.inventory.remove(item_to_use)
            self.update_game_log(f"You used a {item_to_use.name}.")
        else:
            self.update_game_log("This item cannot be used.")
        self._start_combat() # Return to combat menu after using item


    def _perform_flee_attempt(self):
        if random.random() < 0.5:
            self.update_game_log("You successfully fled from combat!")
            self.current_enemy = None # End combat
        else:
            self.update_game_log("You failed to flee!")
            self._perform_enemy_attack() # Enemy gets a free hit if flee fails

    def _auto_attack_turn(self):
        # Check conditions to stop auto-attack
        if self.player.current_health <= 1:
            self.update_game_log("\nYour health is critically low (1 HP remaining)! Auto-attack stopped.")
            self.auto_attack_timer.stop()
            self._start_combat() # Return to manual combat options
            return
        if self.current_enemy is None or self.current_enemy.health <= 0:
            self.update_game_log("Enemy defeated.")
            self.auto_attack_timer.stop()
            self._add_continue_dungeon_button() # Enemy defeated, move on
            return

        # Player attacks
        self._perform_player_attack()
        
        # Check if enemy is defeated after player's attack
        if self.current_enemy is None or self.current_enemy.health <= 0:
            self.auto_attack_timer.stop()
            self._add_continue_dungeon_button()
            return

        # Enemy attacks
        self._perform_enemy_attack()

        # Re-check player health after enemy attack
        if self.player.current_health <= 0:
            self.auto_attack_timer.stop()
            NotRouge_game_core.handle_death(self.player, self.update_game_log) # Pass log function
            # show_town_menu is now called by handle_death from NotRouge_game_core
            return # Exit this auto-attack turn as player is dead

        # Update combat display (optional for auto-attack but useful for feedback)
        if self.current_enemy: # Still in combat
             self.update_game_log(f"--- Auto-Combat: {self.player.name} HP: {self.player.current_health}/{self.player.max_health} vs {self.current_enemy.name} HP: {self.current_enemy.health}/{self.current_enemy.health_full} ---")


# --- Main Application Entry Point ---
if __name__ == "__main__":
    app = QApplication([])
    game_window = GameWindow()
    game_window.show()
    app.exec_()

import os
import json
import random
import math

# --- Game Constants ---
# These are core game constants, not UI specific
STARTING_GOLD = 100
STARTING_HEALTH = 100
STARTING_ATTACK = 10
STARTING_DEFENSE = 5
BASE_EXP_TO_LEVEL = 100
EXP_PER_LEVEL_MULTIPLIER = 1.5
SELL_PRICE_MULTIPLIER = 0.5 # Items sell for half their cost

# --- Helper Functions (Core Logic) ---

def calculate_level_up_exp(level):
    """Calculates the experience needed for the next level."""
    return math.ceil(BASE_EXP_TO_LEVEL * (EXP_PER_LEVEL_MULTIPLIER ** (level - 1)))

# --- Game Classes ---

class Player:
    """Represents the player character."""
    def __init__(self, name="Hero"):
        self.name = name
        self.level = 1
        self.experience = 0
        self.max_health = STARTING_HEALTH
        self.current_health = STARTING_HEALTH
        self.attack = STARTING_ATTACK
        self.defense = STARTING_DEFENSE
        self.gold = STARTING_GOLD
        self.inventory = []  # List of Item objects
        self.equipped = {
            "weapon": None,
            "armor": None,
            "accessory": None
        }

    def gain_exp(self, exp_gained, log_function):
        """Adds experience to the player and handles level ups."""
        log_function(f"You gained {exp_gained} experience!")
        self.experience += exp_gained
        while self.experience >= calculate_level_up_exp(self.level):
            self.experience -= calculate_level_up_exp(self.level)
            self.level_up(log_function)

    def level_up(self, log_function):
        """Increases player stats upon leveling up."""
        self.level += 1
        self.max_health += 15
        self.current_health = self.max_health # Fully heal on level up
        self.attack += 3
        self.defense += 2
        log_function(f"\n*** You leveled up to Level {self.level}! ***")
        log_function("Health +15, Attack +3, Defense +2.")
        log_function("You feel stronger!")

    def take_damage(self, damage, log_function):
        """Reduces player health based on damage taken and defense."""
        effective_damage = max(0, damage - self.defense)
        self.current_health -= effective_damage
        log_function(f"You took {effective_damage} damage!")
        if self.current_health <= 0:
            self.current_health = 0
            return True # Player is dead
        return False # Player is still alive

    def heal(self, amount, log_function):
        """Heals the player, not exceeding max health."""
        old_health = self.current_health
        self.current_health = min(self.max_health, self.current_health + amount)
        healed_amount = self.current_health - old_health
        log_function(f"You healed {healed_amount} health. Current health: {self.current_health}/{self.max_health}")

    def equip_item(self, item, log_function):
        """Equips an item, un-equipping previous item if necessary."""
        if item.item_type in self.equipped:
            old_item = self.equipped[item.item_type]
            if old_item:
                # Unequip old item's stats
                self.attack -= old_item.attack_bonus
                self.defense -= old_item.defense_bonus
                self.max_health -= old_item.health_bonus
                self.current_health = min(self.current_health, self.max_health) # Adjust current health if max decreased
                self.inventory.append(old_item) # Move old item back to inventory
                log_function(f"Unequipped {old_item.name}.")

            # Equip new item
            self.equipped[item.item_type] = item
            self.attack += item.attack_bonus
            self.defense += item.defense_bonus
            self.max_health += item.health_bonus
            self.current_health = min(self.current_health, self.max_health) # Ensure current health doesn't exceed new max
            self.inventory.remove(item)
            log_function(f"Equipped {item.name}.")
        else:
            log_function(f"Cannot equip {item.name}. It's not a recognized equipment type.")

class Item:
    """Represents an item in the game."""
    def __init__(self, name, item_type, cost, attack_bonus=0, defense_bonus=0, health_bonus=0, heal_amount=0):
        self.name = name
        self.item_type = item_type # e.g., "weapon", "armor", "accessory", "consumable"
        self.cost = cost
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.health_bonus = health_bonus
        self.heal_amount = heal_amount

    def to_dict(self):
        """Converts item object to a dictionary for saving."""
        return {
            "name": self.name,
            "item_type": self.item_type,
            "cost": self.cost,
            "attack_bonus": self.attack_bonus,
            "defense_bonus": self.defense_bonus,
            "health_bonus": self.health_bonus,
            "heal_amount": self.heal_amount
        }

    @staticmethod
    def from_dict(data):
        """Creates an Item object from a dictionary."""
        return Item(
            name=data["name"],
            item_type=data["item_type"],
            cost=data["cost"],
            attack_bonus=data.get("attack_bonus", 0),
            defense_bonus=data.get("defense_bonus", 0),
            health_bonus=data.get("health_bonus", 0),
            heal_amount=data.get("heal_amount", 0)
        )

class Enemy:
    """Represents an enemy character."""
    def __init__(self, name, health, attack, defense, gold_drop, exp_drop):
        self.name = name
        self.health = health
        self.attack = attack
        self.defense = defense
        self.gold_drop = gold_drop
        self.exp_drop = exp_drop
        self.health_full = health # Store original health for combat display

    def take_damage(self, damage, log_function):
        """Reduces enemy health based on damage taken and defense."""
        effective_damage = max(0, damage - self.defense)
        self.health -= effective_damage
        log_function(f"The {self.name} took {effective_damage} damage!")
        if self.health <= 0:
            self.health = 0
            return True # Enemy is dead
        return False # Enemy is still alive

# --- Data Loading Functions ---

def load_items_from_file(filename, log_function):
    """Loads Item objects from a text file."""
    items = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): # Skip empty lines and comments
                    continue
                try:
                    parts = line.split('|')
                    name = parts[0]
                    item_type = parts[1]
                    cost = int(parts[2])
                    attack_bonus = int(parts[3]) if len(parts) > 3 and parts[3].strip().isdigit() else 0
                    defense_bonus = int(parts[4]) if len(parts) > 4 and parts[4].strip().isdigit() else 0
                    health_bonus = int(parts[5]) if len(parts) > 5 and parts[5].strip().isdigit() else 0
                    heal_amount = int(parts[6]) if len(parts) > 6 and parts[6].strip().isdigit() else 0
                    items.append(Item(name, item_type, cost, attack_bonus, defense_bonus, health_bonus, heal_amount))
                except ValueError as ve:
                    log_function(f"Error parsing item line '{line}': {ve}. Skipping.")
                except IndexError as ie:
                    log_function(f"Error: Not enough fields in item line '{line}'. Expected at least 3, got {len(parts)}. Skipping.")
        log_function(f"Loaded {len(items)} items from {filename}.")
    except FileNotFoundError:
        log_function(f"Error: {filename} not found. Ensure the file is in the same directory as the game script.")
    except Exception as e:
        log_function(f"An unexpected error occurred while loading items: {e}")
    return items

def load_enemies_from_file(filename, log_function):
    """Loads Enemy objects from a text file."""
    enemies = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): # Skip empty lines and comments
                    continue
                try:
                    parts = line.split('|')
                    name = parts[0]
                    health = int(parts[1])
                    attack = int(parts[2])
                    defense = int(parts[3])
                    gold_drop = int(parts[4])
                    exp_drop = int(parts[5])
                    enemies.append(Enemy(name, health, attack, defense, gold_drop, exp_drop))
                except ValueError as ve:
                    log_function(f"Error parsing enemy line '{line}': {ve}. Skipping.")
                except IndexError as ie:
                    log_function(f"Error: Not enough fields in enemy line '{line}'. Expected 6, got {len(parts)}. Skipping.")
        log_function(f"Loaded {len(enemies)} enemies from {filename}.")
    except FileNotFoundError:
        log_function(f"Error: {filename} not found. Ensure the file is in the same directory as the game script.")
    except Exception as e:
        log_function(f"An unexpected error occurred while loading enemies: {e}")
    return enemies

# --- Game Persistence ---

def save_game(player, save_file, log_function):
    """Saves the current game state to a JSON file."""
    try:
        player_data = {
            "name": player.name,
            "level": player.level,
            "experience": player.experience,
            "max_health": player.max_health,
            "current_health": player.current_health,
            "attack": player.attack,
            "defense": player.defense,
            "gold": player.gold,
            "inventory": [item.to_dict() for item in player.inventory],
            "equipped": {
                slot: item.to_dict() if item else None
                for slot, item in player.equipped.items()
            }
        }
        with open(save_file, "w") as f:
            json.dump(player_data, f, indent=4)
        log_function("Game saved successfully!")
    except Exception as e:
        log_function(f"Error saving game: {e}")

def load_game(save_file, log_function):
    """Loads a game state from a JSON file."""
    if not os.path.exists(save_file):
        log_function("No save file found.")
        return None
    try:
        with open(save_file, "r") as f:
            player_data = json.load(f)
        
        player = Player(player_data["name"])
        player.level = player_data["level"]
        player.experience = player_data["experience"]
        player.max_health = player_data["max_health"]
        player.current_health = player_data["current_health"]
        player.attack = player_data["attack"]
        player.defense = player_data["defense"]
        player.gold = player_data["gold"]
        player.inventory = [Item.from_dict(d) for d in player_data["inventory"]]
        player.equipped = {
            slot: Item.from_dict(d) if d else None
            for slot, d in player_data["equipped"].items()
        }
        log_function("Game loaded successfully!")
        return player
    except Exception as e:
        log_function(f"Error loading game: {e}")
        return None

def handle_death(player, log_function):
    """Handles player death, applying persistence rules."""
    log_function("You have been defeated!")
    log_function("But your adventure doesn't end here...")

    # Apply persistence rules
    player.gold = math.floor(player.gold / 2)
    log_function(f"You kept half your gold: {player.gold} gold remaining.")

    kept_equipment = None
    all_equipment = list(player.equipped.values()) + player.inventory
    equippable_items = [item for item in all_equipment if item and item.item_type != "consumable"]

    # Reset player stats to base first, then apply kept equipment bonuses
    player.attack = STARTING_ATTACK
    player.defense = STARTING_DEFENSE
    player.max_health = STARTING_HEALTH
    player.current_health = STARTING_HEALTH # Start fresh

    if equippable_items:
        kept_equipment = random.choice(equippable_items)
        # Clear inventory and equipped items before adding the kept item
        player.inventory = []
        player.equipped = {"weapon": None, "armor": None, "accessory": None}

        # Add the kept item to inventory and re-equip if it's an equipable type
        if kept_equipment.item_type in ["weapon", "armor", "accessory"]:
            player.equipped[kept_equipment.item_type] = kept_equipment
            # Apply bonuses from the re-equipped item
            player.attack += kept_equipment.attack_bonus
            player.defense += kept_equipment.defense_bonus
            player.max_health += kept_equipment.health_bonus
            player.current_health = player.max_health # Adjust current health to new max
        else: # If kept item is a consumable, just add it to inventory
            player.inventory.append(kept_equipment)

        log_function(f"You managed to keep one random piece of equipment: {kept_equipment.name}.")
    else:
        log_function("You had no equipment to keep.")

    # Calculate levels to keep, ensuring it's at least level 1
    levels_gained = player.level - 1
    levels_to_keep = math.floor(levels_gained / 2)
    player.level = 1 + levels_to_keep
    player.experience = 0 # Reset experience for current level

    log_function(f"You kept half your gained levels. You are now Level {player.level}.")
    player.current_health = player.max_health # Full heal for new start

    save_game(player, "NotRouge_save.json", log_function) # Save the 'resurrected' state
    log_function("You've been revived and returned to town!")


# These global lists will be populated when the module is imported
# The UI launchers will import these populated lists
SHOP_ITEMS = []
DUNGEON_ENEMIES = []

# Self-initialize when the module is loaded
# This is a basic logger for initial loading messages if module is imported directly
def _default_logger(message):
    print(f"[CORE_INIT] {message}")

# Load data on module import
# These paths are relative to where the script executing the import is run.
# For consistency, it's assumed items.txt and enemies.txt are in the same directory as NotRouge_game_core.py or the main launcher.
_items_path = os.path.join(os.path.dirname(__file__), "NotRouge_Items.txt")
_enemies_path = os.path.join(os.path.dirname(__file__), "NotRouge_Enemies.txt")

SHOP_ITEMS = load_items_from_file(_items_path, _default_logger)
DUNGEON_ENEMIES = load_enemies_from_file(_enemies_path, _default_logger)

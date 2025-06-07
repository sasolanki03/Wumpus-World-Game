#!/usr/bin/env python3
import pygame
import sys
import os
import importlib

# Import our menu module
import menu_mod

# Function to run the game
def run_wumpus_game(settings):
    # Import the game module
    import wumpus_world_with_bg_fixed as wumpus_game
    
    # Print the settings being used
    print(f"Starting game with settings: {settings}")
    
    # Create and run the game
    # Note: The original game doesn't accept settings, so we'll just run it as is for now
    game = wumpus_game.WumpusWorld()
    
    # Run the game loop from the main function
    wumpus_game.main()

def main():
    # First show the menu
    settings = menu_mod.show_menu()
    
    if settings:  # If user didn't quit from menu
        # User chose to start the game with the selected settings
        run_wumpus_game(settings)

if __name__ == "__main__":
    main()

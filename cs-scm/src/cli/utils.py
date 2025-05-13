"""
Utility functions for the CLI interface.
"""

import os
import sys
import termios
import tty

# ANSI color codes
ORANGE = "\033[38;2;228;94;39m"  # #e45e27
WHITE = "\033[37m"
BOLD = "\033[1m"
RESET = "\033[0m"
ORANGE_BG = "\033[48;2;228;94;39m"
BLACK = "\033[30m"

def print_header(text):
    """Print a header with the orange theme."""
    print(f"\n{ORANGE}{BOLD}{text}{RESET}")
    print(f"{ORANGE}{'-' * len(text)}{RESET}")

def get_key_press():
    """Get a single keypress from the user."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def select_from_list(items, display_fn, prompt="Select an item:"):
    """
    Display a list of items with arrow key navigation.
    
    Args:
        items (list): List of items to choose from
        display_fn (callable): Function to convert an item to display text
        prompt (str): Prompt to show above the list
        
    Returns:
        The selected item or None if ESC or q was pressed
    """
    if not items:
        return None
        
    selection = 0
    
    while True:
        # Clear the screen
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Print the prompt
        print_header(prompt)
        
        # Print the items
        for i, item in enumerate(items):
            if i == selection:
                print(f"{ORANGE_BG}{BLACK} ▶ {display_fn(item)}{RESET}")
            else:
                print(f"   {display_fn(item)}")
        
        print("\nUse ↑/↓ to navigate, Enter to select, q to quit")
        
        # Get key press
        key = get_key_press()
        
        if key == "\x1b":  # Escape sequence
            # Read the rest of the escape sequence
            next1 = sys.stdin.read(1)
            if next1 == "[":
                next2 = sys.stdin.read(1)
                if next2 == "A":  # Up arrow
                    selection = (selection - 1) % len(items)
                elif next2 == "B":  # Down arrow
                    selection = (selection + 1) % len(items)
        elif key == "\r" or key == "\n":  # Enter
            return items[selection]
        elif key.lower() == "q":  # Quit
            return None
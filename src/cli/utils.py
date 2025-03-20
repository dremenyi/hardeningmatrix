"""
Smartsheet Compliance Analyzer - CLI Utility Functions

This module provides utility functions for enhancing the command-line interface
experience. It includes terminal color formatting, interactive selection menus,
and keyboard input handling for a more user-friendly CLI experience.

Key Components:
- ANSI color code definitions for consistent styling
- Header formatting for visual organization
- Raw terminal input handling for interactive menus
- Interactive list selection with keyboard navigation

These utilities create a polished, interactive command-line experience
that makes the Smartsheet Compliance Analyzer tool more accessible and
easier to use in terminal environments.
"""

import os
import sys
import termios
import tty

# ANSI color and formatting codes
# These codes control text appearance in compatible terminals
ORANGE = "\033[38;2;228;94;39m"  # Custom RGB orange (#e45e27) - primary theme color
WHITE = "\033[37m"               # White text
BOLD = "\033[1m"                 # Bold text formatting
RESET = "\033[0m"                # Reset all formatting
ORANGE_BG = "\033[48;2;228;94;39m" # Orange background (same RGB value as text)
BLACK = "\033[30m"               # Black text (for use with colored backgrounds)


def print_header(text):
    """
    Print a formatted header with the orange theme.
    
    Creates a visually distinct section header with the application's
    orange theme color and a separator line underneath. Used to clearly
    separate different stages of the application workflow.
    
    Args:
        text (str): The header text to display
        
    Example:
        >>> print_header("Loading Compliance Scan Results")
        
        Loading Compliance Scan Results
        ------------------------------
    """
    print(f"\n{ORANGE}{BOLD}{text}{RESET}")
    print(f"{ORANGE}{'-' * len(text)}{RESET}")


def get_key_press():
    """
    Get a single keypress from the user without requiring Enter.
    
    This function temporarily sets the terminal to raw mode to read
    a single character input without line buffering. This allows for
    interactive menus where keypresses have immediate effect.
    
    Returns:
        str: A single character representing the key pressed
        
    Note:
        This function works only in Unix-like environments with termios support.
        For Windows compatibility, consider using msvcrt module instead.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        # Set terminal to raw mode to read single keypresses
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        # Always restore terminal to its original state
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def select_from_list(items, display_fn, prompt="Select an item:"):
    """
    Display an interactive list of items with arrow key navigation.
    
    Creates a full-screen menu for selecting from a list of items.
    The user can navigate using arrow keys and select with Enter,
    or exit without selection using q or ESC.
    
    Args:
        items (list): List of items to choose from
        display_fn (callable): Function to convert an item to display text
                              This allows flexible formatting of different item types
        prompt (str): Prompt to show above the list
        
    Returns:
        Any: The selected item or None if ESC or q was pressed
        
    Example:
        >>> workspaces = client.search_workspaces("SCM Program")
        >>> selected = select_from_list(
        ...     workspaces,
        ...     lambda w: f"{w['name']} ({w['id']})",
        ...     "Select a workspace:"
        ... )
        >>> if selected:
        ...     print(f"You selected: {selected['name']}")
    """
    # Return None for empty lists
    if not items:
        return None
        
    selection = 0
    
    while True:
        # Clear the screen for a clean display
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Print the prompt as a header
        print_header(prompt)
        
        # Print the list of items with the current selection highlighted
        for i, item in enumerate(items):
            if i == selection:
                # Highlighted item with orange background, black text, and arrow
                print(f"{ORANGE_BG}{BLACK} ▶ {display_fn(item)}{RESET}")
            else:
                # Regular item with indentation to align with highlighted items
                print(f"   {display_fn(item)}")
        
        # Print navigation instructions
        print("\nUse ↑/↓ to navigate, Enter to select, q to quit")
        
        # Get and process user input
        key = get_key_press()
        
        if key == "\x1b":  # Escape sequence for arrow keys
            # Read the rest of the escape sequence
            next1 = sys.stdin.read(1)
            if next1 == "[":
                next2 = sys.stdin.read(1)
                if next2 == "A":  # Up arrow
                    selection = (selection - 1) % len(items)  # Wrap around to bottom
                elif next2 == "B":  # Down arrow
                    selection = (selection + 1) % len(items)  # Wrap around to top
        elif key == "\r" or key == "\n":  # Enter key
            return items[selection]  # Return the selected item
        elif key.lower() == "q":  # q key for quit
            return None  # Return None to indicate cancellation
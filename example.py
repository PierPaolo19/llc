#!/usr/bin/env python3
"""
Example usage of the USDT Flasher Tool
"""

from usdt_flasher import USDTFlasher

def main():
    # Create a flasher with initial balance
    flasher = USDTFlasher(initial_balance=5000.0)
    
    print("🎯 USDT Flasher Tool Example\n")
    
    # Flash the initial balance
    print("Flashing initial balance...")
    flasher.flash_balance(duration=2)
    
    # Make some deposits
    print("\n💰 Making deposits...")
    flasher.deposit(1000)
    flasher.deposit(500)
    
    # Make a withdrawal
    print("\n💸 Making withdrawal...")
    flasher.withdraw(800)
    
    # Flash the new balance
    print("\nFlashing updated balance...")
    flasher.flash_balance(duration=2)
    
    # Show transaction history
    flasher.show_transaction_history()
    
    print(f"\n✅ Final Balance: ${flasher.balance:,.2f} USDT")

if __name__ == "__main__":
    main()

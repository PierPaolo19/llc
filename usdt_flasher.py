#!/usr/bin/env python3
"""
USDT Flasher Tool
A tool to display USDT balance information with visual effects
"""

import time
import sys
import random
import argparse
from datetime import datetime

# ANSI color codes for terminal output
COLOR_GREEN = '\033[92m'
COLOR_YELLOW = '\033[93m'
COLOR_CYAN = '\033[96m'
COLOR_MAGENTA = '\033[95m'
COLOR_RESET = '\033[0m'

# Flash animation settings
FLASH_INTERVAL = 0.3  # seconds between color changes


class USDTFlasher:
    """Main class for the USDT Flasher tool"""
    
    def __init__(self, initial_balance=0.0):
        self.balance = initial_balance
        self.transaction_history = []
        
    def flash_balance(self, duration=3):
        """Display the balance with a flashing effect"""
        print("\n" + "="*50)
        print("USDT BALANCE FLASHER")
        print("="*50)
        
        end_time = time.time() + duration
        colors = [COLOR_GREEN, COLOR_YELLOW, COLOR_CYAN, COLOR_MAGENTA]
        
        while time.time() < end_time:
            color = random.choice(colors)
            sys.stdout.write(f"\r{color}💰 USDT Balance: ${self.balance:,.2f} 💰{COLOR_RESET}")
            sys.stdout.flush()
            time.sleep(FLASH_INTERVAL)
        
        print(f"\n{COLOR_RESET}")
        print("="*50 + "\n")
    
    def add_transaction(self, amount, transaction_type="deposit"):
        """Add a transaction to the history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transaction = {
            "timestamp": timestamp,
            "type": transaction_type,
            "amount": amount,
            "balance_after": self.balance
        }
        self.transaction_history.append(transaction)
    
    def deposit(self, amount):
        """Deposit USDT"""
        if amount <= 0:
            print("❌ Error: Deposit amount must be positive")
            return False
        
        self.balance += amount
        self.add_transaction(amount, "deposit")
        print(f"✅ Deposited ${amount:,.2f} USDT")
        return True
    
    def withdraw(self, amount):
        """Withdraw USDT"""
        if amount <= 0:
            print("❌ Error: Withdrawal amount must be positive")
            return False
        
        if amount > self.balance:
            print("❌ Error: Insufficient balance")
            return False
        
        self.balance -= amount
        self.add_transaction(amount, "withdrawal")
        print(f"✅ Withdrew ${amount:,.2f} USDT")
        return True
    
    def show_transaction_history(self):
        """Display transaction history"""
        print("\n" + "="*50)
        print("TRANSACTION HISTORY")
        print("="*50)
        
        if not self.transaction_history:
            print("No transactions yet.")
        else:
            for i, tx in enumerate(self.transaction_history, 1):
                sign = "+" if tx["type"] == "deposit" else "-"
                print(f"{i}. [{tx['timestamp']}] {tx['type'].upper()}: {sign}${tx['amount']:,.2f} | Balance: ${tx['balance_after']:,.2f}")
        
        print("="*50 + "\n")
    
    def show_menu(self):
        """Display the main menu"""
        print("\n" + "="*50)
        print("USDT FLASHER TOOL - MAIN MENU")
        print("="*50)
        print("1. Flash Balance")
        print("2. Deposit USDT")
        print("3. Withdraw USDT")
        print("4. View Transaction History")
        print("5. Check Balance")
        print("6. Exit")
        print("="*50)
    
    def run_interactive(self):
        """Run the interactive menu"""
        print("\n🌟 Welcome to USDT Flasher Tool! 🌟")
        
        while True:
            self.show_menu()
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                self.flash_balance()
            elif choice == "2":
                try:
                    amount = float(input("Enter deposit amount: $"))
                    self.deposit(amount)
                except ValueError:
                    print("❌ Error: Invalid amount")
            elif choice == "3":
                try:
                    amount = float(input("Enter withdrawal amount: $"))
                    self.withdraw(amount)
                except ValueError:
                    print("❌ Error: Invalid amount")
            elif choice == "4":
                self.show_transaction_history()
            elif choice == "5":
                print(f"\n💰 Current Balance: ${self.balance:,.2f} USDT")
            elif choice == "6":
                print("\n👋 Thank you for using USDT Flasher Tool!")
                break
            else:
                print("❌ Invalid choice. Please try again.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="USDT Flasher Tool")
    parser.add_argument("--balance", type=float, default=1000.0,
                       help="Initial balance (default: 1000.0)")
    parser.add_argument("--flash", action="store_true",
                       help="Flash the balance once and exit")
    parser.add_argument("--duration", type=int, default=3,
                       help="Duration of flash effect in seconds (default: 3)")
    
    args = parser.parse_args()
    
    flasher = USDTFlasher(initial_balance=args.balance)
    
    if args.flash:
        flasher.flash_balance(duration=args.duration)
    else:
        flasher.run_interactive()


if __name__ == "__main__":
    main()

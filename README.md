# USDT Flasher Tool

A Python-based tool to display and manage USDT (Tether) balance information with visual effects.

## Features

- 💰 **Flash Balance Display**: Shows your USDT balance with colorful animated effects
- 💵 **Deposit & Withdraw**: Simulate USDT deposits and withdrawals
- 📊 **Transaction History**: Track all your transactions with timestamps
- 🎨 **Interactive Menu**: Easy-to-use command-line interface
- ⚡ **Fast & Lightweight**: No external dependencies required

## Installation

1. Clone the repository:
```bash
git clone https://github.com/PierPaolo19/llc.git
cd llc
```

2. Make the script executable (optional):
```bash
chmod +x usdt_flasher.py
```

## Usage

### Interactive Mode

Run the tool in interactive mode to access all features:

```bash
python3 usdt_flasher.py
```

You can also specify an initial balance:

```bash
python3 usdt_flasher.py --balance 5000
```

### Flash Mode

Quickly flash your balance and exit:

```bash
python3 usdt_flasher.py --flash --balance 10000
```

Customize the flash duration (in seconds):

```bash
python3 usdt_flasher.py --flash --duration 5 --balance 10000
```

## Command-Line Arguments

- `--balance AMOUNT`: Set initial balance (default: 1000.0)
- `--flash`: Flash the balance once and exit
- `--duration SECONDS`: Duration of flash effect in seconds (default: 3)

## Interactive Menu Options

1. **Flash Balance**: Display balance with animated color effects
2. **Deposit USDT**: Add funds to your balance
3. **Withdraw USDT**: Remove funds from your balance
4. **View Transaction History**: See all past transactions
5. **Check Balance**: Display current balance
6. **Exit**: Close the application

## Examples

### Example 1: Start with custom balance
```bash
python3 usdt_flasher.py --balance 25000
```

### Example 2: Quick balance flash
```bash
python3 usdt_flasher.py --flash --balance 50000 --duration 5
```

### Example 3: Interactive session
```bash
python3 usdt_flasher.py
# Then use the menu to:
# - Deposit $500
# - Flash the balance
# - View transaction history
```

## Requirements

- Python 3.6 or higher
- No external dependencies (uses Python standard library only)

## Features in Detail

### Flash Balance
The flash balance feature displays your USDT balance with colorful animations that cycle through different colors (green, yellow, cyan, magenta) to create an eye-catching effect.

### Transaction Management
- **Deposits**: Adds to your balance and records the transaction
- **Withdrawals**: Deducts from your balance (checks for sufficient funds)
- **History**: Maintains a complete log of all transactions with timestamps

### Error Handling
- Validates all user inputs
- Prevents negative transactions
- Checks for sufficient balance before withdrawals
- Provides clear error messages

## License

This project is open source and available for educational purposes.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## Disclaimer

⚠️ This is a demonstration/educational tool. It does not interact with real cryptocurrency or blockchain networks. Do not use this for actual financial transactions.
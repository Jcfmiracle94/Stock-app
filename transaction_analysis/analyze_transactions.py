import csv
import os
from collections import defaultdict

# ==============================================================================
# SECTION 1: SETTINGS
# This part tells the computer WHERE your bank file is and how much money you started with.
# ==============================================================================

# This is the path to your bank's CSV file on your computer.
CSV_PATH = r"C:\Users\jcfmi\Downloads\_All_Transactions_.csv"

# This is the balance you had before any of these transactions happened.
STARTING_BALANCE = 3000.00

def parse_amount(amount_str):
    """
    CLEANER FUNCTION: 
    Takes a messy string like '$1,200.50' and turns it into a clean number like 1200.50.
    """
    if not amount_str:
        return 0.0
    # Remove quotes, '$', and commas so the computer can do math.
    clean_str = amount_str.replace('"', '').replace('$', '').replace(',', '')
    try:
        return float(clean_str)
    except ValueError:
        return 0.0

# ==============================================================================
# SECTION 2: THE ANALYSIS LOGIC
# This is the part that 'reads' your bank statement and does the math.
# ==============================================================================

def analyze_transactions():
    """
    THE ANALYZER:
    Opens your bank file, loops through every single row, and groups your spending.
    """
    # First, make sure the file actually exists!
    if not os.path.exists(CSV_PATH):
        print(f"Error: I couldn't find your file at {CSV_PATH}")
        return

    # We start with everything at zero.
    total_spent = 0
    total_paid = 0
    category_spending = defaultdict(float) # Groups spending by Category (e.g., 'Groceries')
    merchant_spending = defaultdict(float) # Groups spending by Merchant (e.g., 'Amazon')
    merchant_counts = defaultdict(int)      # Counts how many times you visited a store.

    # Open the CSV file and start reading.
    with open(CSV_PATH, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader) # Grab the first line (the column names).
        headers = [h.strip().replace('"', '') for h in headers] # Clean up the names.
        
        for row in reader:
            if not row: continue # Skip empty lines.
            
            # Map the row data to the column names so we can find things easily.
            data = dict(zip(headers, row))
            
            try:
                # Grab the Merchant Name, the Amount, and the Category.
                merchant = data.get('Transaction Merchant Name', 'Unknown').strip().replace('"', '')
                amount = parse_amount(data.get('Transaction Amount', '0'))
                category = data.get('Merchant Category Group Name', 'Other').strip().replace('"', '')

                # DO THE MATH:
                if amount > 0:
                    # Positive amounts mean you spent money.
                    total_spent += amount
                    category_spending[category] += amount
                    merchant_spending[merchant] += amount
                else:
                    # Negative amounts usually mean you paid off a card or got a refund.
                    total_paid += abs(amount)

                # COUNT YOUR HABITS:
                if merchant != "PAYMENT - THANK YOU":
                    merchant_counts[merchant] += 1
            except Exception as e:
                print(f"Skipping a row because of an error: {e}")

    # Calculate your final balance after all the spending and payments.
    current_balance = STARTING_BALANCE - total_spent + total_paid

    # SORT THE RESULTS: Put the biggest numbers at the top.
    sorted_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)
    sorted_merchants = sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)
    sorted_habits = sorted(merchant_counts.items(), key=lambda x: x[1], reverse=True)

    # ==============================================================================
    # SECTION 3: THE FINAL REPORT
    # This prints out everything the computer learned in a clean, easy-to-read way.
    # ==============================================================================

    print("="*40)
    print(" BANK TRANSACTION ANALYSIS REPORT ")
    print("="*40)
    print(f"Starting Balance: ${STARTING_BALANCE:,.2f}")
    print(f"Total Spent:      ${total_spent:,.2f}")
    print(f"Total Paid/Credit: ${total_paid:,.2f}")
    print(f"Current Balance:  ${current_balance:,.2f}")
    print("-" * 40)
    
    print("\nTOP SPENDING CATEGORIES:")
    for cat, amt in sorted_categories[:5]:
        print(f"- {cat}: ${amt:,.2f}")

    print("\nTOP MERCHANTS (BY AMOUNT):")
    for mer, amt in sorted_merchants[:5]:
        if mer != "Unknown":
            print(f"- {mer}: ${amt:,.2f}")

    print("\nSPENDING HABITS (MOST FREQUENT):")
    for mer, count in sorted_habits[:5]:
        print(f"- {mer}: {count} transactions")

    print("\n" + "="*40)
    
    # SIMPLE INSIGHTS:
    if sorted_categories:
        top_cat = sorted_categories[0][0]
        print(f"INSIGHT: Your biggest expense category is '{top_cat}'.")
    
    if sorted_habits:
        top_habit = sorted_habits[0][0]
        print(f"INSIGHT: Your most frequent merchant is '{top_habit}' ({sorted_habits[0][1]} times).")

# This starts the analysis when you run the script.
if __name__ == "__main__":
    analyze_transactions()

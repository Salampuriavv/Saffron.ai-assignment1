import json
from datetime import datetime
from collections import defaultdict
import numpy as np
from scipy.optimize import newton

def load_transactions(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d-%b-%Y")
    except ValueError:
        return None

def fifo_transaction_processing(transactions):
    portfolio = defaultdict(list)

    for transaction in transactions:
        folio = transaction['folio']
        isin = transaction['isin']
        units = float(transaction['trxnUnits'])
        price = float(transaction['purchasePrice'])
        transaction_date = parse_date(transaction['trxnDate'])
        
        key = (isin, folio)

        if units > 0:
            portfolio[key].append({'date': transaction_date, 'units': units, 'price': price})
        elif units < 0:
            remaining_units = abs(units)
            while remaining_units > 0 and portfolio[key]:
                earliest_purchase = portfolio[key][0]
                if earliest_purchase['units'] <= remaining_units:
                    remaining_units -= earliest_purchase['units']
                    portfolio[key].pop(0)
                else:
                    earliest_purchase['units'] -= remaining_units
                    remaining_units = 0

    return portfolio

def total_portfolio_value(portfolio, summary):
    total_value = 0
    for (isin, folio), holdings in portfolio.items():
        current_nav = next((float(item['nav']) for item in summary if item['isin'] == isin and item['folio'] == folio), 0)
        total_units = sum(h['units'] for h in holdings)
        value = total_units * current_nav
        total_value += value
    return total_value

def total_portfolio_gain(portfolio, summary):
    total_gain = 0
    for (isin, folio), holdings in portfolio.items():
        current_nav = next((float(item['nav']) for item in summary if item['isin'] == isin and item['folio'] == folio), 0)
        current_value = sum(h['units'] * current_nav for h in holdings)
        acquisition_cost = sum(h['units'] * h['price'] for h in holdings)
        gain = current_value - acquisition_cost
        total_gain += gain
    return total_gain

def calculate_xirr(cash_flows):
    def npv(rate):
        return sum(cf['amount'] / ((1 + rate) ** ((cf['date'] - cash_flows[0]['date']).days / 365)) for cf in cash_flows)
    
    return newton(npv, 0.1)

def main():
    file_path = 'transaction_detail.json' 
    data = load_transactions(file_path)

    transactions = data['data'][0]['dtTransaction']
    portfolio = fifo_transaction_processing(transactions)

    summary = data['data'][0]['dtSummary']
    total_value = total_portfolio_value(portfolio, summary)
    total_gain = total_portfolio_gain(portfolio, summary)

    print(f"Total Portfolio Value: {total_value}")
    print(f"Total Portfolio Gain: {total_gain}")

    cash_flows = []
    for transaction in transactions:
        date = parse_date(transaction['trxnDate'])
        amount = float(transaction['trxnAmount'])
        cash_flows.append({'date': date, 'amount': -amount})
    cash_flows.append({'date': datetime.now(), 'amount': total_value})
    
    xirr = calculate_xirr(cash_flows)
    print(f"Portfolio XIRR: {xirr}")

if __name__ == "__main__":
    main()

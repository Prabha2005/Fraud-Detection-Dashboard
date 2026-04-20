import pdfplumber
import pandas as pd
import re

def parse_gpay_pdf(file):

    transactions = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            for line in lines:
                # Match amount like ₹100 or ₹1,000
                match = re.search(r"₹[\d,]+(\.\d+)?", line)

                if match:
                    amount = float(match.group().replace("₹", "").replace(",", ""))

                    transactions.append({
                        "transaction_amount": amount,
                        "device_change": 0,
                        "merchant_risk": 0.5,
                        "geo_velocity": 0,
                        "hour_of_day": 12
                    })

    return pd.DataFrame(transactions)
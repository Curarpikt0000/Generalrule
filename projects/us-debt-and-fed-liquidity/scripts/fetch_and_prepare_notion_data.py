
import json
import os
import sys
import requests
from datetime import datetime, timedelta
import pytz
import time

# Add project root to path for imports
project_root = '/Users/chaojin/hermesagent/US Debt and Fed Liquidity/美债收益率和Fed中美日流动性日报'
if project_root not in sys.path:
    sys.path.append(project_root)

from config import DB, THRESHOLDS
from scrapers.fred_client import fetch_series # Corrected import

# Function to get JST today's date (US market close date)
def get_jst_today():
    jst_tz = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.now(jst_tz)
    return now_jst.strftime('%Y-%m-%d')

def get_fred_series_data(series_ids_map):
    data = {}
    for series_id, field_name in series_ids_map.items():
        # fetch_series already includes sleep
        series_data = fetch_series(series_id, days_back=1)
        if series_data and series_data[-1]['value'] != '.': # Get the latest valid observation
            data[field_name] = float(series_data[-1]['value'])
        else:
            data[field_name] = None
    return data

def calculate_status_light(value, thresholds_config):
    if value is None:
        return "⚪待定"
    # Convert thresholds to float if they are not already
    good_threshold = float(thresholds_config['good'])
    warning_threshold = float(thresholds_config['warning'])

    if value < good_threshold:
        return "🟢正常"
    elif value < warning_threshold:
        return "🟡警告"
    else:
        return "🔴危险"

def create_notion_page_properties(db_id, date_str, fetched_data, thresholds_map, title_prefix):
    properties = {
        "Date": {"date": {"start": date_str, "time_zone": "Asia/Tokyo"}},
        "Name": {"title": [{"text": {"content": f"{title_prefix} {date_str}"}}]}
    }
    for field_name, value in fetched_data.items():
        if value is None:
            properties[field_name] = {"number": None}
        else:
            properties[field_name] = {"number": value}
        
        # Calculate status light if thresholds are defined
        status_field_name = f"{field_name}_Status"
        # Check if a direct threshold key exists in the current thresholds_map for this status field
        if status_field_name in thresholds_map: 
            status_light = calculate_status_light(value, thresholds_map[status_field_name])
            properties[status_field_name] = {"select": {"name": status_light}}
        else:
             # Fallback to check THRESHOLDS directly based on field_name if no explicit mapping
            threshold_key_for_status = field_name.replace("_Yield", "_YIELD").replace("_Rate", "_RATE").upper()
            if threshold_key_for_status in THRESHOLDS:
                status_light = calculate_status_light(value, THRESHOLDS[threshold_key_for_status])
                properties[status_field_name] = {"select": {"name": status_light}}
            else:
                 # Default to "⚪待定" if no specific threshold mapping
                properties[status_field_name] = {"select": {"name": "⚪待定"}}

    return {
        "parent": {"database_id": db_id},
        "properties": properties
    }

def main():
    try:
        with open(os.path.join(project_root, 'notion_db_ids.json'), 'r') as f:
            notion_db_ids = json.load(f)

        # FRED_API_KEY is read from config.py directly by fred_client.py
        notion_token = os.getenv('NOTION_TOKEN')

        if not notion_token:
            print("Error: NOTION_TOKEN not found in environment variables.", file=sys.stderr)
            sys.exit(1)

        jst_today_str = get_jst_today()

        # Corrected A7 DB ID access
        a7_db_id = notion_db_ids['page_A_crisis_warning']['databases']['A7_Daily_Risk_Report']['database_id']

        all_notion_payloads = []

        # A1: UST_Yields_Daily
        ust_yields_series_ids = {
            'DGS2': 'UST_2Y_Yield',
            'DGS10': 'UST_10Y_Yield',
            'DGS30': 'UST_30Y_Yield'
        }
        ust_yields_data = get_fred_series_data(ust_yields_series_ids)
        if all(value is None for value in ust_yields_data.values()):
            print("FRED returned no data for UST_Yields_Daily. Assuming non-trading day.", file=sys.stderr)
            print(json.dumps({"status": "non_trading_day", "date": jst_today_str, "db_id_a7": a7_db_id}))
            sys.exit(0)
        
        # A1 Thresholds for status light calculation
        a1_threshold_map = {
            "UST_2Y_Yield_Status": THRESHOLDS['UST_2Y_YIELD'],
            "UST_10Y_Yield_Status": THRESHOLDS['UST_10Y_YIELD'],
            "UST_30Y_Yield_Status": THRESHOLDS['UST_30Y_YIELD']
        }
        a1_payload = create_notion_page_properties(
            notion_db_ids['page_A_crisis_warning']['databases']['A1_UST_Yields_Daily']['database_id'], 
            jst_today_str, ust_yields_data, a1_threshold_map, "美债收益率"
        )
        all_notion_payloads.append({"db_id": notion_db_ids['page_A_crisis_warning']['databases']['A1_UST_Yields_Daily']['database_id'], "payload": a1_payload})

        # A2: UST_Basis_SOFR_Daily
        ust_basis_sofr_series_ids = {
            'OBFR': 'OVN_Repo_Rate',
            'DFEDTARU': 'Fed_Funds_Rate'
        }
        ust_basis_sofr_data = get_fred_series_data(ust_basis_sofr_series_ids)

        a2_threshold_map = {
            "OVN_Repo_Rate_Status": THRESHOLDS['OVN_REPO_RATE'],
            "Fed_Funds_Rate_Status": THRESHOLDS['FED_FUNDS_RATE']
        }
        a2_payload = create_notion_page_properties(
            notion_db_ids['page_A_crisis_warning']['databases']['A2_UST_Basis_SOFR_Daily']['database_id'], 
            jst_today_str, ust_basis_sofr_data, a2_threshold_map, "UST Basis SOFR"
        )
        all_notion_payloads.append({"db_id": notion_db_ids['page_A_crisis_warning']['databases']['A2_UST_Basis_SOFR_Daily']['database_id'], "payload": a2_payload})

        # A5: Fed_Liquidity_Daily
        fed_liquidity_series_ids = {
            'WALCL': 'Fed_Balance_Sheet',
            'IORR': 'Interest_on_Reserves',
            'RRPONTSYD': 'ON_RRP_Takeup',
            'TREAST': 'Treasury_Deposits'
        }
        fed_liquidity_data = get_fred_series_data(fed_liquidity_series_ids)
        a5_threshold_map = {
            "Fed_Balance_Sheet_Status": THRESHOLDS['FED_BALANCE_SHEET'],
            "Interest_on_Reserves_Status": THRESHOLDS['INTEREST_ON_RESERVES'],
            "ON_RRP_Takeup_Status": THRESHOLDS['ON_RRP_TAKEUP'],
            "Treasury_Deposits_Status": THRESHOLDS['TREASURY_DEPOSITS']
        }
        a5_payload = create_notion_page_properties(
            notion_db_ids['page_A_crisis_warning']['databases']['A5_Fed_Liquidity_Daily']['database_id'], 
            jst_today_str, fed_liquidity_data, a5_threshold_map, "Fed 流动性"
        )
        all_notion_payloads.append({"db_id": notion_db_ids['page_A_crisis_warning']['databases']['A5_Fed_Liquidity_Daily']['database_id'], "payload": a5_payload})

        print(json.dumps(all_notion_payloads, indent=2))

    except Exception as e:
        print(f"An error occurred in fetch_and_prepare_notion_data.py: {e}", file=sys.stderr)
        jst_today_str = get_jst_today() # Ensure date is available even on early failure
        with open(os.path.join(project_root, 'notion_db_ids.json'), 'r') as f:
            notion_db_ids = json.load(f)
        a7_db_id = notion_db_ids['page_A_crisis_warning']['databases']['A7_Daily_Risk_Report']['database_id']
        print(json.dumps({"status": "failure", "date": jst_today_str, "db_id_a7": a7_db_id}), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

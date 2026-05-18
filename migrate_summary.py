import asyncio
from services.google_sheets import sheets_service, SUMMARY_HEADERS
from bot.survey_config import TRANSPORT_SURVEY
from bot.translations import TRANSLATIONS

async def migrate_data():
    print("Connecting to Google Sheets...")
    sheets_service.connect()
    print("Connected.")

    print("Fetching existing registrations...")
    records = await sheets_service.get_all_registrations()
    print(f"Found {len(records)} records.")

    am_options = TRANSLATIONS.get("am", {})
    inverse_options = {}
    for q in TRANSPORT_SURVEY.questions:
        if isinstance(q.options, list):
            for opt in q.options:
                am_val = am_options.get(f"opt_{opt}")
                if am_val:
                    inverse_options[am_val] = opt

    summary_rows = []
    for r in records:
        # Normalize fields
        dest = r.get("destination", "")
        if dest in inverse_options:
            dest = inverse_options[dest]
            
        morning = r.get("morning_departure_time", "")
        if morning in inverse_options:
            morning = inverse_options[morning]
            
        freq = r.get("service_frequency", "")
        if freq in inverse_options:
            freq = inverse_options[freq]

        summary_rows.append([
            str(r.get("submission_id", "")),
            str(r.get("full_name", "")),
            str(r.get("contact_phone", "")),
            str(dest),
            str(morning),
            str(r.get("evening_pickup_time", "")),
            f"{r.get('registration_date', '')} {r.get('registration_time', '')}"
        ])

    print(f"Prepared {len(summary_rows)} rows for the Summary Sheet.")
    
    # Write to summary sheet
    summary_ws = sheets_service._summary_spreadsheet.worksheet("Summarized")
    
    # Clear existing data except headers
    print("Clearing existing data in Summary Sheet...")
    summary_ws.clear()
    
    # Append headers and all rows
    print("Writing data to Summary Sheet...")
    summary_ws.append_row(SUMMARY_HEADERS, value_input_option="RAW")
    if summary_rows:
        summary_ws.append_rows(summary_rows, value_input_option="USER_ENTERED")
        
    print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_data())
from datetime import datetime
import json
import logging
import os
import requests

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (INFO, DEBUG, ERROR, etc.)
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def get_google_calendar_data(code: str):
    url = f"https://www.googleapis.com/calendar/v3/calendars/{code}%23holiday%40group.v.calendar.google.com/events"
    params = {"key": os.environ.get("GOOGLE_API_KEY")}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        logging.info("success get google data")
        return response.json()
    else:
        logging.info(f"err get google data {response.status_code}: {response.text}")


def parse_google_calendar_data(code: str, old_updated_at: datetime) -> datetime:
    google_data = get_google_calendar_data(code)

    # return if not new data
    new_updated_at = datetime.strptime(google_data["updated"], "%Y-%m-%dT%H:%M:%S.%fZ")
    if old_updated_at >= new_updated_at:
        logging.info(f"no update {old_updated_at} >= {new_updated_at}")
        return old_updated_at

    year = ""
    holidays = {}

    for existing_item in google_data.get("items", []):
        # Skip "Perayaan"
        if "Perayaan" in existing_item["description"]:
            logging.info(f'skip {existing_item["description"]}')
            continue

        # Extract the date from the "start" section
        date = existing_item.get("start", {}).get("date", "")

        if year != date[:4]:
            write_or_replace_file(code, year, holidays)
            year = date[:4]
            holidays = {}

        holidays[date] = {
            "summary": existing_item["summary"],
            "description": existing_item["description"],
        }

    write_or_replace_file(code, year, holidays)
    return new_updated_at


def write_or_replace_file(code: str, file_name: str, data):
    if file_name == "":
        logging.info("file_name empty")
        return

    file_dir = os.path.join("public", code, f"{file_name}.json")

    # Check if the new file already exists
    if os.path.exists(file_dir):
        os.remove(file_dir)

    # Write the new data to the new JSON file
    with open(file_dir, "w") as new_file:
        json.dump(data, new_file, indent=2)

    logging.info(f"success write {file_dir}")


def main():
    # Get meta
    code = "id.indonesian"

    with open(os.path.join("public", code, "meta.json"), "r") as file:
        country_meta = json.load(file)
        current_updated_at = datetime.strptime(
            country_meta["updated"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        new_updated_at = parse_google_calendar_data(code, current_updated_at)

        write_or_replace_file(
            code, "meta", {"updated": new_updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
        )


# Call the main function if this script is executed
if __name__ == "__main__":
    main()

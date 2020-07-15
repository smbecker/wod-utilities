# WOD Utilities
This repository contains a set of scripts that were used to migrate my workout results from beyondthewhiteboard.com to wodify.com. They were useful for me. Your mileage may vary.

## Scripts
- `bwtb_download_csv.py <bwtb-username> <bwtb-password> [<output path>|workouts.csv]` - This script will download a .CSV file from beyondthewhiteboard.com with all of your workout results. The file is in a pretty crude format. There are utilities in `bwtb_data.py` that can aid in parsing the contents of this file into typed workout results. There are a number of types of workout formats that beyondthewhiteboard uses so hopefully all of them are accounted for. If you find a format that is not accounted for, then you can open an issue or submit a PR to resolve it.

- `transform_bwtb_to_wodify.py [<input path>|workouts.csv] [<output path>|wodify.json]` - This script will take the .CSV file from above, parse the results into known bwtb workout results and then convert them into results that are compatible with the way that Wodify models workout results. The output file is in JSON just for simplicity in review and re-import.

- `wodify_import.py <wodify-username> <wodify-password> [<input path>wodify.json]` - This script will launch a Chrome browser and import the results of the input JSON file. Unfortunately, Wodify does not provide any type of API and the cross-site scripting protections in place prevent me from driving the API without a browser in the mix. This was the only way that I could find to import the results. This also makes it very brittle. If any of the fields in the Wodify site change then that will break the script.
	- This script will do everything possible to import the workout result. In the event that we cannot import specifically, then we will fallback to a 'Non-Benchmarked Metcon'. For example, if you have a Weightlifting result component that cannot be found then we will still import the result but under the 'Metcon' banner.

- `bwtb_to_wodify.py` - This script will walk you through all of the above steps in a _slightly_ more user-friendly experience for all of my non-techie friends out there that still want to take advantage of these utilities.

# Requirements
- Clone the repository locally (or download zip)
- Install Python 3.x
- `pip install -r requirements.txt`
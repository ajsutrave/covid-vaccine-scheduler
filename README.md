# covid-vaccine-scheduler

## Installation
First install dependencies 
```
python3 -m pip install -r requirements.txt
```
You will also need to install the Selenium Driver for your broswer:
https://sites.google.com/a/chromium.org/chromedriver/downloads
https://github.com/mozilla/geckodriver/releases

Make sure to either add the driver to your $PATH, or specify to the script where it was downloaded
```
python3 vaccine_check_heb.py --browser-driver-path /Path/To/Browser/Driver/browserdriver.exe
```

## Usage
Next run the script using your zip code, and the max distance away (in miles) you are willing to accept
```
python3 vaccine_check_heb.py --zip-code 78787 --max-distance 50 [...]
```

If you want to fill out your personal info and automatically accept the requirements fill out `personal_info.txt` and pass it in like so
```
python3 vaccine_check_heb.py @personal_info.txt --max-distance 50 [--auto-accept] [...]
```

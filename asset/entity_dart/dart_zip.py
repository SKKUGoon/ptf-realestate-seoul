import requests
import io
import os
import zipfile
import xmltodict
import pandas as pd
from dotenv import load_dotenv

from typing import Final

URL: Final = "https://opendart.fss.or.kr/api/corpCode.xml"

if __name__ == "__main__":
    # Load api key from .env
    load_dotenv()
    key = os.getenv('DART')

    # Request to DART
    params = {"crtfc_key": key}
    resp = requests.get(URL, params=params)

    # Process .zip
    file = io.BytesIO(resp.content)
    code_zip = zipfile.ZipFile(file)

    data = xmltodict.parse(
        code_zip.read('CORPCODE.xml').decode('utf-8')
    )['result']['list']
    df = pd.DataFrame(data)

    # Save as csv
    df.to_csv('dart.csv')

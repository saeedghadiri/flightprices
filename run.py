from typing import Optional

import requests
import datetime
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed

class FlightPrice(BaseModel):
    site: str
    origin: str
    destination: str
    date: datetime.date
    price: Optional[int] = None
    update_time: datetime.datetime

@retry(stop=stop_after_attempt(3), wait=wait_fixed(15))
def get_price_from_flytoday(origin: str, destination: str, number_of_days: int, update_time: datetime.datetime):
    try:
        name_map = {
            "tehran": "thr",
            "yerevan": "evn"
        }
    
        url = "https://www.flytoday.ir/api/gateway/V1/Flight/calendarLookUp"
    
        headers = {
            "accept": "*/*",
            "accept-language": "fa",
            "content-type": "application/json",
            "origin": "https://www.flytoday.ir",
            "priority": "u=1, i",
            "referer": "https://www.flytoday.ir/",
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/141.0.0.0 Safari/537.36",
            "x-app": "www.flytoday.ir",
            "x-currency": "IRR",
            "x-origin": "https://www.flytoday.ir",
            "x-path": "https://www.flytoday.ir/",
            "x-proxy-cache": "no-store",
            "x-token": "4f624743336d3231414e6f4a714d50625234426f576d636d75305775626256706e62315846485067657657572b4f556e3362504b333376465358546230493246",
        }
    
        payload = {
            "departureDate": datetime.datetime.now().strftime("%Y-%m-%dT00:00:00"),
            "forwardDay": number_of_days,
            "origin": name_map[origin],
            "destination": name_map[destination],
            "airTripType": "OneWay"
        }
    
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    
        print(response.status_code)
        print(response.text)
    
        result = []
        for r in response.json()['result']:
            flight_price = FlightPrice(
                site="flytoday",
                origin=origin,
                destination=destination,
                date=datetime.datetime.strptime(r['departureDate'], "%Y-%m-%d").date(),
                price=int(r['cheapestPrice']),  # convert to IRR
                update_time=update_time,
            )
            result.append(flight_price)
        return result
    except Exception as e:
        print(f"get data from flytoday faild e: {e}")
        return []

@retry(stop=stop_after_attempt(3), wait=wait_fixed(15))
def get_price_mrblit(origin: str, destination: str, number_of_days: int, update_time: datetime.datetime):
    try:

        name_map = {
            "tehran": "IKA",
            "yerevan": "EVN"
        }
    
        url = "https://flight.atighgasht.com/api/Flights/MinPrices"
    
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en,en-US;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-GB;q=0.6",
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJidXMiOiI0ZiIsInRybiI6IjE3Iiwic3JjIjoiMiJ9.vvpr9fgASvk7B7I4KQKCz-SaCmoErab_p3csIvULG1w",
            "content-type": "application/json-patch+json",
            "origin": "https://mrbilit.com",
            "priority": "u=1, i",
            "referer": "https://mrbilit.com/",
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sessionid": "session_63311d38-a2b2-4755-a360-da517ef90dfa",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/141.0.0.0 Safari/537.36",
            "x-playerid": "739ae1b9-15b8-41cf-8767-a7054e5789b5",
        }
    
        payload = {
            "AdultCount": 1,
            "ChildCount": 0,
            "InfantCount": 0,
            "EndDate": f"{(datetime.date.today() + datetime.timedelta(days=number_of_days)).strftime('%Y-%m-%d')}T00:00:00.000Z",
            "Destination": name_map[destination],
            "StartDate": f"{datetime.date.today().strftime('%Y-%m-%d')}T00:00:00.000Z",
            "Origin": name_map[origin],
        }
    
        response = requests.post(url, headers=headers, json=payload)
    
        print(response.status_code)
        print(response.text)
        result = []
        for r in response.json():
            flight_price = FlightPrice(
                site="mrbilit",
                origin=origin,
                destination=destination,
                date=datetime.datetime.strptime(r['Date'][:10], "%Y-%m-%d").date(),
                price=int(r['TotalFare']) if r['TotalFare'] is not None else None,  # convert to IRR
                update_time=update_time,
            )
            result.append(flight_price)
        return result
    except Exception as e:
        print(f"get data from flytoday faild e: {e}")
        return []


def gather_data():
    update_time = datetime.datetime.now(tz=datetime.timezone.utc)
    data_1 = get_price_from_flytoday("tehran", "yerevan", 60, update_time)
    data_2 = get_price_from_flytoday("yerevan", "tehran", 60, update_time)
    data_3 = get_price_mrblit("tehran", "yerevan", 60, update_time)
    data_4 = get_price_mrblit("yerevan", "tehran", 60, update_time)
    data = data_1 + data_2 + data_3 + data_4

    data = [d.model_dump(mode='json') for d in data]
    print("Data gathered:", len(data))
    print("Inserting to DB...")
    response = insert_to_db(data)


def insert_to_db(data):
    import os
    from supabase import create_client, Client

    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    try:
        response = (
            supabase.table("price")
            .insert(data)
            .execute()
        )
        return response
    except Exception as exception:
        print(exception)
        return exception


if __name__ == '__main__':
    gather_data()

import os
import urllib
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import quote
from enum import Enum
import requests
from dotenv import load_dotenv

load_dotenv()


def time_to_seconds(time_str) -> int or None:
    try:
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))

            # Calculate the total number of seconds
            seconds = (hours * 3600) + (minutes * 60)
        else:
            seconds = int(time_str) * 3600
        return seconds
    except ValueError:
        # Handle invalid input
        return None


def soup_helper(content, parser="html.parser"):
    return BeautifulSoup(content, parser)


def get_cookies():
    url = "https://studyrooms.lib.bcit.ca/day.php?"
    response = requests.get(url)
    cookies = response.cookies
    return cookies


class AreaNum(Enum):
    DTC_FLOOR_TWO = 15
    DTC_FLOOR_FIVE_SIX = 12


class RoomBooking:
    """
    RoomBooking Class used to initiate requests like logging in, booking and deleting.
    """
    LOGIN_URL = "https://studyrooms.lib.bcit.ca/admin.php"
    BOOKING_URL = "https://studyrooms.lib.bcit.ca/edit_entry_handler.php"
    DELETE_URL = "https://studyrooms.lib.bcit.ca/del_entry.php"
    VIEW_ENTRY = "https://studyrooms.lib.bcit.ca/view_entry.php"

    ROOMS_DICT = {
        "281": [99],
        "284": [100],
        "288": [104],
        "582": [76],
        "583": [77],
        "586": [78],
        "587": [79],
        "666": [90],
        "667": [91],
        "668": [92]
    }

    def view_week(self, year: int = datetime.year,
                  month: int = datetime.month,
                  day: int = datetime.day,
                  area: AreaNum = AreaNum.DTC_FLOOR_TWO,
                  room: int = 99):
        return f"https://studyrooms.lib.bcit.ca/week.php?year={year}&month={month}&day={day}&area={area.value}&room={room}"

    # For Future Implementation
    RESULTS = {
        "MaxError": "The maximum duration of a booking is 2 hours",
        "BelowZero": "You cannot create a booking which starts in less than 0 seconds",
        "Private": "Private"
    }
    CONTENT_HEADER = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    def __init__(self, email: str, password: str):
        self._email = email
        self._password = password
        self._logged_in = False
        self._cookies = get_cookies()
        self._rooms_booked = []

    def log_in(self) -> None:
        """
        Logs the user in with a username and password by searching for a phrase in the login success string

        :return:
        """
        credentials = {"NewUserName": self._email,
                       "NewUserPassword": self._password,
                       "Action": "SetName",
                       "returl": "https://studyrooms.lib.bcit.ca/day.php?&returl=https%3A%2F%2Fstudyrooms.lib.bcit.ca%2Fday.php%3F&returl=https%3A%2F%2Fstudyrooms.lib.bcit.ca%2Fday.php%3F%26returl%3Dhttps%253A%252F%252Fstudyrooms.lib.bcit.ca%252Fday.php%253F",
                       "TargetURL": "day.php?&returl=https%3A%2F%2Fstudyrooms.lib.bcit.ca%2Fday.php%3F&returl=https%3A%2F%2Fstudyrooms.lib.bcit.ca%2Fday.php%3F%26returl%3Dhttps%253A%252F%252Fstudyrooms.lib.bcit.ca%252Fday.php%253F"}
        try:
            response = requests.post(self.LOGIN_URL, data=credentials, headers=self.CONTENT_HEADER,
                                     cookies=self._cookies)
            if response.status_code == 200:
                content = response.text
                soup = BeautifulSoup(content, 'html.parser')
                result = soup.find(text=f"You are {self._email}")
                if result:
                    print("Successfully Logged in")
                    self._logged_in = True
                else:
                    print("Login Failed")
            else:
                print(f'Failed with response ${response.status_code}')
        except requests.exceptions.RequestException as error:
            print(f'An error occurred: {error}')
        except Exception as error:
            print(f'An unexpected error occurred: {error}')

    def get_booking_id_by_name(self, room_name="Studying", area: AreaNum = AreaNum.DTC_FLOOR_TWO, room: int = 104):
        """
        Gets the room id by the name of the room you set. TODO will probably be changed for deleting,

        :param room: The id for the BCIT area space
        :param area:
        :param room_name:
        :return:
        """
        try:
            response = requests.get(url=self.view_week(area=area, room=room), headers=self.CONTENT_HEADER,
                                    cookies=self._cookies)
            if response.status_code == 200:
                content = response.text
                result = soup_helper(content).find(text=room_name)
                enclosing_a_tag = result.find_parent('a')
                href = enclosing_a_tag.get('href')
                parsed_url = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                booking_id = query_params.get('id')[0]
                return booking_id
        except requests.exceptions.RequestException as e:
            print(f'An error occurred: {e}')
        except Exception as e:
            print(f'An unexpected error occurred: {e}')

    def book_room(self, room=72, duration=2, starting_time=3600, day=2):
        print(starting_time, duration)
        data = {
            "name": "Studying",
            "description": "Studying",
            "start_day": day,
            "start_month": datetime.now().month,
            "start_year": datetime.now().year,
            "start_seconds": starting_time,
            "end_day": day,
            "end_month": datetime.now().month,
            "end_year": datetime.now().year,
            "end_seconds": 36000,
            "area": 15,
            "rooms": room,
            "type": "I",
            "confirmed": 1,
            "private": 1,
            "returl": "",
            "create_by": self._email.lower(),
            "rep_id": 0,
            "edit_type": "series"
        }
        try:
            response = requests.post(url=self.BOOKING_URL, data=data, headers=self.CONTENT_HEADER,
                                     cookies=self._cookies)
            if response.status_code == 200:
                content = response.text
                result = soup_helper(content).find(text="Scheduling Conflict")
                if result:
                    print("Scheduling Conflict")
                    print(result)
                else:
                    print("Successfully booked!")
            else:
                print(f'Failed with response {response.status_code}')

        except requests.exceptions.RequestException as e:
            print(f'An error occurred: {e}')

        except Exception as e:
            print(f'An unexpected error occurred: {e}')

    def delete_booking(self, booking_id):
        data = {"id": booking_id}
        try:
            response = requests.post(url=self.DELETE_URL, data=data, headers=self.CONTENT_HEADER, cookies=self._cookies)
            print(response.status_code)
            if response.status_code == 200:
                print("Room Deleted Successfully")
                print(response.text)

        except requests.exceptions.RequestException as e:
            print(f'An error occurred: {e}')

        except Exception as e:
            print(f'An unexpected error occurred: {e}')

    def get_login(self):
        return self._logged_in


if __name__ == '__main__':
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')
    while True:
        room_booking = RoomBooking(email, password)
        try:
            room_booking.log_in()
            if room_booking.get_login():
                break
        except Exception as e:
            print(f"Error: {e}")

    while room_booking.get_login():
        user_input = input("Enter a command: \n1) Book a Room \n2) Find Room Id By Name \n3) Delete a Room\nq) Exit\n")
        if user_input == "1":
            try:
                # room_choice = input(f"Enter DTC Rooms {room_booking.ROOMS_DICT.keys()}:\n")
                # duration_input = (input("Enter Hours (2hrs. max):\n"))
                # starting_time = input("Enter Desired time (24hours): \n")
                # day_input = int(input("1) Today 2) Tomorrow 3) Day After Tomorrow"))
                # day_booking = (datetime.now() + timedelta(day_input - 1)).day
                # print(f"Booking for room {room_choice} for {duration_input} hours, at {starting_time} "
                #       f"on {day_booking}")
                # room_booking.book_room(room_booking.ROOMS_DICT[room_choice], time_to_seconds(duration_input),
                #                        time_to_seconds(starting_time), day_booking)
                room_booking.book_room()
            except KeyError as e:
                print(f"Key Doesn't Exist! Error: {e}")
            except ValueError as e:
                print(f"Invalid Value! Error: {e}")
            except Exception as e:
                print(f"Invalid Input! Error: {e}")
        elif user_input == "2":
            room_name = input("Enter Room Name (Case Sensitive):\n")
            ref = room_booking.get_booking_id_by_name(room_name)
        elif user_input == "3":
            room_name = input("Enter Room Name (Case Sensitive):\n")
            ref = room_booking.get_booking_id_by_name(room_name)
            room_booking.delete_booking(ref)
        elif user_input == "q":
            exit(0)

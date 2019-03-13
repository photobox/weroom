import requests
import json
import datetime


class Client:
    def __init__(self):
        self.headers = {'Content-Type': 'application/json;charset=utf-8'}
        with open('rooms_info.json') as f:
            rooms_info = json.load(f)
        self.rooms = {self._parse_room_name(room['name']): {'id': room['id'],
                                                            'whiteboard': 'Whiteboard' in room[
                                                                'amenities'],
                                                            'tv': 'TV' in room['amenities'],
                                                            'floor': room['floor']['floor_number'],
                                                            'capacity': room['capacity'],
                                                            'uuid': room['uuid']}
                      for room in rooms_info['rooms']}

    def login(self, username, password):
        data = {"username": username,
                "password": password,
                "api_key": "7d8f169aaa",
                "include_encrypted_user_uuid": True}
        r =requests.post('https://auth.wework.com/api/sessions', headers=self.headers,
                          data=json.dumps(data))
        if r.status_code>=400:
            return False
        r = json.loads(r.text)
        if not r['meta']['success']:
            return False
        connect_response = r['result']
        self.headers['encrypted_user_uuid'] = connect_response['session']['encrypted_user_uuid']
        return True

    def find_and_book_multiple(self, date, start_time, end_time,
                               room_list=None,
                               min_capacity=0, whiteboard=False, tv=False, preferred_floor=2,
                               period=1, times=1):
        t = list(map(int, date.split('-')))
        formated_date = datetime.date(year=t[0], month=t[1], day=t[2])
        dates = [str(formated_date)]
        result = []
        for i in range(times - 1):
            formated_date += datetime.timedelta(days=period)
            if formated_date-datetime.date.today() > datetime.timedelta(weeks=16):
                result.append('Warning: multibooking limited to 4 months in the future')
                break
            if formated_date.weekday()>4:
                continue
            dates.append(str(formated_date))
        for d in dates:
            try:
                result.append(
                    self.find_and_book_single_room(d, start_time, end_time,
                                                   room_list,
                                                   min_capacity, whiteboard, tv, preferred_floor))
            except:
                result.append("Failed to book a room on {} from {} to {}".format(date,
                                                                                 start_time,
                                                                                 end_time))
        return result

    def find_and_book_single_room(self, date, start_time, end_time,
                                  room_list=None,
                                  min_capacity=0, whiteboard=False, tv=False, preferred_floor=2):
        if room_list:
            valid_rooms = list(map(self._parse_room_name, room_list))
        else:
            valid_rooms = self.filter_sort_rooms(min_capacity, whiteboard, tv, preferred_floor)
        available_rooms = [room for room in valid_rooms if
                           self.check_available_slots(room, date, start_time, end_time)]
        booked = False
        result = "Failed to book a room on {} from {} to {}".format(date, start_time, end_time)
        for room in available_rooms:
            spent = self.book_room(room, date, start_time, end_time)
            if spent:
                result = 'Booked room {} on {} from {} to {} for {} credits'.format(room,
                                                                                    date,
                                                                                    start_time,
                                                                                    end_time,
                                                                                    spent)
                booked = True
                break
        return result

    def check_available_slots(self, room_name, date, start_time, end_time):
        room_name = self._parse_room_name(room_name)
        r = json.loads(
            requests.get(
                'https://rooms.wework.com/api/v5/conference_rooms/{}/time_slots?date={}'.format(
                    self.rooms[room_name]['uuid'],
                    date),
                headers=self.headers).text
        )
        filter_f = lambda s: s['start_time'] < start_time or s['end_time'] > end_time or s[
            'available_to_book']
        return all(map(filter_f, r['time_slots']))

    def book_room(self, room_name, date, start, end):
        room_id = self.rooms[room_name]['id']
        data = {"reservation":
                    {"company_uuid": "5fe11b8b-3240-4ac0-9b97-5530125c64e5",
                     "date": date,
                     "start_time": "{}T{}:00".format(date, start),
                     "end_time": "{}T{}:00".format(date, end),
                     "notes": "",
                     "reservable_id": room_id
                     }
                }
        r = requests.post('https://rooms.wework.com/api/v4/rooms/{}/reserve'.format(room_id),
                          headers=self.headers,
                          data=json.dumps(data))
        if r.status_code in [200, 201]:
            return json.loads(r.text)['credits']
        else:
            return 0.0

    def filter_sort_rooms(self, min_capacity=0, whiteboard=False, tv=False, prefered_floor=2):
        filter_f = lambda r: (r['capacity'] >= min_capacity
                              and (not whiteboard or r['whiteboard'])
                              and (not tv or r['tv']))
        name_list = [room_name for room_name in self.rooms if filter_f(self.rooms[room_name])]
        return sorted(name_list, key=lambda r: (abs(prefered_floor - self.rooms[r]['floor'])))

    def _parse_room_name(self, n):
        s = n.lower()
        s = s.replace(' ', '')
        return s



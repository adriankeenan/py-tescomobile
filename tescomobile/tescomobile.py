import requests
import time
import uuid
import datetime

def response_valid(func, *args):
    """check that the API returns a success code in the response"""

    def wrapper(*args):

        response = func(*args)

        response_code = response.get('responseCode', None)
        if response_code != 'OK':
            raise Exception('server response error, code: ' + response_code)

        return response

    return wrapper

def requires_token(func, *args):
    """check that we have a token before calling the wrapped method"""

    def wrapper(*args):

        self = args[0]

        if not hasattr(self, 'token') or not isinstance(self.token, str):
            raise Exception('method requires an authentication token')

        return func(*args)

    return wrapper

class TescoMobile(object):
    """a wrapper around the Tesco Mobile HTTPS JSON API"""

    def __init__(self, phone_number=None, token=None, user_agent=None):

        self.user_agent = user_agent
        if not self.user_agent:
            self.user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 6P Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'

        self.phone_number = phone_number
        if not self.phone_number:
            raise AttributeError('Phone number must be provided')
        if not isinstance(self.phone_number, str):
            raise TypeError('Phone number must be a string')
        if self.phone_number[0] == '+':
            raise AttributeError('Phone number must start with 07..., not +447...')

        self.token = token

    def _get_modified_since_header(self):
        """returns the current datetime for the If-Modified-Since request
        header"""

        now = time.time()
        return time.strftime('%a, %d %b %Y %H:%M:%S GMT+00:00', time.gmtime(now))

    @response_valid
    def send_pin_sms(self):
        """send an sms containing an auth pin"""

        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'Connection': 'Keep-Alive',
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': self.user_agent,
            'X-Client': 'device=Android;version=3.5;tablet=false'
        }

        body = {
            'subscriberNumber': self.phone_number
        }

        response = requests.post(
            'https://apitesco3.mobileaware.com/TescoAPI3/requestpin',
            headers=headers,
            json=body
        )

        data = response.json()

        return data

    @response_valid
    def token_pin_exchange(self, pin):
        """exchange the pin for an auth token"""

        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'Connection': 'Keep-Alive',
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': self.user_agent,
            'X-Client': 'device=Android;version=3.5;tablet=false'
        }

        body = {
            'pinCode': str(pin),
            'subscriptionNumber': self.phone_number
        }

        response = requests.post(
            'https://apitesco3.mobileaware.com/TescoAPI3/confirmpin',
            headers=headers,
            json=body
        )

        data = response.json()

        self.token = data['token']

        return data

    @requires_token
    @response_valid
    def get_usage(self):
        """get usage data (minutes, sms, data) using phone number and token"""

        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'CNT': '1',
            'Connection': 'Keep-Alive',
            'Content-Type': 'application/json; charset=utf-8',
            'If-Modified-Since': self._get_modified_since_header(),
            'NET': 'WIFI',
            'User-Agent': self.user_agent,
            'X-Client': 'device=Android;version=3.5;tablet=false',
            'X-Token': self.token,
            'reqID': str(uuid.uuid4()).replace('-', ''),
            'ts': str(int(time.time() * 1000))
        }

        body = {
            'subscriptionNumber': self.phone_number
        }

        response = requests.post(
            'https://apitesco3.mobileaware.com/TescoAPI3/full',
            headers=headers,
            json=body
        )

        data = response.json()

        return data

    @requires_token
    @response_valid
    def get_invoices(self):
        """get a list of invoices for the account"""

        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'Connection': 'Keep-Alive',
            'If-Modified-Since': self._get_modified_since_header(),
            'User-Agent': self.user_agent,
            'X-Client': 'device=Android;version=3.5;tablet=false',
            'X-Token': self.token
        }

        response = requests.get(
            'https://apitesco3.mobileaware.com/TescoAPI3/invoice/' + self.phone_number,
            headers=headers
        )

        data = response.json()

        return data

    @requires_token
    @response_valid
    def logout(self):
        """invalidate the auth token"""

        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'Connection': 'Keep-Alive',
            'If-Modified-Since': self._get_modified_since_header(),
            'User-Agent': self.user_agent,
            'X-Client': 'device=Android;version=3.5;tablet=false',
            'X-Token': self.token
        }

        response = requests.get(
            'https://apitesco3.mobileaware.com/TescoAPI3/logout',
            headers=headers
        )

        data = response.json()

        self.token = None

        return data
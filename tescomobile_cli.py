 # -*- coding: utf-8 -*-

if __name__ == '__main__':

    # Check for python 3.X
    import sys
    if sys.version_info.major < 3:
        print('This script requires Python 3.x')
        exit(-1)

    # Imports
    import os
    import collections
    import shutil

    import datetime
    from tescomobile import TescoMobile

    # Get details from env
    KEY_PHONENUMBER = 'TESCO_PHONENUMBER'
    KEY_TOKEN = 'TESCO_TOKEN'

    phone_number = os.getenv(KEY_PHONENUMBER, None)
    token = os.getenv(KEY_TOKEN, None)

    if not phone_number:
        print('No ' + KEY_PHONENUMBER + ' env var set')
        phone_number = input('Please enter your phone number: ').replace(' ', '')
        print('Add ' + KEY_PHONENUMBER + ' to your path for use next time')

    if not token:
        print('No ' + KEY_TOKEN + ' env var set')
        t = TescoMobile(phone_number=phone_number)
        t.send_pin_sms()
        pin = input('Please enter the PIN sent via SMS: ')

        print('Fetching token...')

        data = t.token_pin_exchange(pin)
        token = data['token']
        print('Token: ' + token)
        print('Add ' + KEY_TOKEN + ' to your path for use next time')

    print('Fetching balance...\n')

    t = TescoMobile(phone_number=phone_number, token=token)
    data = t.get_usage()

    DATE_FORMAT = '%d/%m/%Y'

    # Determine column widths. COL3 fills remaining space.
    console_width = shutil.get_terminal_size((80,)).columns

    COL1_WIDTH = 20
    COL2_WIDTH = 13
    COL4_WIDTH = 4

    fixed_cols = [COL1_WIDTH, COL2_WIDTH, COL4_WIDTH]
    fixed_width_space = sum(fixed_cols) + len(fixed_cols)
    COL3_WIDTH = console_width - fixed_width_space

    # Get phone number
    phone_number_str = data['subscriberInformation']['mobilePhoneNumber']
    tarrif_str = data['subscriberInformation']['tariff']['description']
    print('Tesco Mobile - ' + phone_number_str + ' - ' + tarrif_str)

    # Get bill start and end dates
    bill_date_start = datetime.datetime.fromtimestamp(int(data['lastInvoice']['billProducedDate']) / 1000)
    bill_date_end = datetime.datetime.fromtimestamp(int(data['nextBillDate']) / 1000)

    bill_days_total = (bill_date_end - bill_date_start).days
    bill_days_used = (datetime.datetime.now() - bill_date_start).days
    bill_days_percentage = (bill_days_used / bill_days_total) * 100

    Allowance = collections.namedtuple('Allowance', 'name total used format')

    allowances = []

    # Add bill cycle as allowance
    bill_cycle_format = lambda x: int(x)
    allowances.append(Allowance('Bill cycle', bill_days_total, bill_days_used, bill_cycle_format))

    # Define the allowances we want to display
    AllowanceDefinition = collections.namedtuple('AllowanceDefinition', 'name format')
    allowance_map = {
        'MIN' : AllowanceDefinition('Minutes', lambda x: int(x)),
        'UNIT' : AllowanceDefinition('Texts', lambda x: int(x)),
        'MB' : AllowanceDefinition('Data', lambda x: int(x)),
        'SAFETYBUFFER' : AllowanceDefinition('Safety buffer', lambda x: '£{:.2f}'.format(x))
    }

    # Add sms, phone, data etc allowances
    for allowance in data['allowances']:

        al_type_id = allowance['allowanceType']

        # Skip any we don't want
        if not al_type_id in allowance_map:
            continue

        al_total = allowance['totalAllowance']
        al_remaining = allowance['totalRemaining']
        al_used = al_total - al_remaining
        al_name = allowance_map[al_type_id].name
        al_format = allowance_map[al_type_id].format

        allowances.append(Allowance(al_name, al_total, al_used, al_format))

    # Print bill start and end dates
    bill_start_str = 'Bill cycle started '.ljust(COL1_WIDTH)
    bill_start_str +=  ' ' + bill_date_start.strftime(DATE_FORMAT).rjust(COL2_WIDTH)
    print(bill_start_str)

    bill_end_str = 'Bill cycle ends  '.ljust(COL1_WIDTH)
    bill_end_str +=  ' ' + bill_date_end.strftime(DATE_FORMAT).rjust(COL2_WIDTH)
    print(bill_end_str)

    # Print allowances
    for al in allowances:

        # Name
        col1 = al.name.ljust(COL1_WIDTH)

        # Used/Total
        col2_used = str(al.format(al.used))
        col2_total = str(al.format(al.total))
        col2 = (col2_used + '/' + col2_total).rjust(COL2_WIDTH)

        # ASCI progress bar
        progess_percent = float(al.used)/al.total * 100

        progress_size  = COL3_WIDTH - 2
        progress_bar_size = int(progess_percent / (float(100) / progress_size))
        progress_empty_size = progress_size - progress_bar_size

        col3 = '[' + '=' * progress_bar_size + ' ' * progress_empty_size + ']'

        # progress percentage
        col4 = (str(int(progess_percent)) + '%').rjust(COL4_WIDTH)

        print('{} {} {} {}'.format(col1, col2, col3, col4))
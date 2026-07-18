#!/usr/bin/env python3
"""Run a speedtest (Ookla Speedtest CLI) and append the result to a Google Sheet."""

import argparse
import datetime
import json
import shutil
import subprocess
import sys

import gspread

HEADER = ['Date (dd-mm-yy)', 'Download (Mbps)', 'Upload (Mbps)', 'Ping (ms)']
CHART_TITLE = 'Download (Mbps), Upload (Mbps) and Ping (ms)'


def parse_args():
    parser = argparse.ArgumentParser(
        description='Simple Python script to push speedtest results '
                    '(using the Ookla Speedtest CLI) to a Google Sheets spreadsheet'
    )
    parser.add_argument(
        '-w', '--workbookname', default='Speedtest',
        help='Sets the workbook name, default is "Speedtest"'
    )
    parser.add_argument(
        '-b', '--bymonth', action='store_true',
        help='Creates a new sheet for each month named MMM YY (ex: Jun 18)'
    )
    parser.add_argument(
        '-c', '--credentials', default='service_account.json',
        help='Path to the Google service account key file, '
             'default is "service_account.json"'
    )
    return parser.parse_args()


def get_client(credentials_file):
    """Authenticate against the Google Sheets API with a service account."""
    try:
        return gspread.service_account(filename=credentials_file)
    except FileNotFoundError:
        sys.exit(
            f'Service account key file "{credentials_file}" not found.\n'
            'Create a service account key in the Google Cloud console and '
            'save it there, or point to it with --credentials.'
        )


def service_account_email(credentials_file):
    with open(credentials_file) as f:
        return json.load(f).get('client_email', '<unknown>')


def run_speedtest():
    """Run the Ookla Speedtest CLI and return (download_mbps, upload_mbps, ping_ms)."""
    speedtest_bin = shutil.which('speedtest')
    if speedtest_bin is None:
        sys.exit('Ookla Speedtest CLI not found in PATH, see '
                 'https://www.speedtest.net/apps/cli')

    result = subprocess.run(
        [speedtest_bin, '--format=json'], capture_output=True, text=True
    )
    if result.returncode != 0:
        sys.exit(f'speedtest failed: {result.stderr.strip() or result.stdout.strip()}')

    data = json.loads(result.stdout)
    # The CLI reports bandwidth in bytes/s; convert to megabits/s
    download = data['download']['bandwidth'] * 8 / 1_000_000
    upload = data['upload']['bandwidth'] * 8 / 1_000_000
    ping = data['ping']['latency']
    return download, upload, ping


def open_worksheet(gc, cliarg):
    """Open the target spreadsheet and (monthly) worksheet."""
    try:
        spreadsheet = gc.open(cliarg.workbookname)
    except gspread.SpreadsheetNotFound:
        sys.exit(
            f'Spreadsheet "{cliarg.workbookname}" not found.\n'
            'Create it in your Google account and share it (Editor) with the '
            f'service account: {service_account_email(cliarg.credentials)}'
        )

    if cliarg.bymonth:
        sheetname = datetime.datetime.now().strftime('%b %y')
        try:
            sheet = spreadsheet.worksheet(sheetname)
        except gspread.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(sheetname, rows=1000, cols=26, index=0)
    else:
        sheet = spreadsheet.sheet1

    return spreadsheet, sheet


def ensure_header_and_chart(spreadsheet, sheet):
    """Create the header row and line chart on a fresh sheet."""
    if sheet.acell('A1').value == HEADER[0]:
        return

    sheet.update([HEADER], 'A1:D1')
    sheet.freeze(rows=1)

    def column_range(index):
        return {'sourceRange': {'sources': [{
            'sheetId': sheet.id,
            'startRowIndex': 0,
            'startColumnIndex': index,
            'endColumnIndex': index + 1,
        }]}}

    spreadsheet.batch_update({'requests': [{'addChart': {'chart': {
        'spec': {
            'title': CHART_TITLE,
            'basicChart': {
                'chartType': 'LINE',
                'legendPosition': 'BOTTOM_LEGEND',
                'headerCount': 1,
                'domains': [{'domain': column_range(0)}],
                'series': [
                    {'series': column_range(column), 'targetAxis': 'LEFT_AXIS'}
                    for column in (1, 2, 3)
                ],
            },
        },
        'position': {'overlayPosition': {'anchorCell': {
            'sheetId': sheet.id,
            'rowIndex': 0,
            'columnIndex': 4,
        }}},
    }}}]})


def submit_into_spreadsheet(gc, cliarg, download, upload, ping):
    """Append the speedtest result to the spreadsheet."""
    spreadsheet, sheet = open_worksheet(gc, cliarg)
    ensure_header_and_chart(spreadsheet, sheet)

    date = datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S')
    sheet.append_row(
        [date, round(download, 2), round(upload, 2), round(ping, 2)],
        value_input_option='USER_ENTERED'
    )
    sheet.columns_auto_resize(0, 3)


def main():
    cliarg = parse_args()

    print('Authenticating with Google...')
    gc = get_client(cliarg.credentials)

    print('Starting speed test...')
    download, upload, ping = run_speedtest()
    print(f'Speed test finished (Download: {download:.2f} Mbps, '
          f'Upload: {upload:.2f} Mbps, Ping: {ping:.2f} ms)')

    print('Writing to spreadsheet...')
    submit_into_spreadsheet(gc, cliarg, download, upload, ping)
    print('Successfully written to spreadsheet!')


if __name__ == '__main__':
    main()

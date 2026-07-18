google-speedtest-chart
======================

Simple Python script to push speedtest results (using the Ookla Speedtest CLI) to a Google Sheets spreadsheet. I use this to measure and track my upload and download bandwith:

[![](http://up.frd.mn/hsoXvzqYw3.png)](https://docs.google.com/spreadsheets/d/e/2PACX-1vSJtguwlM6K4wJtwK842dpTRG46knn0M71A966VRE_9vIcP21s0XMrHXaOwekR2oznM9HE9K344NAsY/pubchart?oid=198771870&format=interactive)

You can find an interactive demo (~~actually productive~~) version of the chart by clicking the image above.

_Note_: If you rather like Grafana than writing to a Google spreadsheet, checkout my new project [`docker-speedtest`](https://github.com/frdmn/docker-speedtest).

### Requirements

* Google account
* Python 3.X
* [`Speedtest CLI by Ookla team`](https://www.speedtest.net/apps/cli)
* [`gspread`](https://github.com/burnash/gspread)

### Installation and usage

1. Clone and open repository:

    ```
    git clone https://github.com/frdmn/google-speedtest-chart.git
    cd google-speedtest-chart
    ```

1. Install dependencies:

    ```
    # https://www.speedtest.net/apps/cli
    wget https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz
    tar xvf ookla-speedtest-1.2.0-linux-x86_64.tgz
    sudo mv speedtest /usr/bin/

    # pip install -r requirements.txt

    sudo apt install python3-gspread
    ```

1. Symlink it into your `$PATH`:

    ```
    ln -s speedtest-charts.py /usr/local/bin/speedtest-to-google
    ```

1. Authorization (service account)

    The script authenticates with a Google Cloud **service account**, which is the
    recommended way to access Google Sheets from unattended scripts and cronjobs
    (no browser-based OAuth flow, no token refresh files):

    1. Create a project in the [Google Cloud console](https://console.cloud.google.com/) (or reuse an existing one)
    1. Enable the **Google Sheets API** and the **Google Drive API** for that project
    1. Create a **service account** ("IAM & Admin" => "Service Accounts"), then create a **JSON key** for it and save the downloaded file as `service_account.json` next to the script (or pass its path with `--credentials`)

    :book: See also the [gspread authentication docs](https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account) for a step-by-step guide.

1. Create a spreadsheet dedicated to collect your speedtest results and **share it (as Editor) with the service account email** (the `client_email` value in `service_account.json`):

    :book: [docs/Create-a-spreadsheet-to-collect-data.md](docs/Create-a-spreadsheet-to-collect-data.md)

1. Run the script with default settings (make sure you have a spreadsheet document called "Speedtest"):

    ```
    speedtest-to-google
    ```

    Alternatively you can use the `-w` switch to set a custom spreadsheet name:

    ```
    speedtest-to-google -w Speedtest-document
    ```

    Here are some other arguments that are available:

    ```
    usage: speedtest-charts.py [-h] [-w WORKBOOKNAME] [-b] [-c CREDENTIALS]

    Simple Python script to push speedtest results (using the Ookla Speedtest CLI) to a Google Sheets spreadsheet

    optional arguments:
      -h, --help            show this help message and exit
      -w WORKBOOKNAME, --workbookname WORKBOOKNAME
                            Sets the workbook name, default is "Speedtest"
      -b, --bymonth         Creates a new sheet for each month named MMM YY (ex: Jun 18)
      -c CREDENTIALS, --credentials CREDENTIALS
                            Path to the Google service account key file, default is "service_account.json"
    ```

### License

[MIT](LICENSE)

### Version

2.0.0

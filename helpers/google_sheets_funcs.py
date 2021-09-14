import httplib2
import os
import string
import time

from apiclient import discovery, errors
from oauth2client.service_account import ServiceAccountCredentials

from helpers.constants import KEY_PATH


def get_credentials_gsheets(json_file="google_service_account.json"):
    credential_path = os.path.join(KEY_PATH, json_file)
    return ServiceAccountCredentials.from_json_keyfile_name(
        credential_path,
        ["https://spreadsheets.google.com/feeds"],
    )


def build_service(json_file="google_service_account.json"):
    credentials = get_credentials_gsheets(json_file=json_file)
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = "https://sheets.googleapis.com/$discovery/rest?" "version=v4"
    service = discovery.build(
        "sheets", "v4", http=http, discoveryServiceUrl=discoveryUrl
    )
    return service


def excel_col(col):
    """ Convert numeric column number to excel-style (letter) column label. """
    quot, rem = divmod(col - 1, 26)
    return excel_col(quot) + chr(rem + ord("A")) if col != 0 else ""


def fetch_length_from_excel_cols(col_range):
    col_range = col_range.split("!")[-1]
    start = col_range.split(":")[0].strip().upper()
    start = "".join([i for i in start if not i.isdigit()])
    end = col_range.split(":")[1].strip().upper()
    end = "".join([i for i in end if not i.isdigit()])

    start_position = 0
    count = 0
    for letter in start:
        count += 1
        letter_index = string.ascii_uppercase.index(letter) + 1
        if count != len(start):
            start_position += 26 * letter_index
        else:
            start_position += letter_index

    end_position = 0
    count = 0
    for letter in end:
        count += 1
        letter_index = string.ascii_uppercase.index(letter) + 1
        if count != len(end):
            end_position += 26 * letter_index
        else:
            end_position += letter_index

    return end_position - start_position + 1


def get_sheet_values(
    sheet_id, range_name, service=None, json_file="google_service_account.json"
):
    if service is None:
        service = build_service(json_file=json_file)

    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=range_name)
            .execute()
        )
    except errors.HttpError as err:
        time.sleep(5)
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=range_name)
            .execute()
        )

    values = result.get("values", [])

    if not values:
        return []
    else:
        values = add_blanks(values, fetch_length_from_excel_cols(range_name))
        return values


def write_sheet_values(
    sheet_id,
    range_name,
    values,
    dimension="ROWS",
    service=None,
    retries=1,
    json_file="google_service_account.json",
):
    """
    :param dimension: 'ROWS' or 'COLUMNS'
    # # https://developers.google.com/sheets/api/samples/writing
    """

    if service is None:
        service = build_service(json_file=json_file)

    body = {"values": values, "majorDimension": dimension}

    request = (
        service.spreadsheets()
        .values()
        .update(
            valueInputOption="USER_ENTERED",
            spreadsheetId=sheet_id,
            range=range_name,
            body=body,
        )
    )

    try:
        request.execute(num_retries=retries)
    except errors.HttpError as err:
        time.sleep(5)
        request.execute(num_retries=retries)


def clean_sheet(
    sheet_id,
    tab_id,
    end_column_index,
    start_row_index=1,
    service=None,
    retries=1,
    json_file="google_service_account.json",
):
    if service is None:
        service = build_service(json_file=json_file)

    body = {
        "requests": [
            {
                "updateCells": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": start_row_index,
                        "startColumnIndex": 0,
                        "endColumnIndex": end_column_index,
                    },
                    "fields": "userEnteredValue",
                }
            }
        ]
    }

    request = service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body)
    request.execute(num_retries=retries)


def add_blanks(read_list, length):
    for row in read_list:
        while len(row) < length:
            row.append("")
    return read_list


def find_a_z(a_length, columns):
    if a_length > 26:
        letter = string.ascii_uppercase[(int(a_length / 26)) - 1]
        letter = letter + string.ascii_uppercase[int(a_length % 26)]
    else:
        letter = string.ascii_uppercase[a_length - 1]
    if columns:
        return "!A:{0}".format(letter)
    else:
        return "!A2:{0}".format(letter)


def get_sheet_id(sheet_id, sheet_order, json_file="google_service_account.json"):
    service = build_service(json_file=json_file)
    sheets = service.spreadsheets().get(spreadsheetId=sheet_id).execute()["sheets"]
    return sheets[sheet_order]["properties"]["sheetId"]


def duplicate_sheet(
    sheet_id, new_sheet_name, dup_id=0, json_file="google_service_account.json"
):
    service = build_service(json_file=json_file)
    latest_sheet_id = get_sheet_id(sheet_id, dup_id)
    request_body = {
        "requests": [
            {
                "duplicateSheet": {
                    "sourceSheetId": latest_sheet_id,
                    "insertSheetIndex": 0,
                    "newSheetName": new_sheet_name,
                }
            }
        ]
    }
    request = service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body=request_body
    )
    request.execute()


def delete_sheet(
    sheet_id, delete_length, del_id=-1, json_file="google_service_account.json"
):
    service = build_service(json_file=json_file)
    sheets = service.spreadsheets().get(spreadsheetId=sheet_id).execute()["sheets"]
    if len(sheets) > delete_length:
        latest_sheet_id = sheets[del_id]["properties"]["sheetId"]
        request_body = {
            "requests": [
                {
                    "deleteSheet": {
                        "sheetId": latest_sheet_id,
                    }
                }
            ]
        }
        request = service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body=request_body
        )
        request.execute()


def write_columns_to_sheet(
    sheet_id, tab_name, columns, json_file="google_service_account.json"
):
    write_sheet_values(
        sheet_id=sheet_id,
        range_name=tab_name + find_a_z(len(columns), True),
        values=[columns],
        dimension="ROWS",
        json_file=json_file,
    )


def write_spreadsheet(
    df,
    sheet_id,
    tab_name,
    columns=True,
    tab_id=0,
    clean_sheet_bool=True,
    clean_sheet_start_row=1,
    write_row_start=-1,
    json_file="google_service_account.json",
):
    service = build_service(json_file=json_file)

    tab_range = find_a_z(len(df.columns.values.tolist()), columns)
    write_list = df.applymap(str).values.tolist()

    if write_row_start != -1 and not columns:
        tab_range = tab_range.replace("2", str(write_row_start))

    if columns:
        write_list.insert(0, df.columns.values.tolist())

    if clean_sheet_bool:
        clean_sheet(
            sheet_id,
            tab_id,
            len(df.columns.values.tolist()),
            start_row_index=clean_sheet_start_row,
            service=service,
            json_file=json_file,
        )

    write_sheet_values(
        sheet_id=sheet_id,
        range_name=tab_name + tab_range,
        values=write_list,
        service=service,
        json_file=json_file,
    )

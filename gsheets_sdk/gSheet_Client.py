from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# Setup the Sheets API

class gSheet_Client:

	def __init__(self, spreadsheet_id):

		self.spreadsheet_id = spreadsheet_id
		self.client = self.authenticate()

	def authenticate(self):
		SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
		store = file.Storage('credentials.json')
		creds = store.get()
		if not creds or creds.invalid:
		    flow = client.flow_from_clientsecrets('gsheets_sdk/client_secret.json', SCOPES)
		    creds = tools.run_flow(flow, store)
		service = build('sheets', 'v4', http=creds.authorize(Http()))
		return service.spreadsheets()

	def get_values(self, range_str):
		result = self.client.values().get(spreadsheetId=self.spreadsheet_id,
		                                  range=range_str).execute()
		values = result.get('values', [])
		loans  = []
		if not values:
		    print('No data found.')
		    return loans
		else:
			for row in values[1:]:
				loan = {}
				for header, data in zip(values[0], row):
					loan[header] = data
				loans.append(loan)
		return loans

	def set_value(self, range_str, value):
		body = {
			'range': range_str,
			'values': [[value]]
		}
		result = self.client.values().update(spreadsheetId=self.spreadsheet_id,
		                                     range=range_str,
		                                     body=body,
		                                     valueInputOption='USER_ENTERED').execute()
		return result
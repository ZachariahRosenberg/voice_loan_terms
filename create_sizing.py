import json, requests, time
from luis_sdk import LUISClient
from pygame   import mixer
import speech_recognition as sr
from gsheets_sdk import gSheet_Client


class Voice_Sizer():

	def __init__(self, map_key, speech_key, luis_appid, luis_appkey, gSheet_sskey, use_mic=True):

		self.map_key    = map_key
		self.speech_key = speech_key

		self.luis   = LUISClient(luis_appid, luis_appkey, True)
		self.gSheet = gSheet_Client(gSheet_sskey)

		self.use_mic = use_mic
		self.begin()
	
	# Starts voice flow, prompts user and sends to LUIS API
	def begin(self):

		response = self.ask_user('Hello, how can I help you?')
		print('user request: ', response)

		print('sending request to LUIS...')
		self.luis.predict(response, {'on_success': self.operator, 'on_failure': lambda err: print(err)})

	# Callback for LUIS Intent response. Routes intent to controller
	def operator(self, res):
		
		intent = res.get_top_intent().get_name()

		if intent == 'Create Sizing':

			self.text_to_speech('Got it, you would like to create a sizing.')
			print('Got it, you would like to create a sizing.')
			self.create_sizing()

		elif intent == 'Something Else':

			self.text_to_speech('Ok, I have understood that you do not know what you would like. Typical. Here\'s a fascinating thought.')
			print('???')
			self.get_thought()

		else:
			print('I\'m sorry, I didn\'t catch that')
			self.begin()

	# Controller for create sizing
	def create_sizing(self):

		address = self.ask_user('what is the address of the property?')

		try:
			bing_address = self.get_bing_address(address)
			print('bing address: ', ' '.join(bing_address.values()))
		except:
			self.text_to_speech('I am sorry, I didn\'t quite get that.')
			self.create_sizing()

		income = self.ask_user('how much did the property collect in rent last year?')
		print('income reported: ',income)

		expense = self.ask_user('what were the total expenses for the property last year?')
		print('expense: ', expense)

		units = self.ask_user('How many units are available at the property?')
		print('units: ', units)

		self.text_to_speech('Alright, sizing property now.')
		print('Sizing...')

		t1 = time.clock()
		self.set_uw_values('Inputs!B5', ' '.join(bing_address.values()))
		self.set_uw_values('Inputs!B22', income)
		self.set_uw_values('Inputs!B51', expense)
		self.set_uw_values('Inputs!B14', units)
		t2 = time.clock()
		time_elapsed = t2-t1

		self.text_to_speech('Finished with sizing, pulling FHA loan terms')
		print('Pulling latest FHA terms')

		fha_loan = self.get_uw_values()

		if float(fha_loan['Loan Amount With Fee'][1:].replace(',', '')) > 1:
			quote = '''
				We have a loan amount of {} at a {} rate for a {} term. 
				This sizing was completed in {} seconds. 
				'''.format(fha_loan['Loan Amount With Fee'], fha_loan['Rate With Fee'], fha_loan['Loan Type'], round(time_elapsed, 2))
			print(quote)
			self.text_to_speech(quote+' Beat that Ryan Patterson!')
		else:
			quote = 'I am sorry, but this property is not a fit for the FHA program. Let\'s try with CMBS instead...'
			print(quote)
			self.text_to_speech(quote)
		
	# Prompts user for input via mic/text.
	def ask_user(self, request):

		self.text_to_speech(request)
		print(request)

		if self.use_mic:
			r = sr.Recognizer()
			with sr.Microphone() as source:
				r.adjust_for_ambient_noise(source)
				self.play_prompt()
				print("Recording...")
				audio = r.listen(source)
				print("Got it, sending to VoiceRecog...")

			try:	
				response = r.recognize_bing(audio, key=self.speech_key)
			except e:
				print("Speech Recognition failed: {0}".format(e))
				response = input('Let\'s try typing the request instead -->\n')

		else:
			response = input('please type your response\n')

		return response

	# Converts text to audio. Uses Bing Speech API
	def text_to_speech(self, text, file_name='sounds/output.mp3', play_audio=True):

		# retrieve jwt
		url = 'https://api.cognitive.microsoft.com/sts/v1.0/issueToken'
		headers = {
			'Ocp-Apim-Subscription-Key': self.speech_key
		}
		bing_jwt = requests.post(url, headers=headers).text


		url = 'https://speech.platform.bing.com/synthesize'
		headers = {
			'Content-Type':	'application/ssml+xml',
			'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
			'User-Agent': 'gLabs Speech',
			'Authorization': 'Bearer ' + bing_jwt 
		}

		payload = """
			<speak version='1.0' xml:lang='en-US'>
				<voice xml:lang='en-US' xml:gender='Female' name='Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)'>
				{}
				</voice>
			</speak>
				  """.format(text)
		sound_file = requests.post(url, headers=headers, data=payload).content

		with open(file_name, 'wb') as f:
			f.write(sound_file)

		if play_audio:
			mixer.init(14250, -16, 2, 4096)
			mixer.music.load(file_name)
			mixer.music.play(loops=1, start=0.0)
			while mixer.music.get_busy() == True:
				continue
	
	# Sets value in sheet_range in gSheet 
	def set_uw_values(self, sheet_range, value):

		return self.gSheet.set_value(sheet_range, value)

	# Pulls FHA quote from Quote Results in gSheet
	def get_uw_values(self):

		loans = self.gSheet.get_values('Quote Results!A2:AM')
		fha_loan = loans[-1]

		return fha_loan

	# Sends string to bing for address standardization. Uses Bing Maps API
	def get_bing_address(self, address):

		url = 'https://atlas.microsoft.com/search/address/json'
		params = {
			'subscription-key': self.map_key, 
			'api-version': '1.0',
			'query': address
		}
		res = requests.get(url, params=params).json()

		bing_address = {
			'street_numb' : res['results'][0]['address']['streetNumber'],
			'street_name' : res['results'][0]['address']['streetName'],
			'city'        : res['results'][0]['address']['municipality'].split(',')[0],
			'state'       : res['results'][0]['address']['countrySubdivision'],
			'zip'         : res['results'][0]['address']['postalCode'],
			'county'      : res['results'][0]['address']['countrySecondarySubdivision']
		}

		return bing_address

	# Plays chime to prompt user to speak
	def play_prompt(self, file='sounds/blip.mp3'):
		
		mixer.init(20500, -16, 1, 4096)
		mixer.music.load(file)
		mixer.music.play(loops=0, start=0.0)
		while mixer.music.get_busy() == True:
			continue

	# Gets a random thought from Ryan Swanson
	def get_thought(self):

		joke = requests.get('https://ron-swanson-quotes.herokuapp.com/v2/quotes').text
		self.text_to_speech(joke)
		print(joke)


if __name__ == '__main__':
	BING_MAPKEY    = 'eFOm0_-7ZzYVCsi7Dbku3aF85gjHZwVuhGFcBOv2GJ0'
	BING_SPEECHKEY = '8c51ff7c89c9438fa9e720ffa9530db3'
	LUIS_APPID     = 'cab6d4fe-10bc-4ed1-85f6-eccc6b385ad0'
	LUIS_APPKEY    = '8092489ce228440bba290f5e6425204b'
	gSheet_SSKEY   = '1Y9VYZbQeUaRWYxCZlmtpuhcwpZqkbfn6wrbRq_UFNH4'

	vs = Voice_Sizer(BING_MAPKEY, BING_SPEECHKEY, LUIS_APPID, LUIS_APPKEY, gSheet_SSKEY)
import string
import csv

class TAnon:
	"""
	This class provides text anonymization by filtering out any words that don't appear in a whitelist.
	Cleaned data is stored in self.results
	e.g. 
	ta = TextAnon('./radiology_all_accessions_will_label_100.csv')
	ta.anonymize_text(dataframe, 'REPORT_TEXT')
	"""
	whitelist = None

	def __init__(self, whitelistPath):
		"""
		:param whitelistPath: relative path to whitelist csv file
		"""
		whitelist_dict = {}
		with open(whitelistPath, 'r') as data:
			for line in csv.DictReader(data):
				if float(line['Label']) == 0:
					whitelist_dict[line['Word']] = int(float(line['Label']))
		self.whitelist = whitelist_dict

	def processing(self, s):
		symbols = string.punctuation.replace('/', '').replace("'", '').replace(':', '') + ' \n'
		sliced, cut_symbols = self.new_slice(s, symbols)
		for i in range(len(sliced)):
			if sliced[i] and sliced[i] not in self.whitelist:
				sliced[i] = '[REMOVED]'
		return self.new_join(sliced, cut_symbols)

	def new_slice(self, s, symbols):
		sliced = []
		characters = []
		i = 0
		for j in range(len(s)):
			if s[j] in symbols:
				sliced.append(s[i:j])
				characters.append(s[j])
				i = j + 1
		sliced.append(s[i:])
		return sliced, characters

	def new_join(self, sliced, cut_characters):
		answer = ''
		for i in range(len(cut_characters)):
			answer += sliced[i]
			answer += cut_characters[i]
		answer += sliced[-1]
		return answer

	def anonymize_text(self, df_target_column):
		at = df_target_column.apply(lambda s: self.processing(str(s)))
		return at

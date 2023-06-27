import re
import string
import requests
from requests.exceptions import RequestException
from ast import literal_eval
from urllib.parse import quote_plus
from thefuzz import fuzz

def catch_requests_exceptions(func):
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except requests.exceptions.RequestException:
			return None
	return wrapper


def normalize_text(text):
	return ''.join(ch for ch in re.sub(r'[^\w\s-]', '', text.lower()) if ch not in set(string.punctuation))


@catch_requests_exceptions
def search_ror(org_name):
	query_url = f'https://api.ror.org/organizations?affiliation={quote_plus(org_name)}'
	api_response = requests.get(query_url).json()
	ror_matches = {}
	if api_response['number_of_results'] != 0:
		search_results = api_response['items']
		for result in search_results:
			if 'organization' in result.keys():
				record = result['organization']
				ror_id = record['id']
				ror_name = record['name']
				if result['chosen'] == True:
					if 'FundRef' in record['external_ids'].keys():
						funder_id = f"http://dx.doi.org/10.13039/{record['external_ids']['FundRef']['all'][0]}"
						return [{"type": "ror", "id": ror_id, "name":ror_name}, {"type": "funder_registry", "id": funder_id, "name":ror_name}]
					else:
						return [{"type": "ror", "id": ror_id, "name":ror_name}]
				else:
					aliases = record['aliases']
					if record['labels'] != []:
						labels = [label['label'] for label in record['labels']]
						all_names =  [ror_name] + labels + aliases
					else:
						all_names = [ror_name] + aliases
					for name in all_names:
						name_mr = fuzz.ratio(normalize_text(
							org_name), normalize_text(ror_name))
						if name_mr >= 95:
							if 'FundRef' in record['external_ids'].keys():
								funder_id = f"http://dx.doi.org/10.13039/{record['external_ids']['FundRef']['all'][0]}"
								ror_matches[name_mr] = [ror_id, ror_name, funder_id]
							else:
								ror_matches[name_mr] = [ror_id, ror_name]
	if ror_matches == {}:
		return None
	else:
		best_match_score = max(ror_matches.keys())
		best_match = ror_matches[best_match_score]
		if len(best_match) == 3:
			return [{"type": "ror", "id": best_match[0], "name":best_match[1]}, {"type": "funder_registry", "id": best_match[2], "name":best_match[1]}]
		else:
			return [{"type": "ror", "id": best_match[0], "name":best_match[1]}]


def is_like_identifier(s):
	pattern = "^(?=.*[0-9])(?=.*[A-Z])[A-Z0-9\s\\-]+$"
	if re.match(pattern, s):
		return True
	return False


def search_funder_ids(parsed_funders):
	parsed_funders = [literal_eval(funder) for funder in parsed_funders]
	parsed_funders = [funder for funder in parsed_funders if not is_like_identifier(funder['funder'])]
	for funder in parsed_funders:
		org_name = funder['funder']
		matches = search_ror(org_name)
		if matches != None:
			funder['ids'] = matches
	return parsed_funders


from parse_acknowledgements import parse_acknowledgements
from search_funder_ids import search_funder_ids
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route('/')
def index():
	return render_template('index.html')

@app.route('/process')
def process():
	form_input = request.args.get('q')
	parsed_funders = parse_acknowledgements(form_input)
	matched_w_ids = search_funder_ids(parsed_funders)
	return jsonify(matched_w_ids)

if __name__ == '__main__':
	app.run(debug=True)
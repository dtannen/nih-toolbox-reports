#!/usr/bin/python
import sys
import math
import pandas
from jinja2 import Environment, FileSystemLoader
from scipy.stats import norm
#from weasyprint import HTML

def clean_registry(df):
	df['PIN'] = df.PIN.str.replace("Cip", "")
	df['record_number'] = "CIP" + df.PIN
	return df

def clean_scores(df):
	df['PIN'] = df.PIN.apply(str)
	df['SD'] = (df.TScore - 50) / 10.0
	df['variable'] = df.Inst.str.extract("\- (.*)", expand = False).str.replace(" 3a", "")
	df['test_date'] = pandas.to_datetime(df.DateFinished)
	df['percentile'] = norm(50, 10).cdf(df.TScore).round(2) * 100
	df['percentile'] = df.percentile.astype(int)
	df['SD'] = df.SD.where(~df.variable.isin(["Emotional Support", "Physical Function"]), -df.SD.values)
	return df

def create_table(df):
	df = df[["Inst", "TScore", "percentile"]]
	df.columns = ["Instrument", "T-score", "Percentile"]
	df = df.sort_values("Instrument")
	df = df.reset_index(drop = True)
	return df

def create_list(df, low = -math.inf, high = math.inf):
	list = df[(df.SD > low) & (df.SD < high)].variable
	str = ", ".join(list)
	return str

def create_recommendations(df):
	db = {
		"Pain Intensity" : "Will continue to diagnose and treat patient's pain problem.",
		"Pain Interference" : "Will continue to diagnose and treat patient's pain problem.",
		"Anger" : "Patient is recommended to practice mindfulness meditation.",
		"Anxiety" : "Patient may benefit from dual use medication for pain and mood and employing non-pharmacologic strategies such as mindfulness meditation and/or CBT. Consider Psychiatry referral.",
		"Physical Function" : "Patient will benefit from improvement in physical function through structured activity, including physical therapy and personalized home exercise program.",
		"Emotional Support" : "Patient will benefit from group therapy to foster a support system and appropriate coping strategies.",
		"Social Isolation" : "Patient will benefit from group therapy to foster a support system and appropriate coping strategies.",
		"Satisfaction Roles Activities" : "Patient will benefit from improvement in physical function through structured activity, including physical therapy and personalized home exercise program.",
		"Depression" : "Patient may benefit from dual use medication for pain and mood and employing non-pharmacologic strategies such as mindfulness meditation and/or CBT. Consider Psychiatry referral.",
		"Sleep Disturbance" : ""
	} 

	df['recommendation'] = df.variable.map(db)
	df['recommendation'] = df.recommendation.where(df.SD > 1, None)

	if df.SD.max() < 1:
		df['recommendation'] = "None at this time, patient is within normal limits across all domains."
	elif sum(df.SD.values > 1) > 7: 
		df['recommendation'] = "Patient displays moderate to severe multidimensional psychological overlay and will require multidisciplinary treatment approach."

	df = df.recommendation.dropna()
	return " ".join(df.unique())

if __name__ == "__main__":
	infile1 = sys.argv[1]
	infile2 = sys.argv[2]

	registry = pandas.read_csv(infile1)
	scores = pandas.read_csv(infile2)

	registry = clean_registry(registry)
	scores = clean_scores(scores)

	env = Environment(loader = FileSystemLoader("./template/"))
	template = env.get_template("report.html")

	for patient_id in registry.PIN.unique():
		patient_data = registry[registry.PIN == patient_id]
		patient_scores = scores[scores.PIN == patient_id]
		outfile = patient_data.record_number.to_string(index = False) + " " + patient_scores.test_date.dt.strftime("%Y-%d-%m").max()
		template_vars = {
				"title" : outfile,
				"patient_name" : patient_data.Name.to_string(index = False),
				"record_number" : patient_data.record_number.to_string(index = False),
				"test_date" : patient_scores.test_date.dt.strftime("%m/%d/%Y").max(),
				"table" : create_table(patient_scores).to_html(index = False, classes = "u-full-width", border = 0),
				"severe_variables" : create_list(patient_scores, low = 2),
				"moderate_variables" : create_list(patient_scores, low = 1, high = 2),
				"average_variables" : create_list(patient_scores, low = 0, high = 1),
				"treatment_recommendations" : create_recommendations(patient_scores) 
			}

	html = template.render(template_vars)
	with open(outfile + ".html", "w") as f:
		f.write(html)
	#HTML(string = html).write_pdf(, stylesheets = "")


		

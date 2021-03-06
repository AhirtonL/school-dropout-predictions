##################################
##								##
##	Machine Learning Pipeline 	##
##	Bridgit Donnelly			##
##								##
##################################

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pylab
import sys, re, csv
import time
import sklearn as sk
from sklearn.cross_validation import KFold
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier#, GradientBoostingClassifier, BaggingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import LinearSVC
#from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, precision_recall_curve

# Code adapted from https://github.com/yhat/DataGotham2013/

'''
NOTE: Main function for this file only loads and produces summary statistics in 
order to allow the user to make decisions about data imputation and feature generation
based on the user's understanding of the data.
'''

## STEP 1: READ DATA IN CSV FORM

def read_data(filename):
	'''
	Takes a filename and returns a dataframe.
	'''
	original = pd.read_csv(filename, header=0, index_col='id')
	df = original.copy()
	return df

def camel_to_snake(column_name):
    """
    Converts a string that is camelCase into snake_case
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', column_name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def line_count(dataset):
		with open(dataset, 'rU') as data_file:
			reader = csv.reader(data_file)
			lines = list(reader)
			#Total File Rows
			XR = len(lines)
			return XR

# ---------------------------------------------------------------------

## STEP 2: EXPLORE DATA - generate distributions and data summaries

def getSumStats(data):
    desc = data.iloc[:,1:].describe().T
    desc.drop([desc.columns[4], desc.columns[6]], axis=1, inplace=True)
    mode = data.iloc[:,1:].mode()
    desc = pd.concat([desc.T, mode])
    desc.rename({0:'mode', '50%':'median'}, inplace=True)
    desc.to_csv("ml_sumstats.csv")


def summarize(df):
	'''
	Given a dataframe and the original filename, this outputs a CSV with an adjusted filename.
	Return the summary table.
	'''

	# Create Summary Table
	summary = df.describe().T

	# Add Median & Missing Value Count
	summary['median'] = df.median()
	summary['missing_vals'] = df.count().max() - df.describe().T['count'] # Tot. Count - count
	
	output = summary.T
	return output

def print_to_csv(df, filename):
	''' Given a dataframe and a filename, outputs a CSV.'''

	# Check that filename was CSV
	filename_split = str(filename).strip().split('.')

	if filename_split[-1] != 'csv':
		filename = "".join(filename_split[0:len(filename_split)-1]) + ".csv"

	df.to_csv(filename)

def histogram1(variable, data, color, bins):

	#Generate Graph
	fig = data[variable].hist(bins=bins, color=color)
	fig.set_xlabel(variable) #defines the x axis label
	fig.set_ylabel('Number of Observations') #defines y axis label
	fig.set_title(variable+' Distribution') #defines graph title
	plt.draw()
	plt.savefig("output/histograms/"+variable+"_histogram1_"+str(bins)+".jpg")
	plt.clf()


def histogram2(variable, data, color, np1, np2):

	#Generate Graph
	fig = data[variable].hist(bins=np.arange(np1, np2), color=color)
	fig.set_xlabel(variable) #defines the x axis label
	fig.set_ylabel('Number of Observations') #defines y axis label
	fig.set_title(variable+' Distribution') #defines graph title
	plt.draw()
	plt.savefig("output/histograms/"+variable+"_histogram2_"+str(np1)+".jpg")
	plt.clf()


def summarize_dataset(df):
	"""Select dataset to summarize. Use this function to summarize a dataset.
	To focus on specific variables, please use summary_statistics instead."""

	#Define Data
	df.columns = [camel_to_snake(col) for col in df.columns]

	for variable in df.columns:

		print "_"*50
		print "Summary Statistics "+str(variable)+": "
		count = (df[str(variable)].count())
		print "Missing values: ", df.count().max() - df.describe().T['count']
		print "Describe "+str(variable)+": ", '\n', (df[str(variable)].describe())
		print "Mode: ", (df[str(variable)].mode())
		#Histogram
		if count > 1:
			try:
				histogram1(str(variable), df, 'c', 5)
				histogram1(str(variable), df, 'g', 10)
				histogram2(str(variable), df, 'b', 1.5, 10)
				histogram2(str(variable), df, 'r', 1, 10)
			except:
				pass



def summary_statistics(variable, data, bin1=5, bin2=10):
	"""Select variable to summarize. Please input the dataset.
		Histogram bins can be modified. Default is 5 and 10."""

	print "_"*50
	print "Summary Statistics "+str(variable)+": "
	count = (data[str(variable)].count())
	print "Missing values: ", data.count().max() - data.describe().T['count']
	print "Describe "+str(variable)+": ", '\n', (data[str(variable)].describe())
	print "Mode: ", (data[str(variable)].mode())
	#Histogram
	try:
		if count > 1:
			histogram1(str(variable), dataset, 'c', bin1)
			histogram1(str(variable), dataset, 'g', bin2)
			histogram2(str(variable), dataset, 'b', (bin1/float(4)), bin2)
			histogram2(str(variable), dataset, 'r', (bin1/float(5)), bin2)
	except:
		pass


# ---------------------------------------------------------------------

## STEP 3: PRE-PROCESS DATA - Fill in misssing values

def replace_with_value(df, variables, values):
	'''
	For some variables, we can infer what the missing value should be.
	This function takes a dataframe and a list of variables that match
	this criteria and replaces null values with the specified value.
	'''
	if len(variables) <= 2:
		variable = variables
		value = values
		df[variable] = df[variable].fillna(value)

	elif len(variables) > 2:
		for i in range(len(variables)):
			variable = variables[i]
			value = values[i]
			df[variable] = df[variable].fillna(value)



def replace_with_mean(df, variables):
	'''
	For some variables, imputing missing values with the variable mean 
	makes the most sense.
	This function takes a dataframe and a list of variables that match 
	this criteria and replaces null values with the variable's mean.
	'''
	# Find means for each field
	for field in variables:
		mean = df[field].mean()

		# Replace Null Values
		for index, row in df.iterrows():
			if pd.isnull(row[field]):
				df.ix[index, field] = mean

def replace_if_missing(df, variable_missing, variable_fill):
	'''
	Takes a variable and replaces missing values (variable_missing) with
	data from another column (variable_fill).
	'''

	for index, row in df.iterrows():
		if pd.isnull(row[variable_missing]):
			df.ix[index, variable_missing] = row[variable_fill]

def replace_dummy_null_mean(df, null_col, destination_cols):
	'''
	Takes a null column resulting from get_dummies and imputes the mean 
	of the destination columns.
	'''
	for field in destination_cols:
		mean = df[field].mean()
	
		for index, row in df.iterrows():
			if row[null_col] == 1:
				df.ix[index,field] = mean


##################
## TO ADD LATER ##
def replace_class_conditional(df, variables, field):
	'''
	For some variables, we want to impute the missing values by certain
	class-conditional means.
	This function takes a dataframe and a list a variables that match this 
	criteria, as well as the field to use to determine classes. It finds 
	each unique value of the provided class and imputes mean values based on 
	those classes.
	'''
	pass
##################

def impute(df, variable, cols):
	'''
	For some variables, we cannot infer the missing value and replacing with
	a conditional mean does not make sense.
	This function takes a dataframe and a variables that matches this criteria 
	as well as a list of columns to calibrate with and uses nearest neighbors 
	to impute the null values.
	'''
	# Split data into test and train for cross validation
	is_test = np.random.uniform(0, 1, len(df)) > 0.75
	train = df[is_test==False]
	validate = df[is_test==True]
	
	## Calibrate imputation with training data
	imputer = KNeighborsRegressor(n_neighbors=1)

	# Split data into null and not null for given variable
	train_not_null = train[train[variable].isnull()==False]
	train_null = train[train[variable].isnull()==True]

	# Replace missing values
	imputer.fit(train_not_null[cols], train_not_null[variable])
	new_values = imputer.predict(train_null[cols])
	train_null[variable] = new_values

	# Combine Training Data Back Together
	train = train_not_null.append(train_null)

	# Apply Nearest Neighbors to Validation Data
	new_var_name = variable + 'Imputed'
	validate[new_var_name] = imputer.predict(validate[cols])
	validate[variable] = np.where(validate[variable].isnull(), validate[new_var_name],
								validate[variable])


	# Drop Imputation Column & Combine Test & Validation
	validate.drop(new_var_name, axis=1, inplace=True)
	df = train.append(validate)

	''' FOR FUTURE
	# Apply Imputation to Testing Data
	test_df[new_var_name] = imputer.predict(test_df[cols])
	test_df[variable] = np.where(test_df[variable].isnull(), test_df[new_var_name],
								test_df[variable])
	'''

	return df.sort_index()
	

# ---------------------------------------------------------------------

## STEP 4: GENERATE FEATURES - write a function to discretize a continuous variable
## and a function that can take a categorical variable and create binary variables.

def find_features(df, features, variable):
	'''Uses random forest algorithm to determine the relative importance of each
	potential feature. Takes dataframe, a numpy array of features, and the dependent
	variable. Outputs dataframe, sorting features by importance'''
	clf = RandomForestClassifier()
	clf.fit(df[features], df[variable])
	importances = clf.feature_importances_
	sort_importances = np.argsort(importances)
	rv = pd.DataFrame(data={'variable':features[sort_importances],
							'importance':importances[sort_importances]})
	return rv

def adjust_outliers(x, cap):
	'''Takes series and creates upperbound cap to adjust for outliers'''
	if x > cap:
		return cap
	else:
		return x

def bin_variable(df, variable, num_bins, labels=None):
	'''Discretizes a continuous variable based on specified number of bins'''
	new_label = variable + '_bins'
	df[new_label] = pd.cut(df[variable], bins=num_bins, labels=labels)


# ---------------------------------------------------------------------

## STEP 5: BUILD AND EVALUATE CLASSIFIERS - Create comparison table of the performace
## of each classifier on each evaluation metric

def build_classifiers(df, X, y, classifiers):
	'''
	Takes a dataframe of features (X) and a dataframe of the variable to predict (y). 
	Returns a new dataframe comparing each classifier's performace on 
	the given evaluation metrics.
	'''
	index = 0

#	import IPython
# 	IPython.embed()

	for name, clf in classifiers:
		print "Building " + name + '...'

		# Construct K-folds
		kf = KFold(len(y), n_folds=5, shuffle=True)
		y_pred = y.copy()

		# Iterate through folds
		for train_index, test_index in kf:
			X_train, X_test = X.iloc[train_index], X.iloc[test_index]
			y_train = y.iloc[train_index]

			import IPython
			IPython.embed()

			#Initialize classifier
			model = clf
			model.fit(X_train, y_train)
			y_pred.iloc[test_index] = model.predict(X_test)

		test_classifier(df, X, y, y_pred, name)
		evaluate_classifier(name, index, y, y_pred)
		index += 1

#	return rv

def test_classifier(df, X, y, y_pred, name):
	'''
	Takes a dataframe (df), column names of predictors (X) and a dependent
	variable (y). Loops over generic classifiers to find predictions. Creates
	a decision tree using prediction misclassification as the dependent variable.
	'''

	var_name = name + '_predict'
	try:
		df[var_name] = y_pred
	except:
		import pdb
		pdb.set_trace()
	correct = name + '_correct'
	
	# Determine "correctness" based on 0.5 threshold
	df[correct] = (df[var_name] > 0.5).astype(int)

	# Determine which observations are being misclassified
	tree = DecisionTreeClassifier(max_depth=5)
	tree.fit(df[X.columns], df[correct])
	get_tree_decisions(tree, df.columns)

# Borrowed heavily from http://stackoverflow.com/questions/20224526/how-to-extract-the-decision-rules-from-scikit-learn-decision-tree
def get_tree_decisions(tree, feature_names):
    left      = tree.tree_.children_left
    right     = tree.tree_.children_right
    threshold = tree.tree_.threshold
    features  = [feature_names[i] for i in tree.tree_.feature]
    value = tree.tree_.value

    def recurse(left, right, threshold, features, node):
            if (threshold[node] != -2):
                    print "if ( " + features[node] + " <= " + str(threshold[node]) + " ) {"
                    if left[node] != -1:
                            recurse (left, right, threshold, features,left[node])
                    print "      } else {"
                    if right[node] != -1:
                            recurse (left, right, threshold, features,right[node])
                    print "}"
            else:
                    print "return " + str(value[node])

    recurse(left, right, threshold, features, 0)
	
def evaluate_classifier(model, index, y_real, y_predict):
	'''
	For an index of a given classifier, evaluate it by various metrics
	'''
	
	rv = []
	rv.loc[index,'classifier'] = name

	# Metrics to evaluate
	metrics = [('baseline', (1 - y_real.mean()))
				('accuracy', accuracy_score(y_real, y_predict)),
				('precision', precision_score(y_real, y_predict)),
				('recall', recall_score(y_real, y_predict)),
				('f1', f1_score(y_real, y_predict)),
				('area_under_curve', roc_auc_score(y_real, y_predict))]

	for name, m in metrics:
		rv.loc[index, name] = m

	print_to_csv(rv, 'compare_classifiers.csv')
	plot_precision_recall_curve(y_real, y_predict, model)



def plot_precision_recall_curve(y_real, y_predict, model):
	# Compute Precision-Recall and plot curve
	precision, recall, thresholds = precision_recall_curve(y_test, y_score[:, 1])
	area = auc(recall, precision)
	print "Area Under Curve: %0.2f" % area

	pl.clf()
	pl.plot(recall, precision, label='Precision-Recall curve')
	pl.xlabel('Recall')
	pl.ylabel('Precision')
	pl.ylim([0.0, 1.05])
	pl.xlim([0.0, 1.0])
	pl.title('Precision-Recall example: AUC=%0.2f' % area)
	pl.legend(loc="lower left")

	plt.draw()
	plt.savefig("output/evaluation/"+model+"_precision-recall-curve"+".jpg")
	plt.clf()


# -------------------------------------------------------------------------
if __name__ == '__main__':
	
	if len(sys.argv) <= 1:
		sys.exit("Must include a filename.")

	else:
		dataset = sys.argv[1]
		
		## Load data 
		df = read_data(dataset)
		variables = list(df.columns.values)

		## Run initial summary statistics & graph distributions
		summary = summarize(df)
		#print_to_csv(summary, 'summary_stats.csv')
		
		for v in variables:
			histogram(df, v)

		



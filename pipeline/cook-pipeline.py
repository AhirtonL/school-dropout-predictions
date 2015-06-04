'''
Christine Cook
Machine Learning
PA 3
'''

import pandas as pd 
import numpy as np
import pylab as pl 
import csv, time
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, BaggingClassifier
from sklearn.metrics import roc_curve, auc, accuracy_score, precision_score, f1_score, recall_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn import tree, datasets, linear_model
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier  


def getSumStats(data):
    desc = data.iloc[:,1:].describe().T
    desc.drop([desc.columns[4], desc.columns[6]], axis=1, inplace=True)
    mode = data.iloc[:,1:].mode()
    desc = pd.concat([desc.T, mode])
    desc.rename({0:'mode', '50%':'median'}, inplace=True)
    desc.to_csv("data_sumstats.csv")

def cleanData(data, cohort):
    if cohort == 1:
        variables_to_drop = ['g6_tardyr','g6_school_name', 'g7_school_name', 'g8_school_name', 'g9_school_name', 'g10_school_name', 'g11_school_name', 'g12_school_name','g6_year', 'g6_gradeexp', 'g6_grade', 'g6_wcode', 'g7_year', 'g7_gradeexp', 'g7_grade', 'g7_wcode', 'g8_year', 'g8_gradeexp', 'g8_grade', 'g8_wcode', 'g9_year', 'g9_gradeexp', 'g9_grade', 'g9_wcode', 'g10_year', 'g10_gradeexp', 'g10_grade', 'g10_wcode', 'g11_year', 'g11_gradeexp', 'g11_grade', 'g11_wcode', 'g12_year', 'g12_gradeexp', 'g12_grade', 'g12_wcode']
        data.drop(variables_to_drop, axis=1, inplace=True)
        
    elif cohort == 2:
        variables_to_drop = ['g6_school_name', 'g7_school_name', 'g8_school_name', 'g9_school_name', 'g10_school_name', 'g11_school_name', 'g12_school_name','g6_year', 'g6_grade', 'g6_wcode', 'g7_year', 'g7_grade', 'g7_wcode', 'g8_year', 'g8_grade', 'g8_wcode', 'g9_year', 'g9_grade', 'g9_wcode', 'g10_year', 'g10_grade', 'g10_wcode', 'g11_year', 'g11_grade', 'g11_wcode', 'g12_year', 'g12_grade', 'g12_wcode']
        data.drop(variables_to_drop, axis=1, inplace=True)

    ## Create single column for birth year
    data['birthday'] = data['g11_byrmm']
    birthday_cols = ['g12_byrmm', 'g10_byrmm', 'g9_byrmm', 'g8_byrmm', 'g7_byrmm', 'g6_byrmm']
    for c in birthday_cols:
        ml.replace_if_missing(data, 'birthday', c)
        data.drop(c, axis=1, inplace=True)
    
    data['birth_year'] = data.loc[:,'birthday'].astype(str, copy=False)[:4]
    data['birth_month'] = data.loc[:,'birthday'].astype(str, copy=False)[4:]
    data.drop('birthday', axis=1, inplace=True)

    ## Create single column for gender
    data['gender'] = data['g11_gender']
    gender_cols = ['g12_gender', 'g11_gender', 'g10_gender', 'g9_gender', 'g8_gender', 'g7_gender', 'g6_gender']
    for c in gender_cols:
        ml.replace_if_missing(data, 'gender', c)
        data.drop(c, axis=1, inplace=True)

    #clean retained
    retained_cols = ['g11_retained', 'g12_retained', 'g9_newmcps', 'g10_newmcps', 'g11_newmcps', 'g12_newmcps', 'g9_newus', 'g10_newus', 'g11_newus', 'g12_newus']
    for col in retained_cols:
        data[col] = data[col].notnull()

    #create flag if a given student is missing a year's worth of data
    grade_id = ['g6_pid', 'g7_pid', 'g8_pid', 'g9_pid', 'g10_pid', 'g11_pid', 'g12_pid']
    year = 6
    for g in grade_id:
        col_name = 'g' + str(year) + '_missing'
        data[col_name] = data[g].isnull()
        data.drop(g, axis=1, inplace=True)
        year+=1

    return data

def makeDummies(data):
    school_ids = [col for col in data.columns if 'school_id' in col]
    data[school_ids] = data.loc[:,school_ids].astype(str, copy=False)

    string_cols = list(data.select_dtypes(include=['object']))
    
    data = pd.get_dummies(data[string_cols], dummy_na=True)
    
    data.drop(list(data.select_dtypes(include=['object'])), axis=1, inplace=True)

    return data

def chooseCols(data, pred_grade):
    for x in range(pred_grade, 12):
        dropVars = [col for col in data.columns if str(x) in col]
        dropoutVar = 'g' + str(pred_grade) + '_dropout'
        dropVars.remove(dropoutVar)
        data.drop(dropVars, axis=1, inplace=True)

    return data

def imputeData(data):
    #change msam to missing is msam_NA==1
    nanList =  ['g6_g6msam_nan', 'g7_g7msam_nan', 'g8_g8msam_nan', 'g9_g8msam_nan']
    msamList = [[ 'g6_g6msam_Advanced', 'g6_g6msam_Basic', 'g6_g6msam_Proficient'], ['g7_g7msam_Advanced', 'g7_g7msam_Basic', 'g7_g7msam_Proficient'], ['g8_g8msam_Advanced', 'g8_g8msam_Basic', 'g8_g8msam_Proficient'],['g9_g8msam_Advanced', 'g9_g8msam_Basic', 'g9_g8msam_Proficient']]
    for x in range(0,len(nanList)):
        nacol = nanList[x]
        colList = msamList[x]
        for col in colList:
            df.loc[df[nacol] == 1, col] = np.nan 


    #pred missing data using any available data
    wordList = ['absrate', 'mapr', 'msam_Advanced', 'msam_Basic', 'msam_Proficient', 'mobility', 'nsusp', 'mpa', 'tardyr', 'psatm', 'psatv', 'retained']
    for word in wordList:
        colList = [col for col in df.columns if word in col]
        rowMean = df[colList].mean(axis=1)
        for col in colList:
            df[col].fillna(rowMean, inplace=True)

    return data

def limitRows(data, pred_grade):
    #get rid of previous dropouts
    for x in range(6, pred_grade-1):
        doVar = 'g' + str(x) + '_dropout'
        data = data[data[doVar] !=1 ]

    #get rid of people missing in previous yr
    #mVar = 'g' + str(pred_grade-1) + '_missing'
    #data = data[data[mVar] !=1 ]

    return data

def makeChartDiscrete(data, col, title):
    data_copy = data
    data_copy = data_copy.dropna()
    data_max = data_copy.iloc[:,col].max()
    step = (data_max/50)
    if step < 1:
        bins=list(range(0, int(data_max), 1))
    else:
        bins=list(range(0, int(data_max), step))
    pl.figure()
    pl.title(title)
    pl.xlabel(title)
    pl.ylabel('Frequency')
    bins = pl.hist(data_copy.iloc[:,col], bins)
    pl.savefig(title)

def makeChartContinuous(data, col, title):
    y_vals = data.iloc[:,col]
    data_id = data.iloc[:,0]
    pl.figure()
    pl.title(title)
    pl.xlabel(title)
    pl.ylabel('Frequency')
    pl.scatter(y_vals,data_id)
    pl.savefig(title)

def imputeMean(data):
    data.fillna(value=data.mean(), inplace=True)
    return data

def plotROC(name, probs, test_data):
    fpr, tpr, thresholds = roc_curve(test_data['SeriousDlqin2yrs'], probs)
    roc_auc = auc(fpr, tpr)
    pl.clf()
    pl.plot(fpr, tpr, label='ROC curve (area = %0.2f)' % roc_auc)
    pl.plot([0, 1], [0, 1], 'k--')
    pl.xlim([0.0, 1.05])
    pl.ylim([0.0, 1.05])
    pl.xlabel('False Positive Rate')
    pl.ylabel('True Positive Rate')
    pl.title(name) 
    pl.legend(loc="lower right")
    pl.savefig(name)

def evaluateClassifier(name, y_true, y_pred, probs, test_data):
    # precision, recall, F1 scores, accuracy
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    # ROC curve, AUC on fig
    plot_roc("Perfect Classifier", test_data['SeriousDlqin2yrs'], test_data)
    plot_roc("Guessing", np.random.uniform(0, 1, len(test_data['SeriousDlqin2yrs'])), test_data)
    plotROC(name, probs, test_data)
    return precision, recall, f1



def main():
    #read data
    data = pd.read_csv('DATA_DO_NOT_UPLOAD/clean_data_cohort1.csv', index_col=False)

    #clean data
    data = cleanData(data, 1)

    #make dummies
    data = makeDummies(data)

    #shrink dataset size
    data = chooseCols(data, 12)

    #impute data
    data = imputeData(data)

    #limit rows to valid
    data = limitRows(data, 12)

    # define parameters
    #names = ["Nearest Neighbors", "Linear SVM", "Decision Tree", "Random Forest", "AdaBoost", "Linear Regression", "Bagging"]
    #classifiers = [KNeighborsClassifier(3), LinearSVC(C=0.025), DecisionTreeClassifier(max_depth=5), RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1), AdaBoostClassifier(), linear_model.LinearRegression(), BaggingClassifier()]

    names = ["Decision Tree"]
    classifiers = [DecisionTreeClassifier(max_depth=2)]

    # split data
    for x in range(0,2):
        print "\nFold: " + str(x)

        train_data, test_data = train_test_split(data, test_size=.2)

        # define Xs, Y
        X_train = train_data.iloc[:,2:]
        y_train = train_data.iloc[:,1]
        X_test = test_data.iloc[:,2:]
        y_test = test_data.iloc[:,1]

        clf_results = {}

        # loop through classifiers, get predictions, scores
        for name, clf in zip(names, classifiers):

            #time training
            start_time = time.clock()
            clf.fit(X_train, y_train)
            end_time = time.clock()
            training_time = (end_time - start_time)

            #time testing
            start_time = time.clock()
            if (name=="Linear Regression") | (name=="Linear SVM"):
                probs = clf.predict(X_test)
                preds = probs.round()
            else:
                preds = clf.predict(X_test)
                probs = clf.predict_proba(X_test)[::,1]
            end_time = time.clock()
            testing_time = (end_time - start_time)

            # evaluate classifier
            precision, recall, f1 = evaluateClassifier(name, y_test, preds, probs, test_data)
            accuracy = clf.score(X_test, y_test)

            # add results to dict
            clf_results[name] = {}
            clf_results[name]['accuracy'] = accuracy
            clf_results[name]['precision'] = precision
            clf_results[name]['recall'] = recall
            clf_results[name]['f1'] = f1
            clf_results[name]['testing time'] = testing_time
            clf_results[name]['training time'] = training_time


        print clf_results

        with open('trial_' + str(x) + '.csv', 'wb') as f:
            w = csv.DictWriter(f, clf_results.keys())
            w.writeheader()
            w.writerow(clf_results)
    
    print "End"

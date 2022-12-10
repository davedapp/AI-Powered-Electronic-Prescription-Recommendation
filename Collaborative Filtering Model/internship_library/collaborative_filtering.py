#Library
import pandas as pd
import numpy as np
import json
import time
from operator import itemgetter
#from sklearn.model_selection import train_test_split

  
def load_medicineData(medicinePath="C:/Users/Dave/Internship Data/Progress 1 (Gath &Cl)/clean_medicines_091121.csv", medicinePrescPath="C:/Users/Dave/Internship Data/Progress 1 (Gath &Cl)/clean_medicine_prescription_091121.csv", medicine_dosePath="C:/Users/Dave/Internship Data/Progress 4 (Collaborative Filtering)/meds_with_dose.csv"):
  medicine = pd.read_csv(medicinePath)
  medicinePresc = pd.read_csv(medicinePrescPath)
  medicine_dose = pd.read_csv(medicine_dosePath)
  return medicine, medicinePresc, medicine_dose

#Read presciption and patient files
def load_prescPatData(fullPrescPath = "C:/Users/Dave/Internship Data/Progress 3 (Data Splitting)/80 Percent Used/prescription_reduced.csv", allPrescPath="C:/Users/Dave/Internship Data/Progress 6 (Deployment)/allPresc.csv", patientsPath="C:/Users/Dave/Internship Data/Progress 6 (Deployment)/patients.csv", allPivotPath = "C:/Users/Dave/Internship Data/Progress 6 (Deployment)/allPivot.csv"): 
  fullPresc = pd.read_csv(fullPrescPath)
  allPresc = pd.read_csv(allPrescPath)
  patients = pd.read_csv(patientsPath)
  allPivot = pd.read_csv(allPivotPath)
  return fullPresc, allPresc, patients, allPivot 

#Prepro Data
def prepro(allPresc, patients, allPivot):
  patientIds = set(allPresc['patientId'])
  prescIds = set(allPresc['id'])
  realPatients = patients[patients['id'].isin(patientIds)]
  realPivot = allPivot[allPivot['id'].isin(prescIds)]
  realPresc = allPresc[allPresc['id'].isin(realPivot['id'])]
  return realPresc, realPatients, realPivot

#json.loads
def similarityICD10(newPresc, allPresc):
  newData = json.loads(newPresc['differentialDiagnosis'])
  allData = json.loads(allPresc['differentialDiagnosis'])
  #print("newData: ", newData)
  #print("allData: ", allData)
  count = 0 
  for i in newData:
    if i in allData:
      count += 1
  similarity = ((count)/len(newData)) * 4
  return similarity


def filterICD10(newPresc, allPresc, threshold=2.05):
  dictTemp = dict()
  for idx, record in allPresc.iterrows():
    #print(record['id'])
    sim = similarityICD10(newPresc, record)
    #print(sim)
    dictTemp[record['id']] = {'patientId': record['patientId'],'similarity': sim}
  filtered = dict((k, v) for k, v in dictTemp.items() if v['similarity'] >= threshold)
  prescId = [*filtered]
  #print(prescId)
  allPrescFiltered = allPresc[allPresc['id'].isin(prescId)]
  return filtered, allPrescFiltered


def findSimilarityScore(newPresc, allPresc, icdSim, patients):
  totalScore = icdSim.get(allPresc['id'], {}).get('similarity')
  ageCategory = ['Child', 'Adolescence', 'Adult', 'Senior Adult']
  BMICategory = ['Underweight','Normal','Overweight']

  age1 = patients.loc[patients['id'] == newPresc['patientId'],'patientAgeCategory'].iloc[0]
  #print("age1:", age1)
  age2 = patients.loc[patients['id'] == allPresc['patientId'],'patientAgeCategory'].iloc[0]
  #print("age1:", age1)

  index1 = ageCategory.index(age1)
  index2 = ageCategory.index(age2)
  if index1 != index2:
    totalScore += 1 - ((abs(index1-index2))/4)
  else:
    totalScore += 1

  # bmi score (yang lama)
  bmi1 = patients.loc[patients['id'] == newPresc['patientId'],'patientBMICategory'].iloc[0]
  #print("bmi1:", bmi1)
  bmi2 = patients.loc[patients['id'] == allPresc['patientId'],'patientBMICategory'].iloc[0]
  #print("bmi2:", bmi2)
  if bmi1 == bmi2:
    totalScore += 1
    totalScore *= 4
  else:
    totalScore += 0
 
  # gender score
  if newPresc["patientGender"] == allPresc["patientGender"]:
    totalScore += 1
  else:
    totalScore += 0
  return totalScore

def getSimilarPrescriptions(newPresc, allPresc, icdSim, patients):
  dictTemp = dict()
  for idx, record in allPresc.iterrows():
    #print("pertama:",record['id'])
    sim = findSimilarityScore(newPresc, record, icdSim, patients)
    dictTemp[record['id']] = sim
    #print("kedua: ", record['id'])
  mostSimilar = dict(sorted(dictTemp.items(), key=itemgetter(1), reverse=True))
  #print(mostSimilar)
  return mostSimilar

def getMedicine(similarPresc, allPivot):
  prescId = similarPresc.keys()
  medList = dict()
  prescResult = allPivot[allPivot['id'].isin(prescId)]
  for idx, row in prescResult.iterrows():
      tempString = 'medicineBrand'
      for i in range(5):
          stringCounter = str(i+1)
          meds = tempString+stringCounter
          #print(medList)
          if (not pd.isnull(row[meds])):
              if(row[meds] not in medList):
                  medList[row[meds]] = 1
              else:
                  medList[row[meds]] += 1       
  return dict(sorted(medList.items(), key=itemgetter(1), reverse=True)[:10])

def getGTMedicine(testRow):
  meddList = dict()
  tempString = 'medicineBrand'
  for i in range(5):
      stringCounter = str(i + 1)
      meds = tempString + stringCounter
      if (not pd.isnull(testRow[meds].all())):
          if (testRow[meds].all() not in meddList or testRow[meds].all() is not np.nan):
              meddList[testRow[meds].all()] = 1
  return meddList

def getMedicineDosage(medList, medicine_dose):
  doseDict = dict()
  medError = ["OBH 200 IKAP sir Komb btl 200 ml", "Nystatin NOVE susp100.000 IU/ml btl 15 ml"]
  medBrand = [*medList]
  #print(medBrand)
  for i in medError:
    if i in medBrand: medBrand.remove(i)
  if len(medBrand)==0:
    pass
  else:
    for brand in medBrand:
    #  if brand in medicine_dose['brand']:
          #print("frequency: ", medicine_dose.loc[medicine_dose['brand'] == brand, 'frequency'].values[0])
          #print("frequencyDd: ", medicine_dose.loc[medicine_dose['brand'] == brand, 'frequencyDd'].values[0])
          #print("timing: ", medicine_dose.loc[medicine_dose['brand'] == brand, 'timing'].values[0])
          #print("duration: ", medicine_dose.loc[medicine_dose['brand'] == brand, 'duration'].values[0])
          #print("amount: ", medicine_dose.loc[medicine_dose['brand'] == brand, 'amount'].values[0])
          doseDict[brand] = {'frequency': medicine_dose.loc[medicine_dose['brand'] == brand, 'frequency'].values[0],
                             'frequencyDd': medicine_dose.loc[medicine_dose['brand'] == brand, 'frequencyDd'].values[0],
                             'timing': medicine_dose.loc[medicine_dose['brand'] == brand, 'timing'].values[0],
                             'duration': medicine_dose.loc[medicine_dose['brand'] == brand, 'duration'].values[0],
                             'amount': medicine_dose.loc[medicine_dose['brand'] == brand, 'amount'].values[0]}
      #else:
       #   pass
  return doseDict

def reCall(prediction, groundTruth):
    count = 0
    for i in groundTruth:
        if i in prediction:
            count += 1
    if len(groundTruth) > 0 :
        recall = float(count / len(groundTruth))
        return recall
    else:
        return 0

def Precision(prediction, groundTruth):
  count = 0
  for i in groundTruth:
    if i in prediction:
        count += 1
  if len(prediction) > 0:
    precision = float(count / len(prediction))
    return precision
  else:
    return 0

def f1Score(recall, precision):
  if (float(precision + recall) > 0):
    f1score = float(float(2) * (float(precision * recall)) / (float(precision + recall)))
    return f1score 
  else:
    return 0


def predict(newPresc, allPresc, allPivot, patients, medicine_dose):
  start = time.perf_counter()
  prescDict, similarICD10 = filterICD10(newPresc, allPresc)
  similarPrescription = getSimilarPrescriptions(newPresc, similarICD10, prescDict, patients)
  medicineList = getMedicine(similarPrescription, allPivot)
  groundTruth = getGTMedicine(allPivot)
  medsWithDosage = getMedicineDosage(medicineList, medicine_dose)
  recall = reCall(medicineList, groundTruth)
  precision = Precision(medicineList, groundTruth)
  f1score = f1Score(recall, precision)
  end = time.perf_counter()
  runtime = end - start
  return medicineList, medsWithDosage, recall, precision, f1score, runtime

def add(num1, num2):
  add = num1+num2
  return add
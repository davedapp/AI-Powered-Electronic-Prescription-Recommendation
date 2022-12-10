#LIBRARY
from numpy.core.multiarray import array
import streamlit as st
import pandas as pd
import numpy as np
import json
from internship_library import collaborative_filtering as cf

#TITLE
def show_app_page():
    st.title("Welcome to e-Recommendation Prescription!")
    st.subheader("#Patient Information")
    st.write("We need some information to give the well-suited recommendations")

show_app_page()


#USER DATA INPUT

with open("C:/Users/Dave/Internship Data/Progress 1 (Gath &Cl)/ICD-10 Drug Mapping/clean_drug_mapping.json", "r") as f:
  drugMap = json.load(f)

def getList(dict):
    return list(dict.keys())

icd10 = getList(drugMap)

patientId = st.text_input('Patient ID')
gender = st.selectbox('Select Gender', ['Male', 'Female'])
age = st.slider('Slide your Age', 1, 150)
height = st.number_input('Height (cm)', 1, 500)
weight = st.number_input('Weight (kg)', 1, 500)

st.subheader("#Differential Diagnosis")
diagnosis1 = st.selectbox('Select Differential Diagnosis 1', icd10)
diagnosis2 = st.selectbox('Select Differential Diagnosis 2', icd10)
diagnosis3 = st.selectbox('Select Differential Diagnosis 3', icd10)
diagnosis4 = st.selectbox('Select Differential Diagnosis 4', icd10)
diagnosis5 = st.selectbox('Select Differential Diagnosis 5', icd10)
#diagnosis = list([str(diagnosis1), str(diagnosis2), str(diagnosis3), str(diagnosis4), str(diagnosis5)])

def getDifferentialDiagnosis(newPresc, diagnosis1, diagnosis2, diagnosis3, diagnosis4, diagnosis5):
    tempString = "diagnosis"
    symbol = ["*&", "+&", "-&", "//&"]
    #symbolIndex = [-1,0,1,2]
    for i in range(5):
            currentCounter = i+1
            stringCounter = str(i+1)
            inputDiagnosis = locals()[tempString+stringCounter]
            currentDiagnosis = str(tempString+stringCounter)
            if inputDiagnosis == "NaN":
                newPresc['differentialDiagnosis'] = newPresc['differentialDiagnosis'].replace(currentDiagnosis, '^')
                newPresc['differentialDiagnosis'] = newPresc['differentialDiagnosis'].replace('"^"', '')
                if currentCounter > 1:
                    newPresc['differentialDiagnosis'] = newPresc['differentialDiagnosis'].replace(symbol[i-1], '')
            else:
                newPresc['differentialDiagnosis'] = newPresc['differentialDiagnosis'].replace(currentDiagnosis, inputDiagnosis)
                if currentCounter > 1:
                    newPresc['differentialDiagnosis'] = newPresc['differentialDiagnosis'].replace(symbol[i-1], ",")
    return newPresc

#classify age category
def classifyAge(age):
    age = int(age)
    if 0 <= age <=12:
        category = 'Child'
    elif 13 <= age <= 18:
        category = 'Adolescence'
    elif 19 <= age <= 59:
        category = 'Adult'
    else:
        category = 'Senior Adult'
    return category

#classify BMI category
def calculateBMI(weight, height):
  w = weight
  h = 0.01 * height
  bmi = w/(h*h)
  return round(bmi, 1)

def classifyBMI(weight, height):
    bmi = calculateBMI(weight, height)
    if bmi < 18.5:
        category = 'Underweight'
    elif 18.5 <= bmi <= 24.9:
        category = 'Normal'
    #elif 25 <= df['patientBMI'][i] <= 29.9:
    elif bmi >= 25:
        category = 'Overweight'
    return category

def classifyGender(gender):
    if gender == "Female":
        gender = "f"
    else:
        gender = "m"
    return gender

def getPatientInfo(age, weight, height, gender):
    patientAgeCategory = classifyAge(age)
    patientBMICategory = classifyBMI(weight, height)
    gender = classifyGender(gender)
    return patientAgeCategory, patientBMICategory, gender

def getNewPresc(newPresc, diagnosis1, diagnosis2, diagnosis3, diagnosis4, diagnosis5):
    newPresc = getDifferentialDiagnosis(newPresc, diagnosis1, diagnosis2, diagnosis3, diagnosis4, diagnosis5)
    return newPresc
    

#load data
medicine, medicinePresc, medicine_dose = cf.load_medicineData()
#oriPresc, oriPatients, oriPivot  = cf.load_prescPatData()
fullPresc, allPresc, patients, allPivot  = cf.load_prescPatData()

#Preprocessing
fullPresc, patients, allPivot = cf.prepro(fullPresc, patients, allPivot)

patientAgeCategory, patientBMICategory, gender = getPatientInfo(age, weight, height, gender)

#GIVE PREDICTION
ok = st.button("Give Recommendation")
if ok:
    
    newPresc = pd.Series({
    "patientId": "{}".format(patientId),
    "patientGender": "{}".format(gender),
    "age": str(age),
    "heights": str(height),
    "weight": str(weight),
    "differentialDiagnosis": '["diagnosis1"*&"diagnosis2"+&"diagnosis3"-&"diagnosis4"//&"diagnosis5"]',
    "patientAgeCategory": "{}".format(patientAgeCategory),
    "patientBMICategory":"{}".format(patientBMICategory)
    })

    #newPresc = pd.Series({"patientId":(str(patientId)), "patientGender":str(gender), "age":(str(age)), "height":(str(height)),
    #"weight": (str(weight)), "differentialDiagnosis": str(diagnosis), "patientAgeCategory":str(patientAgeCategory),
    #"patientBMICategory":str(patientBMICategory)})
    
    newPresc = getNewPresc(newPresc, diagnosis1, diagnosis2, diagnosis3, diagnosis4, diagnosis5)
    #newPresc = getDifferentialDiagnosis(newPresc, diagnosis1, diagnosis2, diagnosis3, diagnosis4, diagnosis5)


    #newPresc = {"patientId":(str(patientId)), "patientGender":str(gender), "age":(age), "height":(height),
    #"weight": (weight), "differentialDiagnosis":(diagnosis), "patientAgeCategory":str(patientAgeCategory),
    #"patientBMICategory":str(patientBMICategory)}
    
    #newPresc = str({"patientId":(str(patientId)), "patientGender":str(gender), "age":(age), "height":(height),
    #"weight": (weight), "differentialDiagnosis": diagnosis, "patientAgeCategory":str(patientAgeCategory),
    #"patientBMICategory":str(patientBMICategory)})

    #st.json(newPresc)
    st.dataframe(newPresc)
    medicineList, medsWithDosage, recall, precision, f1score, runtime = cf.predict(newPresc, allPresc, allPivot, patients, medicine_dose)
    

    st.json(f'{medicineList}')
    st.json(f'{medsWithDosage}')

    #st.write(medicineList)
    #for idx, record in newPresc.iterrows():
    #    prescDict, similarICD10 = cf.filterICD10(record, allPresc)
    #    similarPrescription = cf.getSimilarPrescriptions(record, similarICD10, prescDict, patients)
    #st.json(prescDict)
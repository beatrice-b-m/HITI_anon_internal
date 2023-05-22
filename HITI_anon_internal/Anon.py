import pandas as pd
import os
import copy
import pickle
import numpy as np
from os import listdir
from datetime import datetime
from os.path import isfile, join
import re
from tqdm import tqdm
from HITI_anon_internal.TimeShift import TShift
from HITI_anon_internal.MedEncrypter import Enigma
from HITI_anon_internal.TextAnon import TAnon
import HITI_anon_internal.ColNorm as ColNorm
"""from TimeShift import TShift
from MedEncrypter import Enigma
from TextAnon import TAnon
import ColNorm as ColNorm"""

"""Master file/id storage that has all of the projects"""

class EmoryAnon:
    """
    class that has functions in it to encrypt or timeshift given data\
    v2.0: working in the form:
    df_mag_anon['anon_EMPI']=EmoryAnon.IDanon(df_magview.report,project_name="hari_mammo",type='empi')
        type can be {EMPI, date, p_acc, r_acc_, enc, or order}
    df_mag_anon['anon_report']=EmoryAnon.Reportanon(df_magview.report)
    """

    def __init__(self, masterkey_directory, whitelist_file, columnFile=None):
        """loads or creates a master key from the working directory"""
        self.allowed_types = ['empi', 'date', 'path_acc', 'rad_acc', 'enc', 'order', 'UID_study', 'UID_series', 'csn', 'institution_name']
        self.masterkey_directory = masterkey_directory
        self.whitelist_file = whitelist_file
        self.proj_textanon = TAnon(os.path.join(self.masterkey_directory, self.whitelist_file))

        #add user defined bdc column tags
        if columnFile != None:
            self.bdc_df = pd.read_csv(columnFile)

        files = [f for f in listdir(self.masterkey_directory) if isfile(join(self.masterkey_directory, f))]
        # checking project extension (all projects have key.project_name format)
        self.master_key = {}
        for file in files:
            if file.endswith('ANONmaster'):
                if file == 'key.ANONmaster':
                    key_file = os.path.join(self.masterkey_directory, file)
                    print("Loading Master Key: " + key_file)
                    self.master_key = pickle.load(open(key_file, "rb"))
                    self.project_key = {}
                    for name in self.master_key.keys():
                        self.project_key[name] = copy.deepcopy(self.master_key[name])
                    last_mod = os.path.getmtime(key_file)
                    timestampStr = datetime.fromtimestamp(last_mod).strftime('%Y-%m-%d@%H:%M')
                    print("Backing up Master Key as: key[" + timestampStr + '].ANONmaster')
                    file_path = os.path.join(self.masterkey_directory, 'key' + timestampStr + '.ANONmaster')
                    pickle.dump(self.master_key, open(file_path, "wb"))
                    pickle.dump(self.master_key, open(file_path, "wb"))

        if self.master_key == {}:
            self.project_key = {}
            for name in self.master_key.keys():
                self.project_key[name] = copy.deepcopy(self.master_key[name])
            print('No Master Key found to Load, creating new project key')

    def load_recentMasterKey(self):
        if self.master_key != {}:
            self.project_key = {}
            for name in self.master_key.keys():
                self.project_key[name] = copy.deepcopy(self.master_key[name])
            print('Loading Keys from ' + os.path.join(self.masterkey_directory,
                                                      'key.ANONmaster'))
        else:
            self.project_key = {}
            for name in self.master_key.keys():
                self.project_key[name] = copy.deepcopy(self.master_key[name])
            print('No Master Key found to Load, creating new project key')

    def col_norm(self, df):
        return ColNorm.normalize_cols(df)

    # Explicitly adds a field to the master key.
    # @param type has to be explicitly defined in constants determines the callback function to add to enigma.
    def AddField(self, fieldName, type):
        proj_enigma = Enigma(16, type)
        keyName = fieldName + '_enigma'
        if keyName not in self.project_key:
            self.project_key[keyName] = proj_enigma
        else:
            print("Field already in master key. Please use existing field or check the name.")
        
    def IDanon(self, df_col, data_type):
        """deidentifies ID(type) in a dataframe(df) based on the existing key and returns the deidentified ID column"""
        df_col = df_col.fillna(0)
        
        if not data_type + '_enigma' in self.project_key.keys():
            print("Data type not in master key. Please add it using the AddField function.")
            return

        if self.project_key[data_type+'_enigma'].callback == None:
            raise Exception("No callback is set. If this is an existing enigma please manually set the callback function.")

        # Special case with EMPI to account for timeshift.
        if 'empi' in data_type:  # pads the empi with zeros in front to make 8 digit number - also makes the
            # timeshift mapping here
            if not 'empi_timeshift' in self.project_key.keys():
                proj_timeshift = TShift(pd.unique(df_col))
                self.project_key['empi_timeshift'] = proj_timeshift
            else:
                self.project_key['empi_timeshift'].update_timeshifts(df_col)
            anon = df_col.apply(self.project_key[data_type + '_enigma'].callback)

        else:
            anon = df_col.apply(self.project_key[data_type + '_enigma'].callback)

        return anon

    def TScol(self, df_empi_col, date_col):
        """EMPI only, is mapped at IDAnon must be encrypted before using any timeshifts"""
        try:
            shifted = self.project_key['empi_timeshift'].update_dates_df(df_empi_col, date_col)
            return shifted
        except KeyError:
            print('Did not Reference EMPI column after EMPI anonymization')

    def TextAnon(self, df_text_col):
        textanon = self.proj_textanon.anonymize_text(df_text_col)
        return textanon

    def AgeAnon(self, df_age_col):
        age_col = df_age_col.copy()
        for index, value in age_col.items():
            if value > 89:
                age_col[index] = 89
        return age_col

    def TSmapper(self, enigma, timeshift):
        """
        converts the encryption table and timeshift table into one mapping table

        - no timeshift = first two columns
        """
        original_id = []
        new_id = []
        t_shift = []
        for key, value in enigma.patient_table.items():
            original_id.append(key)
            new_id.append(value)
            t_shift.append(timeshift.lookup_timeshift[int(key)].days)

        data = {'PHI': original_id, 'PHI_ENC': new_id, 'Dates_Shifted': t_shift}
        map = pd.DataFrame(data)

        return map

    def IDmapper(self, id_cols, enigma):
        """
        converts the encryption table and timeshift table into one mapping table

        - no timeshift = first two columns
        """
        anon_ids = id_cols.to_list()
        reversed_dict = {}  # reverse the dictionary for faster lookup
        for key, value in enigma.patient_table.items():
            reversed_dict[value] = key
        original_ids = []
        for i in anon_ids:
            if i != i:  # checks for nan (nan is not equal to itself)
                original_ids.append(0)
            else:
                original_ids.append(reversed_dict[i])
        data = {'PHI': original_ids, 'PHI_ANON': anon_ids}
        map = pd.DataFrame(data)

        return map

    def save_keys(self):
        for key in self.project_key.keys():
            self.master_key[key] = self.project_key[key]
        file_path = os.path.join(self.masterkey_directory, 'key.ANONmaster')
        pickle.dump(self.master_key, open(file_path, "wb"))
        print('Saved keys to: ' + file_path)

    #will anonymize tabular based on handling criteria from DICOMTagDict
    #only set chunksize if you have a large csv file
    def anon_tabular(self, csv_path, destPath, chunk_size=10**6):

        anon_target = os.path.join(destPath, 'metadata_anon.csv')
        phi_target = os.path.join(destPath, 'metadata_phi_anon.csv')

        #remove files if they already exist
        if os.path.exists(anon_target):
            os.remove(anon_target)
        
        if os.path.exists(phi_target):
            os.remove(phi_target)

        ids = {'StudyInstanceUID' : 'UID_study', 'SeriesInstanceUID' : 'UID_series', 'PatientID' : 'empi', 'AccessionNumber' : 'rad_acc'}
        
        chunkCounter = 0
        csv_iter = pd.read_csv(csv_path, chunksize=chunk_size)
        for chunk in csv_iter:
            
            # Drops all columns with invalid patientID.
            chunk = chunk[chunk["PatientID"].apply(pd.to_numeric, errors='coerce').notna()].reset_index(drop=True)
            chunk['PatientID'] = chunk['PatientID'].astype(np.int64)
 
            print('processing chunk: ' + str(chunkCounter))
            chunkCounter+=1

            anon = chunk.copy()

            #anonymize EMPI first
            tmpAnon = self.IDanon(chunk['PatientID'], data_type='empi')
            anon['empi_anon'] = tmpAnon
            chunk['empi_anon'] = tmpAnon
            anon.drop(['PatientID'], axis=1, inplace=True)

            for col in tqdm(list(chunk.columns)):
                spl_flag = False
                mod_col = None
                if '_' in col:
                    spl_flag = True
                    spl = col.split('_')
                    mod_col = spl[-1]

                handler = None
                
                try: 
                    if spl_flag:
                        handler = self.bdc_df[self.bdc_df['Keyword'] == mod_col]['TagHandler'].iloc[0] #if sequence field
                    else: #non sequence field
                        handler = self.bdc_df[self.bdc_df['Keyword'] == col]['TagHandler'].iloc[0]
                except:
                    handler = None

                if handler == 'Remove':
                    anon.drop([col], axis=1, inplace=True)
                
                elif handler == 'SkewDate':
                    chunk[col] = pd.to_datetime(chunk[col], format="%Y%m%d", errors='coerce') #do twice to ensure same
                    dateAnon = self.TScol(chunk['PatientID'], chunk[col])
                    chunk[col+'_anon'] = dateAnon #add anonymized date to real and anonymized files
                    anon[col+'_anon'] = dateAnon
                    anon.drop([col], axis=1, inplace=True) #drop real date from anonymized df

                elif handler == 'Anonymize':

                    if col == 'PatientID':
                        continue #since it was already anonymized

                    if col == 'SOPInstanceUID':
                        anon.drop([col], axis=1, inplace=True)
                        continue
                         
                    if col in ids:
                        
                        tmpAnon = self.IDanon(anon[col], data_type=ids[col])
                        anon[col+'_anon'] = tmpAnon
                        chunk[col+'_anon'] = tmpAnon
                        anon.drop([col], axis=1, inplace=True)
                
                    else:
                        tmpAnon = self.IDanon(anon[col], data_type=col)
                        anon[col+'_anon'] = tmpAnon
                        chunk[col+'_anon'] = tmpAnon
                        anon.drop([col], axis = 1, inplace=True)
                
                elif handler == 'SkewAge':
                    continue
                #extracts age from DICOM age format
                    # pattern = "[0]*((\\d)*)"
                    # p = re.compile(pattern)
                    # anon[col+'_temp'] = anon[col].apply(lambda x: str(p.search(str(x)).group(1))) 
                    # age_anon = self.AgeAnon(anon[col+'_temp'])
                    # anon[col+'_anon'] = age_anon
                    # chunk[col + '_anon'] = age_anon
                    # anon.drop([col+'_temp', col], axis=1, inplace=True)
                
                elif handler == 'Preserve':
                    continue
                
                #drop if not present in dataset
                else:
                    anon.drop([col], axis=1, inplace=True)
            
            anon.to_csv(anon_target, index=False, mode='a')
            chunk.to_csv(phi_target, index=False, mode='a')

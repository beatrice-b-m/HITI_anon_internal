# Emory HITI Anonymization (internal use)
Dependencies:
pandas, pycryptodomex, numpy

Quick Start (after pip installing the package)

from HITI_anon_internal.Anon import EmoryAnon

Anon = EmoryAnon(masterkey_directory, whitelist_file)

Class/Functions | Usage | Example
------------ | ------------- | -------------
EmoryAnon() | Initalize the anonymization class | EAnon = EmoryAnon(masterkey_directory, whitelist_file_name)    
IDanon() | anonymizes the ID based on the ID column and ID type specified *allowed ID types: 'empi', 'date', 'path_acc', 'rad_acc', 'enc', 'order', 'UID_study', 'UID_series'*| df['EMPI_DEID] = EAnon.IDanon(df['empi'], data_type='empi')
TScol() | anonymizes the dates based on the empi column and date column *must reference EMPI column for timeshift* | df['DATE_DEID'] = EAnon.TScol(df['empi'], df['date'])
TextAnon() | redacts PHI from a text/report column specified from the most recent/updated whitelist table| df['REDACT_REPORT'] = EAnon.TextAnon(df['report_text'])
AgeAnon() | anonymizes any identifiable age above 89 to 89 given the age column | df['AGE_DEID'] = EAnon.AgeAnon(df['age'])
save_keys() | saves the keys to the masterkey | EAnon.save_keys()
TSmapper() | returns a dataframe of the original ID, anonymized ID, and applied timeshifts to that ID | EAnon.TSmapper(EAnon.project_key['empi_enigma'], EAnon.project_key['empi_timeshift'])
IDmapper() | returns a dataframe of the original ID and anonymized ID from an input ID df column | EAnon.IDmapper(df['empi'], EAnon.project_key['empi_enigma'])
load_recentMasterKey() | load the keys from the most recent masterkey (if available) | EAnon.load_recentMasterKey()
col_norm() | normalizes the dataframe column names by removing special characters and whitespaces e.g. ' Pt-EMPI' = 'Pt_EMPI' | df = EAnon.col_norm(df)
DICOMAnon() | Intialize the DICOM anonymization class | dcma = DICOMAnon(EAnon, folder_depth, destPath, ignoreDesc)
run() | Runs DICOM anonymization on one DICOM image based on t

Documentation/Version History:
- v0: Combined the Pathology_Encryption.ipynb and encrypter.ipynb notebooks
- v0.5: debugged/cleaned up some code *using a standalone version of pycryptodome (pip install -- user pycryptodomex)
- v1: working version (one mapping file, encrypting one ID, date shifting a list of columns)
- v1.1: added accession normalization to 18 characters e.g.: 00000XX130000000 to 00000XX20130000000
- v2: made implementation changes to work in the form below
- v2.1: hardcoded only specific ID types (empi, date, path_acc, rad_acc, enc, order) to be allowed, dateshift to be only +/- 31-180 days, masterfile logging, made all anonimized IDs to be the same length as the original IDs i.e. ACCESSIONS = 18 characters, ACCESSIONS_DEID = 18 digit number (starting with a non-zero digit)
- v2.2: added Thomas' textanon code. Minor changes: changed naming conventions of inputs; changed enigma IDs to be the data type; saving the enigmas to the masterkey to remove possibility of using the same encryption for different IDs.
- v2.3: skipping the ID encryption (since it's an unnecessary step) and directly selecting random number for ID
- v2.4: added master key backup during loading
- v2.5: different datetime formatting ('%Y-%m-%d %H:%M', '%Y-%m-%d', '%d-%b-%y') and error message if it's not in that format
- v2.6: empi coded to 8 digits with zero padding in front; accessions to 16 digits with zero padding in front if it was stripped; save versioning with last modified date of the masterkey
- v2.7: missing EMPI becomes 'no_ID' and '0' for empi and DEID_empi respectively
- v2.8: make missing data = '0' for deidentified IDs and date outputs and keep the columns as is
- v2.9: changed missing data handling: missing IDs become 'NaN' instead of 0
- v3.0: allow updates to whitelisting, made into package; changed empi to -00000000 to nan
- v3.1: changed function inputs so that it's just the specific columns
- v3.2: changed the initalization of EMPI timeshifts to the EMPI anonymization (i.e. timeshifts only can work with EMPI)
- v3.3: misc changes: no automatic column normalization, documentations of functions, etc.
- v3.4: updated permissions so that the group has permissions to read/write/modify the masterkey and updated datetime format to work with 'YYYYMMDD' format.
- v3.5: added AgeAnon()
- v3.6: fixed nan/NaT date handling - all nan/NaT dates will be kept as NaT
- v3.7: fixed accession encryption so that all accessions not in the normal 16-18 length format returns NaN.
- v3.8: fixed accession problem with 2020 ones and added IDmapper that returns a mapped original and anonymized ID
- v3.9: removed the automatic permissions changing for now while fixing the chmod/chown errors (errors were from using different server with different group IDs).
- v4.0: added radiology accession error handling (if accession isn't in the format we expect (length 18-16) then set as nan)
- v4.1: added pathology accession handling (a more flexible accession handling, since path accessions may have different formats than the more uniform rad acc)
- v4.2: fixed accession/empi anonymization so that it'll just give '999' instead of NaN for invalid accessions/empis 
- v4.3: added UID anonymization (UID_study and UID_series)
- v4.4: added CSN anonymization
- v4.5: added institution name anonymization
- v4.6: added DICOM anonymization
- v4.7: added automated metadata anonymization based on DICOMTagDict
- v4.8: modified accession anonymizer to output only 12 digit anonymized accessions
- v4.9: added EraseContent field in DICOMTagDict to erase the content of a tag but not remove it in DICOM anonymization
- v4.10: removed EraseContent field in DICOMTagDict and set Remove field to set that tag to an empty string
- v4.11: added datatypes class to allow anonymized values to be more flexible.
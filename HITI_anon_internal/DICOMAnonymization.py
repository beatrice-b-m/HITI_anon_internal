
from doctest import OutputChecker
import logging
from inspect import isdatadescriptor
from xml.dom import ValidationErr
import numpy as np
import re
import pandas as pd
import pydicom as dicom
import os
import PIL as pil
from shutil import copyfile
import logging
from sqlalchemy import except_all
from tqdm import tqdm


class DICOMAnon:
    '''
    Constructor for the DICOM Anonymization functionality of the Emory anon tool
    @params:
    EAnon - Emory Anonymization tool Anon object -> has current MK and BDC Dict loaded at construction
    folder_depth - how DICOMs are read and saved
    destPath - output path for the anonymized dicoms
    ignoreDesc - SeriesDescriptions that should be ignored during Anonymization (i.e deleted) 
    '''
    def __init__(self, EAnon, folder_depth, destPath, ignoreDesc):
        self.EAnon = EAnon
        self.bdc_df = EAnon.bdc_df
        self.folder_depth = folder_depth
        self.destPath = destPath
        self.ignoreDesc = ignoreDesc

    def reassign_metadata(self, dcm, tags, Anon, empi):

        patIdMask = ('0x10', '0x20')
        SOPMask = ('0x8', '0x18')
        accMask = ('0x8', '0x50')
        studyMask = ('0x20', '0xd')
        seriesMask = ('0x20', '0xe')

        #if anything in ignore description is in the series description of the DICOM skip it

        bdc_df = self.bdc_df
        ids = {patIdMask : 'empi', studyMask : 'UID_study', seriesMask : 'UID_series', accMask: 'rad_acc'}

        if type(tags) != list:
            tags = [tuple( x for x in tags)]

        i = 0
        while i < len(tags):
            
            value = dcm[tags[i]].value
            temp_i = i 
            #handle nested sequences
            if type(dcm[tags[temp_i]].value) == dicom.sequence.Sequence:
              
                for ds in range(len(dcm[tags[temp_i]].value)):
                    ret = self.reassign_metadata(dcm[tags[temp_i]].value[ds], tags[i+1], Anon, empi)
                    
                    dcm[tags[temp_i]].value[ds] = ret
                    i+=1

            else:
        
            #selects how we should handle the tag
            #if there is no handler in the DICOMTagDict we will remove the tag
                try:
                    #converts tuple to string to anonymize
                    handler = bdc_df.loc[bdc_df[bdc_df['TagMask'] == str(tags[i])].index, 'TagHandler'].values[0]
                    
                except Exception as e:
                    handler = None
                #delete the tag from the metadata Dataset object if it should be removed
                if handler == "Remove" or handler == "NotSet":
                    dcm[tags[i]].value = ''
                #anonymize using EmoryAnon
                #keep data types consistent, modify in emory anon tool 
                elif handler == "Anonymize":
                    #if tag isn't supported by the emory anon module delete it
            
                    if tags[i] == SOPMask:
                        dcm[tags[i]].value = dicom.uid.generate_uid()

                    elif tags[i] in ids:
                
                        tmp_anon = Anon.IDanon(pd.Series(value), data_type=ids[tags[i]])
                        dcm[tags[i]].value = str(tmp_anon.iloc[0])
                    
                    else:
                        del dcm[tags[i]]
                        # tmp_anon = Anon.general_anon(pd.Series(value), data_type=tag)
                        # dcm[tag].value = str(tmp_anon.iloc[0])

                elif handler == "SkewDate":
                    tmpDate = pd.to_datetime(pd.Series(value), format="%Y%m%d")
                    dateAnon = Anon.TScol(pd.Series(empi), pd.Series(tmpDate))
                    dcm[tags[i]].value = dateAnon.iloc[0]


                elif handler == "SkewAge":
                    #extracts age from DICOM age format
                    pattern = "[0]*((\\d)*)"
                    p = re.compile(pattern)
                    age = p.search(value).group(1)
                
                    age_anon = Anon.AgeAnon(pd.Series(age).astype(int))
                    dcm[tags[i]].value = str(age_anon.iloc[0])
                
                elif handler == "Preserve":
                    pass
                else:
                    del dcm[tags[i]]
                
            i+=1

        return dcm

    def save_anon_dicom(self, dcm, tuples, output_dir, Anon, folderDepth):

        savingHandler = []
        if folderDepth == 0:
            savingHandler = ["SOPInstanceUID"]
        elif folderDepth == 1:
            savingHandler = ["PatientID"]
        elif folderDepth == 2:
            savingHandler = ["PatientID", "StudyInstanceUID"]
        elif folderDepth == 3:
            savingHandler = ["PatientID", "StudyInstanceUID",  "SOPInstanceUID"]
        elif folderDepth == 4:
            savingHandler = ["PatientID", "StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID"]
        else:
            savingHandler = None
            raise ValueError("Please choose a folder depth between 0 and 4")
        
        
        # dcm.remove_private_tags() #remove all private tags
        if hasattr(dcm, 'SeriesDescription'):
            for desc in self.ignoreDesc:
                if desc in dcm.SeriesDescription.lower():
                    logging.exception('Skipping: Series decription {} in ignore list'.format(dcm.SeriesDescription))

                    return
        
        ids = {'PatientID' : 'empi', 'StudyInstanceUID' : 'UID_study', 'SeriesInstanceUID' : 'UID_series', 'AccessionNumber': 'rad_acc'}
        #if the new field contains 'UID' use the UID anonymization instead of a random string 
        #some dicom viewers might expect uid format 

        empi_tag = ('0x10', '0x20')

        if empi_tag not in dcm:
            raise AttributeError("No PatientID present in DICOM")
            return

        #cast to float so compatible with operations
        try:
            empi = float(dcm[empi_tag].value)
        except:
            return
        empi_anon = Anon.IDanon(pd.Series(empi), data_type='empi')


        dcm[empi_tag].value = str(empi_anon.iloc[0])
        tuples.remove(empi_tag)

        if hasattr(dcm, 'file_meta'):
            meta_masks = self.get_tag_masks(dcm.file_meta)
            dcm.file_meta = self.reassign_metadata(dcm.file_meta, meta_masks, Anon, empi)

        i = 0
        while i < len(tuples):
            temp_i = i 
            
            if type(dcm[tuples[temp_i]].value) == dicom.sequence.Sequence:
                
                for ds in range(len(dcm[tuples[temp_i]].value)):
                    ret = self.reassign_metadata(dcm[tuples[temp_i]].value[ds], tuples[i+1], Anon, empi)
                    
                    dcm[tuples[temp_i]].value[ds] = ret
                    i+=1

            else:
                dcm = self.reassign_metadata(dcm, tuples[i], Anon, empi)   
            i+=1
        
        #save dicoms with overwritten metadata to a new folder based on the folder strucutre
        path = output_dir
        for key in savingHandler:
            path = os.path.join(path, str(dcm[key].value))

            #break here so we don't create an extra directory
            if key == "SOPInstanceUID":
                break
            if not os.path.exists(path):
                os.mkdir(path)

        path = path = path+".dcm"
        
        dcm.save_as(path)

        #return anonymized dicom outputh path for integration with niffler metadata extraction
        return path

    def get_tag_masks(self, dcm, masks=None):
        
        if not masks:
            masks = []

        for tag in dcm:

            tmpTag = tag.tag

            if type(dcm[tmpTag].value) == dicom.sequence.Sequence:
                tmpSeq = dcm[tmpTag].value
                masks.append((hex(tmpTag.group), hex(tmpTag.elem)))
                for elem in tmpSeq:
                    subSeq = self.get_tag_masks(elem)
                    masks.append(subSeq)
            else:
                masks.append((hex(tmpTag.group), hex(tmpTag.elem)))

        return masks

    def run(self, dcm, log_path):
        LOG_FILENAME = log_path
        logging.basicConfig(filename=LOG_FILENAME, filemode='a', level=logging.DEBUG)
        masks = self.get_tag_masks(dcm)
        out_path = self.save_anon_dicom(dcm, masks, self.destPath, self.EAnon, self.folder_depth)
        return out_path

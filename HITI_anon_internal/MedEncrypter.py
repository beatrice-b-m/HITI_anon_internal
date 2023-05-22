from collections import defaultdict
from collections import defaultdict
import random
import os
import numpy as np
import string
from HITI_anon_internal.constant import DataTypes

class Enigma:
    """
    tips for some errors that might happen:
    https://stackoverflow.com/questions/52166887/typeerror-object-type-class-str-cannot-be-passed-to-c-code
    """
    # Constructor for the enigma class.
    # callback is the callback functinon used with a specified type when adding a new enigma
    def __init__(self, block_size, type):
        """
        :param block_size: 
        """
        self.block_size = block_size
        self.patient_table = defaultdict(str)
        self.encrypt_table = defaultdict(int)
        self.callback = self._assignCallback(type)
        self.enc = []
    
    # Assigns the proper callback function to the enigma class using the specified data type.
    def _assignCallback(self, type):
        # Maps callback functions to their defined types.
        callbackMapping = {
            DataTypes.ACCESSION : self._RandomizeToAccession,
            DataTypes.NUMERIC : self._RandomizeToNumeric,
            DataTypes.STRING: self._RandomizeToString,
            DataTypes.UID : self._RandomizeToUid
        }

        if type not in callbackMapping.keys():
            raise ValueError("Please use a supported datatype.")

        for name, member in DataTypes.__members__.items():
            if type == member:
                # If there is a match assign it the proper callback
                return callbackMapping[member]

        if self.callback == None:
            raise ValueError("Callback not set correctly.")

    def encrypt_patient(self, pt):
        if pt == 0:
            return 999
        pt = str(int(pt))
        l = len(pt)
        first = '0'
        if pt not in self.patient_table.keys():
            while first == '0':
                enc = int(random.randint(10**(l-1), (10**l)-1))
                first = str(enc)[0]
                if enc in self.enc:
                    first = '0'
            self.patient_table[pt] = enc
            self.enc.append(enc)
            return enc
        else:
            return self.patient_table[pt]


    def _RandomizeToNumeric(self, pt):
        if pt == 0:
            return 999
        pt = str(int(pt))
        if len(pt) < 8:
            pt = pt.rjust(8, '0')
        l = len(pt)
        first = '0'
        if pt not in self.patient_table.keys():
            while first == '0':
                enc = int(random.randint(10 ** (l - 1), (10 ** l) - 1))
                first = str(enc)[0]
                if enc in self.enc:
                    first = '0'
            self.patient_table[pt] = enc
            self.enc.append(enc)
            return enc
        else:
            return self.patient_table[pt]

    #generates a random string to be used as institution name
    def _RandomizeToString(self, value):
        if value == 0 or value == None:
            return 999
        if value not in self.patient_table.keys():
            enc = ''.join(random.choices(string.ascii_lowercase, k=10))
            while enc in self.enc:
                enc = ''.join(random.choices(string.ascii_lowercase, k=10))
            self.patient_table[value] = enc
            self.enc.append(enc)
            return enc
        else:
            return self.patient_table[value]

    def _RandomizeToUid(self, pt):
        if pt == 0:
            return 999
        if pt not in self.patient_table.keys():
            enc = self._randomizeID(pt)
            while enc in self.enc:
                enc = self._randomizeID(pt)
            self.patient_table[pt] = enc
            self.enc.append(enc)
            return enc
        else:
            return self.patient_table[pt]

    # randomly anonymizes the input id
    def _randomizeID(self, id):
        string = str(id)
        splits = string.split('.')
        newID = splits[0]
        i = 0
        for split in splits:
            if i == 0:
                i += 1
                continue
            elif len(split) == 1:
                newID = '.'.join((newID, split))
                continue
            num = int(split) + random.randint(0, 9)
            newID = '.'.join((newID, str(num)))

        return newID
    
    def _RandomizeToAccession(self, pt):
        if pt == None:
            return 999
        
        if pt not in self.patient_table.keys():
            enc = ""
            for i in range(12):
                enc+=str(random.randint(0, 9))
            while enc in self.enc:
                tmp = ""
                for i in range(12):
                    tmp+=str(random.randint(0, 9))
                enc = tmp
            self.patient_table[pt] = enc
            self.enc.append(enc)
            return enc

        else:
            return self.patient_table[pt]

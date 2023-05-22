import pandas as pd
import numpy as np
import Cryptodome
import re
import random
import datetime as datetime
import os


class TShift:
    """
    This class creates timeshift for a given patient in both structure and unstructured forms
    
    :Attributes:
        -lookup_timeshift
    """

    def __init__(self, patients, adend=None):
        """
        - min 30 day shift, max 180
        :param patients: list-like, describes the patient identification number in the data
        """
        self.shifts = [i for i in range(-180, -30)] + [j for j in range(31, 181)]
        self.lookup_timeshift = {pt: datetime.timedelta(days=random.choice(self.shifts)) for pt in patients}
        if adend is None:
            self.adend = " (ANON) "
        else:
            self.adend = adend

    def find_dates(self, text, debug=False):
        """
        - Date Formats - needed American Dates 
        This returns all regex math objects for a given date pattern
        # need to quantify the different changes in the dates
        """
        # need to classify dates
        _ = re.finditer(r"[0-9]+/[0-9]+/[0-9]{2,4}", text)
        # _ = re.finditer(r"[0-9]+/[0-9]+/[0-9]{2}",text)
        if debug:
            for x in _:
                print(x.group())
            return _
        else:
            for x in _:
                yield x

    def to_datetime(self, match):
        """
        This fu
        :param date:
        """
        # find the length of the last group and retrun the striped date and start and end of the given match objects in tuple form
        return (match.start(), match.end(), datetime.datetime.strptime(str(match.group()), "%m/%d/%y"))

    def update_dates(self, pt, text):
        """
        This function updates the date with the equivalent timeshift in the file
        :param pt:
        :param text:
        """
        if type(text) is not str:
            print(text)
            raise
        shifted = 0
        matches = [self.to_datetime(match) for match in self.find_dates(text)]
        for match in matches:
            date = match[2] + self.lookup_timeshift[pt]
            text = text[:match[0] + shifted] + date.strftime("%m/%d/%y") + self.adend + text[match[1] + shifted:]
            shifted += len(self.adend)
        return text

    def update_dates_df(self, df_ref, date_cols):
        """
        shifts the listed datetime columns and returns the changed columns
        """
        tshift = []
        for idx in df_ref.index:
            shifted = self.shift_dates(df_ref[idx], date_cols[idx])
            tshift.append(shifted)
        ts = pd.Series(tshift)
        return ts

    def try_parse_date(self, text):
        text = str(text)
        if text == 'nan' or text == 'NaT':
            return pd.NaT, None
        elif not '-' in text:
            text = str(text[:4]+'-'+text[4:6]+'-'+text[6:])
        for datetime_fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d-%b-%y'):
            try:
                return datetime.datetime.strptime(text, datetime_fmt), datetime_fmt
            except ValueError:
                pass
        raise ValueError('no valid date format found, please use the format: %Y-%m-%d %H:%M, %Y-%m-%d, %d-%b-%y \n -see https://strftime.org/ for more information')

    def update_timeshifts(self, df_ref):
        for pt in df_ref:
            if pt not in self.lookup_timeshift.keys():
                self.lookup_timeshift[pt] = datetime.timedelta(days=random.choice(self.shifts))

    def shift_dates(self, patients, date):
        """
        :arg pt - reference for date shifts
        :arg date - date to shift
        :returns shifted_date - shifted datetime as string
        """
        try:
            if np.isnan(patients):
                return pd.NaT
        except:
            raise Exception("Not an allowed type. Please use the empi column.")
        #if patients not in self.lookup_timeshift.keys():
        #    self.lookup_timeshift[patients] = datetime.timedelta(days=random.choice(self.shifts))

        date, fmt = self.try_parse_date(date)
        if fmt == None:
            return date
        shifted_date = date + self.lookup_timeshift[patients]
        shifted_date_str = shifted_date.strftime(fmt)

        return shifted_date_str

    def update_lookup(self, patients):
        if patients not in self.lookup_timeshift.keys():
            self.lookup_timeshift[patients] = datetime.timedelta(days=random.choice(self.shifts))
            return self.lookup_timeshift[patients]


"""
datetime formats:

from datetime import datetime

'STUDY_DATE'
datetime_str = '2013-09-24'
datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')

'XXX_DATETIME'
datetime_str = '2013-09-23 16:36'
datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
"""
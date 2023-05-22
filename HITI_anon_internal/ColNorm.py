"""the original col_normalizer_jjj.py
 - with comments
 - added the drop nan column function as well."""

import re
import numpy as np


def reformat_word(string):
    """ Changes the string into a format easier for python use
    i.e. change all spaces, dashes, underscores and non-alphanumeric characters into underscores and make it all
    uppercase
        :param df:
        :return:
        >>> reformat_word('abcd') 
        'ABCD'
        >>> reformat_word("a-bcd")
        'A_BCD'
        >>> reformat_word("a b cd")
        'A_B_CD'
        >>> reformat_word("ab  cd")
        'AB_CD'
        >>> reformat_word("@Ab9 nsf#9")
        'AB9_NSF_9'
    """
    words = [x for x in re.finditer(r'[A-Z|a-z|0-9]*',string) if x.start() != x.end()]
    return "_".join(x.group(0) for x in words)


def normalize_cols(df):
    """ Takes a dataframe and reformats the column headers
    :param df:
    :return:
    """
    try:
        df.drop(np.nan, axis=1, inplace=True)
        cols = list(df.columns)
        col_map = {col: reformat_word(col) for col in cols}
    except:
        cols = list(df.columns)
        col_map = {col: reformat_word(col) for col in cols}
    return df.rename(col_map, axis='columns')


def normalize_accession(accession):
    """
    Takes a dataframe and reformats the accession column
    i.e. there are two formats: one with just the year (18) and one with the whole year (2018)
    """
    if len(accession) < 18:
        return accession[:7] + '20' + accession[7:]
    else:
        return accession


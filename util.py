import json
import re
import unicodedata

import pandas as pd
import numpy as np
import seaborn as sns
from scipy import stats


def load_ids():
    """
    Load and prepare Chinese IDS data.
    """
    
    ids = pd.read_csv("ids.txt", sep="\t", header=None, comment="#",
                      names=["codepoint", "character", "decomposition"]).set_index("codepoint")
    
    # Load radical data.
    with open("unihan-json/kRSKangXi.json", "r") as rad_f:
        rad_dict = json.load(rad_f)
        rad_dict = {char: int(vals.split(".")[0]) for char, vals in rad_dict.items()}
        
    # Load pronunciation / tone / frequency data.
    with open("unihan-json/kHanyuPinlu.json", "r") as hanyu_f:
        hanyu_dict = json.load(hanyu_f)
        # Retain the max-frequency reading.
        hanyu_dict = {char: max([(freq, reading) for reading, freq in readings.items()])
                      for char, readings in hanyu_dict.items()}
        
    # Set new fields.
    ids["radical"] = ids.character.map(rad_dict)
    ids["frequency"], ids["pinyin"] = \
        zip(*ids.character.map(hanyu_dict).apply(lambda x: (None, None) if x is np.nan else x))
    ids["pinyin_toneless"], ids["tone"] = zip(*ids.pinyin.map(analyze_tone))
    
    return ids
        

tone_string_re = re.compile(r"^([^\d]*)([1-5]?)([^\d]*)$", flags=re.UNICODE)
tone_to_number = {0x304: ord('1'), 0x301: ord('2'), 0x30c: ord('3'),
                  0x300: ord('4')}
def analyze_tone(s):
    """
    Analyze tone and segmental content of a single character.
    """
    if s is None:
        return None, None
    analyzed = unicodedata.normalize("NFD", s).translate(tone_to_number)
    try:
        start, tone_num, end = tone_string_re.findall(analyzed)[0]
    except IndexError:
        print(s, analyzed)
        return 
    
    tone_num = int(tone_num) if tone_num else 5
    return start + end, tone_num
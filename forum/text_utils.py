# The following code contains some functions that can be used for preprocessing data and text cleansing
"""
Author: Vykp00
"""
import re

import unicodedata

from forum.contractions import CONTRACTION_MAP  # For removing contractions


# Removing accented characters
def remove_accented_chars(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    return text


# Expand contraction
def expand_contractions(text, contraction_mapping=CONTRACTION_MAP):
    contractions_pattern = re.compile('({})'.format('|'.join(contraction_mapping.keys())),
                                      flags=re.IGNORECASE | re.DOTALL)

    def expand_match(contraction):
        match = contraction.group(0)
        first_char = match[0]
        expanded_contraction = contraction_mapping.get(match) \
            if contraction_mapping.get(match) \
            else contraction_mapping.get(match.lower())
        expanded_contraction = first_char + expanded_contraction[1:]
        return expanded_contraction

    expanded_text = contractions_pattern.sub(expand_match, text)
    expanded_text = re.sub("'", "", expanded_text)
    return expanded_text


# Remove special character
def remove_special_characters(text, remove_digits=False):
    pattern = r'[^a-zA-z0-9\s]' if not remove_digits else r'[^a-zA-z\s]'
    text = re.sub(pattern, '', text)
    return text


# This combine all functions to one process
def normalize_corpus(corpus, contraction_expansion=True,
                     accented_char_removal=True, text_lower_case=True,
                     special_char_removal=True, remove_digits=False):
    # normalize corpus
    if accented_char_removal:
        corpus = remove_accented_chars(corpus)
    # expand contractions
    if contraction_expansion:
        corpus = expand_contractions(corpus)
    # lowercase the text
    if text_lower_case:
        corpus = corpus.lower()
    # remove extra newlines
    corpus = re.sub(r'[\r|\n|\r\n]+', ' ', corpus)
    # remove special characters and\or digits
    if special_char_removal:
        # insert spaces between special characters to isolate them
        special_char_pattern = re.compile(r'([{.(-)!}])')
        corpus = special_char_pattern.sub(" \\1 ", corpus)
        corpus = remove_special_characters(corpus, remove_digits=remove_digits)
        # remove extra whitespace
    cleaned_corpus = re.sub(' +', ' ', corpus)

    return cleaned_corpus

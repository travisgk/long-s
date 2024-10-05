"""
Filename: _german_conversion.py
Description: This contains the complex function that inserts the long S
             into the German language.

Author: TravisGK
Version: 1.0

License: MIT License
"""

import itertools
import re
from ._simple_conversions import strip_consonant_accents, transfer_long_S
from ._german_lists import *

UNKNOWN_S = "φ"


def _crossword_replace(text: str, spelling_pattern: str):
    """
    This function fills in ambiguous cases of the letter S
    by using a given spelling pattern.

    The spelling pattern is actually the replacement term,
    while the search terms are generated by taking
    the spelling pattern and creating every possible spelling combination
    where any letter "s" or "ſ" will be swapped with an UNKNOWN S;
    all of these search terms will always have at least one UNKNOWN S.

    The way this function works is analogous to filling in a crossword:
    the program recognizes where patterns can "fit" into the blanks.

    Parameters:
    text (string): the text to be searched and possibly modified.
    spelling_pattern (string): the replacement term.

    Returns:
    string: text with replacements applied (if any).
    bool: whether a replacement was made.
    """
    if len(spelling_pattern) > len(text):
        return text, False

    # uses itertools.product to generate all combinations
    # of the search term with any letter S swapped out with
    # an UNKNOWN_S.
    options = [(c if c not in "ſs" else [c, UNKNOWN_S]) for c in spelling_pattern]
    combos = itertools.product(*options)
    possible_terms = ["".join(combo) for combo in combos if UNKNOWN_S in combo]

    old_text = text
    for possible_term in possible_terms:
        text = text.replace(possible_term, spelling_pattern)

    return text, (text != old_text)


def _blueprint_replace(text: str, blueprint_text: str, spelling_pattern: str):
    """
    Returns text with a spelling pattern enforced and if any replacements were made.

    """
    pattern_without_long_s = spelling_pattern.replace("ſ", "s")
    matched_indices = [
        m.start()
        for m in re.finditer(re.escape(pattern_without_long_s), blueprint_text)
    ]

    for index in matched_indices:
        end_index = index + len(spelling_pattern)
        text = text[:index] + spelling_pattern + text[end_index:]

    return text, len(matched_indices) > 0


def _fill_in_double_s(word: str):
    """Returns the word with a basic pattern with double S filled in."""
    word = word.replace(f"{UNKNOWN_S}s", "ſs")
    word = word.replace(f"s{UNKNOWN_S}", "sſ")
    return word


def _find_blank_indices(word):
    """Returns a list of indices where any UNKNOWN_S remains in the word."""
    return [i for i, c in enumerate(word) if c == UNKNOWN_S]


def convert_german_word(word: str):
    """Returns German text with the long S (ſ) placed appropriately."""

    DEFAULT_UNKNOWNS_TO_LONG_S = True  # True by default.
    FORCE_SHORT_S_BEFORE_Z = False  # False after 1901.
    PRINT_DEBUG_TEXT = False

    backup_word = word

    # 0) The program has the conversions of some commonly-used
    #    words explicitly written in memory, so if the word is one of those,
    #    the function will return that conversion immediately.
    if PRINT_DEBUG_TEXT:
        print(f"Begins) {word}")
        print(f"Step 0)")

    clean_word = strip_consonant_accents(word.lower())

    # matches list are indexed by the starting letter.
    exact_matches_list = EXACT_MATCHES.get(clean_word[0])
    if exact_matches_list is not None:
        for term in exact_matches_list:
            no_long_s = term.replace("ſ", "s")
            if clean_word == no_long_s:
                word = transfer_long_S(term, word)
                if PRINT_DEBUG_TEXT:
                    print(f"\t{word}")
                return word

    blueprint_word = clean_word  # used for indexing and forced replacements.
    clean_word = clean_word[:-1].replace("s", UNKNOWN_S) + clean_word[-1]

    # S as the first letter in a word is always long.
    if clean_word.startswith(UNKNOWN_S):
        clean_word = "ſ" + clean_word[1:]

    # the penultimate S is almost always long.
    if clean_word[-2] == UNKNOWN_S:
        if clean_word[-1] != "k":
            clean_word = clean_word[:-2] + "ſ" + clean_word[-1:]
        else:
            clean_word = clean_word[:-2] + "s" + clean_word[-1:]

    clean_word = _fill_in_double_s(clean_word)
    remaining_blank_indices = _find_blank_indices(clean_word)
    if UNKNOWN_S not in (clean_word[i] for i in remaining_blank_indices):
        # the word has been fully solved, so it's returned.
        word = transfer_long_S(clean_word, word)
        return word

    # 1) This step applies basic patterns to try to solve any ambiguous S.
    # ---
    # determines which occurrences of S can't be explicitly decided as
    # being a short S (and thereby which ones must definitely be a short S).
    if FORCE_SHORT_S_BEFORE_Z:
        pattern = f"{UNKNOWN_S}(?=[aäceioöpſ{UNKNOWN_S}tuüy])"  # removed K for DEBUG
    else:
        pattern = f"{UNKNOWN_S}(?=[aäceioöpſ{UNKNOWN_S}tuüyz])"  # removed K for DEBUG
    uncertain_indices = [m.start() for m in re.finditer(pattern, clean_word)]

    # fills in any determined short S from the pattern.
    certain_short_s_indices = [
        i
        for i, c in enumerate(clean_word)
        if c == UNKNOWN_S and i not in uncertain_indices
    ]
    for index in certain_short_s_indices:
        clean_word = clean_word[:index] + "s" + clean_word[index + 1 :]
    clean_word = _fill_in_double_s(clean_word)

    if PRINT_DEBUG_TEXT:
        print(f"Step 1)\t{clean_word}")

    # 2) This step uses the blueprint replace function to try to solve
    #    any ambiguous S, but only for patterns
    #    that occur at the end of words.
    if PRINT_DEBUG_TEXT:
        print(f"Step 2)")

    ends_list = None
    if len(blueprint_word) >= 3:
        index = blueprint_word[-3:]
        ends_list = END_PATTERNS.get(index)
    if ends_list is None and len(blueprint_word) >= 2:
        index = blueprint_word[-2:]
        ends_list = END_PATTERNS.get(index)
    if ends_list is None and len(blueprint_word) >= 1:
        index = blueprint_word[-1]
        ends_list = END_PATTERNS.get(index)

    if ends_list is not None:
        for term in ends_list:
            if len(term) <= len(clean_word):
                clean_snippet = clean_word[-len(term) :]
                blueprint_snippet = blueprint_word[-len(term) :]

                clean_snippet, made_replacement = _blueprint_replace(
                    clean_snippet, blueprint_snippet, term
                )
                if made_replacement:
                    if PRINT_DEBUG_TEXT:
                        print(f"\tEND PATTERN: {term}")
                    clean_word = clean_word[: -len(term)] + clean_snippet
                    clean_word = _fill_in_double_s(clean_word)
                    break

    if PRINT_DEBUG_TEXT:
        print(f"\t{clean_word}")

    # 3) This step uses the crossword replace function to try to solve
    #    any ambiguous S. A dictionary of spelling patterns that can occur
    #    anywhere in the word are used to try to further solve the spelling.
    if PRINT_DEBUG_TEXT:
        print(f"Step 3)")

    remaining_blank_indices = _find_blank_indices(clean_word)
    for term in OMNIPRESENT_PATTERNS:
        if UNKNOWN_S not in (clean_word[i] for i in remaining_blank_indices):
            break  # no more unknowns remain.

        clean_word, made_replacement = _crossword_replace(clean_word, term)
        if made_replacement:
            if PRINT_DEBUG_TEXT:
                print(f"\tOMNIPRESENT PATTERN: {term}")
            clean_word = _fill_in_double_s(clean_word)
            remaining_blank_indices = _find_blank_indices(clean_word)

    if PRINT_DEBUG_TEXT:
        print(f"\t{clean_word}")

    # 4) This step uses the crossword replace function to try to solve
    #    any ambiguous S, but only for patterns
    #    that occur at the beginning of words.
    if PRINT_DEBUG_TEXT:
        print(f"Step 4)")

    starts_list = START_PATTERNS.get(blueprint_word[0])
    if starts_list is not None and UNKNOWN_S in (
        clean_word[i] for i in remaining_blank_indices
    ):
        for term in starts_list:
            if len(term) <= len(clean_word):
                clean_snippet = clean_word[: len(term)]
                clean_snippet, made_replacement = _crossword_replace(
                    clean_snippet, term
                )
                if made_replacement:
                    if PRINT_DEBUG_TEXT:
                        print(f"\tSTART PATTERN: {term}")
                    clean_word = clean_snippet + clean_word[len(term) :]
                    clean_word = _fill_in_double_s(clean_word)
                    break

    if PRINT_DEBUG_TEXT:
        print(f"\t{clean_word}")

    # 5) This step runs postprocess replacements with the crossword search.
    for term in POSTPROCESS_PATTERNS:
        if UNKNOWN_S not in (clean_word[i] for i in remaining_blank_indices):
            break  # no more unknowns.

        clean_word, made_replacement = _crossword_replace(clean_word, term)
        if made_replacement:
            clean_word = _fill_in_double_s(clean_word)

    if PRINT_DEBUG_TEXT:
        print(f"Step 5) {clean_word}")

    # 6) This step enforces a few exceptional spellings.
    for term in FORCED_OVERWRITES:
        if len(term) <= len(clean_word):
            clean_word, made_replacement = _blueprint_replace(
                clean_word, blueprint_word, term
            )
            if made_replacement:
                clean_word = _fill_in_double_s(clean_word)
                # can't break here b/c search is omnipresent.

    if PRINT_DEBUG_TEXT:
        print(f"Step 6) {clean_word}")

    # Result) The word is cleaned up and returned.
    if DEFAULT_UNKNOWNS_TO_LONG_S:
        clean_word = clean_word.replace(UNKNOWN_S, "ſ")
    word = transfer_long_S(clean_word, word)

    if PRINT_DEBUG_TEXT:
        print(f"Result) {word}")

    return word

import pprint
import difflib
import json
import sys
__author__ = 'aderi'

import os.path
sys.path.append('/nfs/guest2/aderi/unidecode/lib/python3.4/site-packages/')

from unidecode import unidecode
PATH = '../iso_codes/'

if not os.path.exists(PATH):
    PATH = '../../iso_codes/'

if not os.path.exists(PATH):
    PATH = '../../iso_codes/'

if not os.path.exists(PATH):
    PATH = '../../../gazetteer/iso_codes/'

if not os.path.exists(PATH):
    PATH = 'iso_codes/'

code_to_lang_filename = PATH + 'code_to_lang.json'
lang_to_code_filename = PATH + 'lang_to_code.json'
iso1_to_iso3_filename = PATH + 'iso1_to_iso3.json'
iso3_to_iso1_filename = PATH + 'iso3_to_iso1.json'
code_to_lang_table_filename = PATH + 'code_to_lang.table'
macro_to_indiv_filename = PATH + 'macro_to_indiv.json'


def generate_json_dumps():
    code_to_lang = dict()
    lang_to_code = dict()
    with open('LanguageCodes.tab', 'r') as language_codes_file:
        for line in language_codes_file:
            info = line.rstrip().split('\t')
            code, country_id, lang_status, lang = info

            code_to_lang[code] = lang
            lang_to_code[lang] = code

    with open('iso_1_to_iso_3', 'r') as language_codes_file:
        for line in language_codes_file:
            info = line.rstrip().split('\t')

            iso_1, iso_2, iso_3, language, scope, info_type, temp = info

            code_to_lang[iso_3] = language
            lang_to_code[language] = iso_3

    with open('iso-639-3_Code_Tables_20150505/iso-639-3_Name_Index_20150505.tab', 'r') as language_codes_file:
        language_codes_file.readline()
        for line in language_codes_file:
            info = line.rstrip('\n').split('\t')

            iso_3, lang_1, lang_2 = info
            code_to_lang[iso_3] = lang_1
            lang_to_code[lang_2] = iso_3
            lang_to_code[lang_1] = iso_3

    with open('/auto/nlg-05/deri/gazetteer/iso_codes/collected-lang-to-iso.table', 'r') as language_codes_file:
        for line in language_codes_file:
            info = line.rstrip('\n').split('\t')

            lang, temp, iso_3 = info
            if len(iso_3) != 3:
                print(lang, iso_3)
            # assert len(iso_3) == 3
            if iso_3 not in code_to_lang:
                code_to_lang[iso_3] = lang
            lang_to_code[lang] = iso_3

    with open(code_to_lang_filename, 'w') as code_to_lang_file:
        json.dump(code_to_lang, code_to_lang_file)
    with open(lang_to_code_filename, 'w') as lang_to_code_file:
        json.dump(lang_to_code, lang_to_code_file)

    iso1_to_iso3 = dict()
    iso3_to_iso1 = dict()
    with open('iso_1_to_iso_3', 'r') as language_codes_file:
        for line in language_codes_file:
            info = line.rstrip('\n').split('\t')

            iso_1, iso_2, iso_3, language, scope, info_type, temp = info

            iso1_to_iso3[iso_1] = iso_3
            iso3_to_iso1[iso_3] = iso_1

    with open(iso1_to_iso3_filename, 'w') as iso1_to_iso3_file:
        json.dump(iso1_to_iso3, iso1_to_iso3_file)
    with open(iso3_to_iso1_filename, 'w') as iso3_to_iso1_file:
        json.dump(iso3_to_iso1, iso3_to_iso1_file)

    macro_to_indiv = dict()
    with open('iso-639-3_Code_Tables_20150505/iso-639-3-macrolanguages_20150112.tab', 'r') as macrolanguage_file:
        macrolanguage_file.readline()
        for line in macrolanguage_file:
            info = line.rstrip('\n').split('\t')
            macrolang, indiv_lang, temp = info
            if macrolang in macro_to_indiv:
                macro_to_indiv[macrolang].append(indiv_lang)
            else:
                macro_to_indiv[macrolang] = [indiv_lang]
    with open(macro_to_indiv_filename, 'w') as macro_to_indiv_file:
        json.dump(macro_to_indiv, macro_to_indiv_file)

    with open(code_to_lang_table_filename, 'w') as code_to_lang_table_file:
        code_lang_tuple_list = sorted([(code, lang) for lang, code in lang_to_code.items()])
        for code_lang_tuple in code_lang_tuple_list:
            code_to_lang_table_file.write('{0}\t{1}\n'.format(code_lang_tuple[0], code_lang_tuple[1]))


def get_macro_to_indiv():
    with open(macro_to_indiv_filename, 'r') as macro_to_indiv_file:
        macro_to_indiv = json.load(macro_to_indiv_file)
    return macro_to_indiv


def get_code_to_lang():
    with open(code_to_lang_filename, 'r') as code_to_lang_file:
        code_to_lang = json.load(code_to_lang_file)
    return code_to_lang


def get_lang_to_code():
    with open(lang_to_code_filename, 'r') as lang_to_code_file:
        lang_to_code = json.load(lang_to_code_file)
    return lang_to_code


def get_iso3_to_iso1():
    with open(iso3_to_iso1_filename, 'r') as infile:
        iso3_to_iso1 = json.load(infile)
    return iso3_to_iso1


def get_iso1_to_iso3():
    with open(iso1_to_iso3_filename, 'r') as infile:
        iso1_to_iso3 = json.load(infile)
    return iso1_to_iso3


def find_isocode_for_wikicode(wikicode):  # TODO: do language matching across individual tokens (e.g., Egyptian Arabic)

    lang_to_code = get_lang_to_code()

    iso3_to_iso1 = get_iso3_to_iso1()
    iso1_to_iso3 = get_iso1_to_iso3()
    if wikicode in iso3_to_iso1:
        return wikicode
    elif wikicode in iso1_to_iso3:
        return iso1_to_iso3[wikicode]
    else:
        return wikicode


def find_wikicode_for_isocode(isocode):
    lang_to_code = get_lang_to_code()
    iso3_to_iso1 = get_iso3_to_iso1()
    iso1_to_iso3 = get_iso1_to_iso3()

    if isocode in iso3_to_iso1:
        return iso3_to_iso1[isocode]
    else:
        return isocode


def find_lang_for_code(code):
    code_to_lang = get_code_to_lang()

    if code in code_to_lang:
        return code_to_lang[code]
    else:
        return None


def find_code_for_languages(languages,
                            website_str_return=False, set_of_known_codes = None):  # TODO: do language matching across individual tokens (e.g., Egyptian Arabic)

    lang_to_code = get_lang_to_code()

    if set_of_known_codes is not None:
        lang_to_code = {lang: code for lang, code in lang_to_code.items() if code in set_of_known_codes}
    website_str = ""
    website_str_2 = ""

    lowercase_lang_to_truecase = {key.lower(): key for key in lang_to_code}
    lang_to_code = {key.lower(): val for key, val in lang_to_code.items()}

    will_return_str = False
    if type(languages) is str:
        will_return_str = True
        languages = [languages]

    if will_return_str:
        return_codes = ''
    else:
        return_codes = dict()

    for language in languages:
        # lang_list = language.split()
        # lang_list = [ x.lower().capitalize() for x in lang_list]
        # if not language[0].isupper():
        #     language = ' '.join([ x.lower().capitalize() for x in language.split()])
        try_code = lang_to_code.get(language.lower())
        if try_code is not None:
            if will_return_str:
                return_codes = try_code
                website_str = 'Using code {0} for {1}.'.format(try_code, language)
            else:
                return_codes[language] = try_code

        else:

            try:
                try_language = difflib.get_close_matches(language, lang_to_code.keys(), 1)[0]
            except IndexError:
                print("Couldn't find code for language {0}".format(language))
                website_str = 'Couldn\'t find any code for {0}!'.format(language)

                if website_str_return:
                    return None, website_str, website_str_2
                return None

            if website_str_return:
                try_code = lang_to_code[try_language]
            else:
                try_code = lang_to_code[try_language] + '#' + try_language
            if will_return_str:
                return_codes = try_code
            else:
                return_codes[language] = try_code

            print("with a fuzzy match, found code {0} for language {1}".format(try_code, language))
            website_str = 'Using a fuzzy match, using code {0} ({1}) for {2}'.format(try_code.split('#')[0],
                                                                                              lowercase_lang_to_truecase[
                                                                                                  try_language],
                                                                                              language)

    if not website_str_return:
        return return_codes
    else:

        possible_language_keywords = set([word.lower() for word in languages[0].split(' ') if word.lower() in lang_to_code])
        possible_code_language_tuples = []
        for lang, code in lang_to_code.items():
            if not set(lang.split(' ')).isdisjoint(possible_language_keywords) and code != return_codes and \
                    (set_of_known_codes is None or code in set_of_known_codes):
                possible_code_language_tuples.append('{0} ({1})'.format(unidecode(lowercase_lang_to_truecase[lang]), code))

        if len(possible_code_language_tuples) > 0:
            website_str_2 = 'Also consider: {0}.'.format(', '.join(possible_code_language_tuples))

        # print(website_str)
        return return_codes, website_str, website_str_2


def is_code(code):
    code_to_lang = get_code_to_lang()
    return code.lower() in code_to_lang


# def get_language_for_code(code):
# """deprecate????"""
#     code_to_lang = get_code_to_lang()
#     assert code in code_to_lang, '{0} not a valid code'.format(code)
#     return code_to_lang[code]


if __name__ == '__main__':
    generate_json_dumps()
    print(find_code_for_languages('Moldovan'))
    print(get_macro_to_indiv()['ara'])
    print(find_lang_for_code('be-x-old'))
    print(find_code_for_languages('Eastern Bengali', True))
    print(find_code_for_languages('Arabic', True))




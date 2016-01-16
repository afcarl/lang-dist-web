import copy
import csv
import glob
import pprint
import math
from subprocess import check_output

__author__ = 'aderi'
import sys

sys.path.append('/auto/nlg-05/deri/gazetteer')
sys.path.append('/')
try:
    from unicode.unicode_stats import ScriptsInfo, fancy_print, get_script_as_features, get_script_to_pared_chars, \
        get_pared_down_chars_as_features, get_lang_to_pared_char_set, get_lang_to_pared_char_set_short, \
        get_lang_script_info
except ImportError:
    pass

import iso_codes.parse_language_codes
from collections import defaultdict

try:
    import numpy as np
    import scipy.spatial.distance
    from ipa.phoneme_features import get_lang_phoneme_set
except ImportError:
    pass

DIST_ATTR_LIST = sorted(
    ['u_composite', 'u_genetic', 'u_geo', 'u_p', 'u_s', 'avg', 'u_avg', 'transliterable', 'phonetic'])
FEAT_ATTR_LIST = sorted(['same_alph', 'named_entity_count', 'wiki', 'europarl'])
DISTS_FILE = 'lang.dists'

SCRIPT_DIST_ATTR_LIST = sorted(['avg', 'transliterable'])
SCRIPT_FEAT_ATTR_LIST = sorted(['named_entity_count'])
SCRIPT_DISTS_FILE = 'script.dists'


def get_dist_attr_list():
    return DIST_ATTR_LIST


def get_feat_attr_list():
    return FEAT_ATTR_LIST


class ScoreStruct(object):
    def __init__(self):
        self.dist_dict = {attr: None for attr in DIST_ATTR_LIST}
        self.feat_dict = {feat: None for feat in FEAT_ATTR_LIST}

    def set_dist(self, attr_string, val):
        assert attr_string in self.dist_dict
        self.dist_dict[attr_string] = float(val)

    def set_feat(self, attr_string, val):
        assert attr_string in self.feat_dict
        self.feat_dict[attr_string] = str(val)

    def get_dist_vals(self):
        vals = [self.dist_dict[key] for key in sorted(self.dist_dict.keys())]
        return vals

    def get_dist_avg(self, ignore_attr=None):
        if ignore_attr is None:
            attr_vals = [x for x in self.get_dist_vals() if x is not None]
            return sum(attr_vals) / len(attr_vals)
        else:
            attr_vals = [dist for key, dist in self.dist_dict.items() if dist is not None and key != ignore_attr]
            return sum(attr_vals) / len(attr_vals)

    def get_feat_vals(self):
        vals = [self.feat_dict[key] for key in sorted(self.feat_dict.keys())]
        return vals

    def __str__(self):
        return_str = ''
        for attr in sorted(self.dist_dict.keys()):
            return_str += '{0}:{1}\t'.format(attr, self.dist_dict[attr])
        for feat in sorted(self.feat_dict.keys()):
            return_str += '{0}:{1}\t'.format(feat, self.feat_dict[feat])
        return return_str


class ScriptScoreStruct(object):
    def __init__(self):
        self.dist_dict = {attr: None for attr in SCRIPT_DIST_ATTR_LIST}
        self.feat_dict = {feat: None for feat in SCRIPT_FEAT_ATTR_LIST}

    def set_dist(self, attr_string, val):
        assert attr_string in self.dist_dict
        self.dist_dict[attr_string] = float(val)

    def set_feat(self, attr_string, val):
        assert attr_string in self.feat_dict
        self.feat_dict[attr_string] = str(val)

    def get_dist_vals(self):
        vals = [self.dist_dict[key] for key in sorted(self.dist_dict.keys())]
        return vals

    def get_dist_avg(self, ignore_attr=None):
        if ignore_attr is None:
            attr_vals = [x for x in self.get_dist_vals() if x is not None]
            return sum(attr_vals) / len(attr_vals)
        else:
            attr_vals = [dist for key, dist in self.dist_dict.items() if dist is not None and key != ignore_attr]
            return sum(attr_vals) / len(attr_vals)


    def get_feat_vals(self):
        vals = [self.feat_dict[key] for key in sorted(self.feat_dict.keys())]
        return vals

    def __str__(self):
        return_str = ''
        for attr in sorted(self.dist_dict.keys()):
            return_str += '{0}:{1}\t'.format(attr, self.dist_dict[attr])
        for feat in sorted(self.feat_dict.keys()):
            return_str += '{0}:{1}\t'.format(feat, self.feat_dict[feat])
        return return_str


URIEL_DIR = '/auto/nlg-05/deri/gazetteer/lang_lang_dist/v0'


def make_pretty_float(f):
    if f is None:
        return 'None'
    if f == 1.0 or f == 0.0:
        return str(f)
    return "%0.6f" % f


def remove_None(s):
    if s is None:
        return 'None'
    return s


def print_dict(in_list=None, out_list=None):
    for code in sorted(code_to_code_to_scorestruct.keys()):
        print(code)
        for code2 in sorted(code_to_code_to_scorestruct[code].keys()):
            # print(code2)
            # print(code_to_code_to_scorestruct[code][code2])
            print('\t{0}\t{1}'.format(code2, str(code_to_code_to_scorestruct[code][code2])))


def print_dict_to_file(dists_file, in_list=None, out_list=None):
    with open('/auto/nlg-05/deri/gazetteer/lang_lang_dist/%s' % dists_file, 'w') as lang_dist_file:
        lang_dist_file.write('{0}\t{1}\t{2}\t{3}\n'.format('code1', 'code2',
                                                           '\t'.join(DIST_ATTR_LIST), '\t'.join(FEAT_ATTR_LIST)))
        for code in sorted(code_to_code_to_scorestruct.keys()):
            if in_list is not None and code not in in_list:
                continue
            for code2 in sorted(code_to_code_to_scorestruct[code].keys()):
                # print(code2)
                if out_list is not None and code2 not in out_list:
                    continue
                dist_string = '\t'.join(
                    map(make_pretty_float, code_to_code_to_scorestruct[code][code2].get_dist_vals()))
                feat_string = '\t'.join(map(remove_None, code_to_code_to_scorestruct[code][code2].get_feat_vals()))
                lang_dist_file.write('{0}\t{1}\t{2}\t{3}\n'.format(code, code2, dist_string, feat_string))


def script_print_dict_to_file(dists_file, in_list=None, out_list=None):
    with open('/auto/nlg-05/deri/gazetteer/lang_lang_dist/%s' % dists_file, 'w') as lang_dist_file:
        lang_dist_file.write('{0}\t{1}\t{2}\t{3}\n'.format('script1', 'script2',
                                                           '\t'.join(SCRIPT_DIST_ATTR_LIST),
                                                           '\t'.join(SCRIPT_FEAT_ATTR_LIST)))
        for code in sorted(script_to_script_to_scorestruct.keys()):
            if in_list is not None and code not in in_list:
                continue
            for code2 in sorted(script_to_script_to_scorestruct[code].keys()):
                # print(code2)
                if out_list is not None and code2 not in out_list:
                    continue
                dist_string = '\t'.join(
                    map(make_pretty_float, script_to_script_to_scorestruct[code][code2].get_dist_vals()))
                feat_string = '\t'.join(map(remove_None, script_to_script_to_scorestruct[code][code2].get_feat_vals()))
                lang_dist_file.write('{0}\t{1}\t{2}\t{3}\n'.format(code, code2, dist_string, feat_string))


def avg_dict(feat_name='avg', ignore_attr=None):
    for code1 in code_to_code_to_scorestruct:
        for code2 in code_to_code_to_scorestruct[code1]:
            score_struct = code_to_code_to_scorestruct[code1][code2]
            score_struct.set_dist(feat_name, score_struct.get_dist_avg(ignore_attr))


def avg_dict_script(feat_name='avg'):
    for code1 in script_to_script_to_scorestruct:
        for code2 in script_to_script_to_scorestruct[code1]:
            score_struct = script_to_script_to_scorestruct[code1][code2]
            score_struct.set_dist(feat_name, score_struct.get_dist_avg())


def load_uriel(iso_set=None):
    listing = glob.glob('{0}/*distance.csv'.format(URIEL_DIR))

    for filename in sorted(listing):
        print(filename)
        dist_feature_name = 'u_' + filename.replace('{0}/'.format(URIEL_DIR), '').replace('_distance.csv', '')
        print(dist_feature_name)
        index_to_code = dict()
        with open(filename, 'r') as csv_file:
            uriel_csv = csv.reader(csv_file, delimiter=',')
            for i, row in enumerate(uriel_csv):

                if i == 0:
                    index_to_code = {index: code for index, code in enumerate(row[1:])}
                    continue
                if iso_set is not None and row[0] not in iso_set:
                    continue

                for index, val in enumerate(row[1:]):
                    # print(code_to_code_to_scorestruct[row[0]][index_to_code[index]])
                    if iso_set is not None and index_to_code[index] not in iso_set:
                        continue
                    code_to_code_to_scorestruct[row[0]][index_to_code[index]].set_dist(dist_feature_name, val)

                    # if i > 5:
                    # break
                    # break
    avg_dict('u_avg')
    # print_dict()


def get_omniglot_iso_code_to_scripts_info():
    global all_scripts, omniglot_scripts_file, line, x, primary, secondary
    omniglot_iso_code_to_scripts_info = defaultdict(ScriptsInfo)
    all_scripts = set()
    with open('/auto/nlg-05/deri/gazetteer/unicode/omniglot.scripts') as omniglot_scripts_file:
        for line in omniglot_scripts_file:
            line = line.rstrip().split('\t')
            primary = set(x for x in line[1].split(' ') if x != '')
            secondary = set(x for x in line[2].split(' ') if x != '')
            omniglot_iso_code_to_scripts_info[line[0]] = ScriptsInfo(primary, secondary)
            all_scripts = all_scripts.union(primary)
            all_scripts = all_scripts.union(secondary)
    return omniglot_iso_code_to_scripts_info


def get_omniglot_scripts():
    global all_scripts, omniglot_scripts_file, line, x, primary, secondary, \
        omniglot_iso_code_to_script_features, iso_code_0, scripts_feat_0, iso_code_1, scripts_feat_1, \
        scripts_0, scripts_1
    omniglot_iso_code_to_scripts_info = get_omniglot_iso_code_to_scripts_info()
    omniglot_iso_code_to_script_features = get_script_as_features(omniglot_iso_code_to_scripts_info, all_scripts)
    for iso_code_0, scripts_feat_0 in sorted(omniglot_iso_code_to_script_features.items()):
        if iso_code_0 not in code_to_code_to_scorestruct:
            continue

        for iso_code_1, scripts_feat_1 in sorted(omniglot_iso_code_to_script_features.items()):
            # print(scripts_info_0)
            # print(scripts_info_1)

            if iso_code_1 not in code_to_code_to_scorestruct:
                continue
            cos_dist = scipy.spatial.distance.cosine(scripts_feat_0, scripts_feat_1)
            if 'e' in str(cos_dist):
                cos_dist = 0.0
            code_to_code_to_scorestruct[iso_code_0][iso_code_1].set_dist('scripts', cos_dist)

            scripts_0 = omniglot_iso_code_to_scripts_info[iso_code_0].get_all_scripts()
            scripts_1 = omniglot_iso_code_to_scripts_info[iso_code_1].get_all_scripts()

            if scripts_0.isdisjoint(scripts_1):
                code_to_code_to_scorestruct[iso_code_0][iso_code_1].set_feat('same_alph', '-')
            else:
                code_to_code_to_scorestruct[iso_code_0][iso_code_1].set_feat('same_alph', '+')


def get_europarl_iso_codes():
    europarl_codes = 'bg cs da de el en es et fi fr hu it et et fi fr hu it lt lv nl pl pt ro sk sl sv'.split(' ')

    europarl_codes = [iso_codes.parse_language_codes.find_isocode_for_wikicode(x) for x in europarl_codes]

    return europarl_codes


def get_code_to_ne_counts():
    code_to_ne_counts = defaultdict(int)
    with open('/home/nlg-05/deri/gazetteer/lang_lang_dist/counts.uniq', 'r') as counts_file:
        for line in counts_file:
            count, iso_code = line.rstrip().split()
            count = int(count)
            code_to_ne_counts[iso_code] = count
    return code_to_ne_counts


def get_named_entity_counts(code_to_code_to_scorestruct):
    code_to_ne_counts = get_code_to_ne_counts()

    for code1 in code_to_code_to_scorestruct:
        for code2 in code_to_code_to_scorestruct[code1]:
            count = 0
            if code2 in code_to_ne_counts:
                count = code_to_ne_counts[code2]
            code_to_code_to_scorestruct[code1][code2].set_feat('named_entity_count', str(count))

            # for iso_code, count in code_to_ne_counts.items():
            # if iso_code in code_to_code_to_scorestruct:
            # print(count, iso_code)
            # for code1 in code_to_code_to_scorestruct:
            #             code_to_code_to_scorestruct[code1][iso_code].set_feat('named_entity_count', str(count))
            #
            #     else:


def get_script_named_entity_counts(script_to_script_to_scorestruct):
    script_to_ne_counts = defaultdict(int)
    with open('/home/nlg-05/deri/gazetteer/lang_lang_dist/script.counts.uniq', 'r') as counts_file:
        for line in counts_file:
            count, script = line.rstrip().split()
            count = int(count)
            script_to_ne_counts[script] = count

    for script, count in script_to_ne_counts.items():
        if script in script_to_script_to_scorestruct:
            for script1 in script_to_script_to_scorestruct:
                script_to_script_to_scorestruct[script1][script].set_feat('named_entity_count', str(count))


def get_script_unicode_dists():
    script_to_pared_chars, all_pared_chars = get_script_to_pared_chars()
    script_to_char_features = get_pared_down_chars_as_features(script_to_pared_chars, all_pared_chars)
    pprint.pprint(script_to_pared_chars)

    for script1, char_features1 in sorted(script_to_char_features.items()):
        for script2, char_features2 in sorted(script_to_char_features.items()):
            cos_dist = scipy.spatial.distance.cosine(char_features1, char_features2)
            if 'e' in str(cos_dist):
                cos_dist = 0.0
            script_to_script_to_scorestruct[script1][script2].set_dist('transliterable', cos_dist)


def get_lang_pared_char_sets_dists():
    lang_to_pared_char_set, lang_to_char_set, all_pared_chars = get_lang_to_pared_char_set_short()

    code_to_ne_counts = get_code_to_ne_counts()

    """remove codes with very little data"""
    for code, ne_count in code_to_ne_counts.items():
        if ne_count < 500:
            lang_to_pared_char_set.pop(code)
            lang_to_char_set.pop(code)

    lang_to_char_features = get_pared_down_chars_as_features(lang_to_pared_char_set, all_pared_chars)


    # pprint.pprint(lang_to_char_features)

    uriel_loaded = True
    if len(code_to_code_to_scorestruct) == 0:
        uriel_loaded = False

    for iso_code1, char_features1 in sorted(lang_to_char_features.items()):
        # if uriel_loaded and iso_code1 not in code_to_code_to_scorestruct and code_to_ne_counts[iso_code1] < :
        # continue
        for iso_code2, char_features2 in sorted(lang_to_char_features.items()):
            # if uriel_loaded and iso_code2 not in code_to_code_to_scorestruct:
            # continue

            cos_dist = scipy.spatial.distance.cosine(char_features1, char_features2)
            if 'e' in str(cos_dist):
                cos_dist = 0.0
            code_to_code_to_scorestruct[iso_code1][iso_code2].set_dist('transliterable', cos_dist)


def get_wiki_to_lang_dict():
    wiki_to_lang = dict()

    with open('/auto/nlg-05/deri/elisa_data/data/text-extracts/wiki-languages.txt', 'r') as in_file:
        for line in in_file:
            # list_of_wikis.append(line.strip().split()[3])
            line = line.strip().split()
            for i, elem in enumerate(line):
                elem = elem.replace(',', '')

                if elem.isdigit() and i != 0:
                    wikicode = line[i - 1]

                    lang_name = ' '.join(line[1:i - 1])
                    iso_code = iso_codes.parse_language_codes.find_isocode_for_wikicode(wikicode)

                    wiki_to_lang[iso_code] = lang_name
                    break
    return wiki_to_lang


def add_wiki_info_and_europarl(code_to_code_to_scorestruct):
    wiki_to_lang = get_wiki_to_lang_dict()
    europarl_iso_codes = set(get_europarl_iso_codes())

    for code1 in code_to_code_to_scorestruct:
        for code2 in code_to_code_to_scorestruct[code1]:
            has_wiki = '-'
            is_europarl = '-'
            if code2 in wiki_to_lang:
                has_wiki = '+'
            if code2 in europarl_iso_codes:
                is_europarl = '+'
            code_to_code_to_scorestruct[code1][code2].set_feat('wiki', has_wiki)
            code_to_code_to_scorestruct[code1][code2].set_feat('europarl', is_europarl)


def get_same_alph():
    omniglot_iso_code_to_scripts_info = get_omniglot_iso_code_to_scripts_info()
    lang_to_script = get_lang_script_info()

    for code1 in code_to_code_to_scorestruct:

        if code1 in lang_to_script:
            scripts_1 = {lang_to_script[code1].lower().capitalize()}
            # print(code1, scripts_1)
        elif code1 in omniglot_iso_code_to_scripts_info:
            scripts_1 = omniglot_iso_code_to_scripts_info[code1].get_all_scripts()
        else:
            continue
            # print('ERROR', code1)

        for code2 in code_to_code_to_scorestruct[code1]:


            if code2 in lang_to_script:
                scripts_2 = {lang_to_script[code2].lower().capitalize()}
            elif code2 in omniglot_iso_code_to_scripts_info:
                scripts_2 = omniglot_iso_code_to_scripts_info[code2].get_all_scripts()
                # print(code2, scripts_2)
            else:
                continue
                # print('ERROR', code1, code2)

            if scripts_1 is None or scripts_2 is None:
                code_to_code_to_scorestruct[code1][code2].set_feat('same_alph', '0')

            elif scripts_1.isdisjoint(scripts_2):
                code_to_code_to_scorestruct[code1][code2].set_feat('same_alph', '-')
            else:
                # print('here')
                code_to_code_to_scorestruct[code1][code2].set_feat('same_alph', '+')
                #
                # elif code1
                # for code2 in code_to_code_to_scorestruct[code1]:
                # same_alph = '-'


def read_in_bitdist():
    print('reading in bitdist')
    phon_to_phon_to_bitdist = defaultdict(dict)
    with open('/auto/nlg-05/deri/gazetteer/ipa/ipa.bitdist.table', 'r') as infile:
        for line in infile:
            phon1, phon2, dist = line.rstrip().split('\t')
            dist = float(dist)
            phon_to_phon_to_bitdist[phon1][phon2] = dist
    return phon_to_phon_to_bitdist


def compute_phoible_similarity(lang1, lang2, phoneme_set1, phoneme_set2, phoneme_to_output, phon_to_phon_to_bitdist):
    phoible_sim = 0.0
    if lang1 == lang2:
        return 0.0

    for phon1 in phoneme_set1:
        if phon1 in phoneme_set2:
            continue

        max_weight = -1.0
        max_phon = ''
        for phon2 in phoneme_set2:
            if phon1 in phon_to_phon_to_bitdist and phon2 in phon_to_phon_to_bitdist[phon1] and \
                            phon_to_phon_to_bitdist[phon1][phon2] > max_weight:
                max_weight = phon_to_phon_to_bitdist[phon1][phon2]
                max_phon = phon2
        # max_weight = max(phon_to_phon_to_bitdist[phon1], key=phon_to_phon_to_bitdist[phon1].get)

        # if phon1 in phoneme_to_output:
        # output = phoneme_to_output[phon1]
        # else:
        #     command = ['grep', '^{0}\t'.format(phon1), '/auto/nlg-05/deri/gazetteer/ipa/ipa.bitdist.table']
        #     output = check_output(command).rstrip().decode('utf-8').split('\n')
        #     phoneme_to_output[phon1] = output

        # max_weight = -1.0
        # max_phon = ''
        # for line in output:
        #     line = line.split('\t')
        #     found_phon = line[1]
        #
        #     if found_phon in phoneme_set2:
        #         weight = float(line[2])
        #
        #         if weight > max_weight:
        #             max_weight = weight
        #             max_phon = found_phon
        # print (1- max_weight, phon1, max_phon)
        phoible_sim += 1 - max_weight

    return phoible_sim


def get_phoible_similarity_unchanged():
    with open('phonetic.dists.clean', 'r') as phonetic_dist_file:
        phonetic_dist_file.readline()
        for line in phonetic_dist_file:
            code1, code2, dist = line.rstrip().split('\t')
            if dist != 'None':
                dist = float(dist)
                code_to_code_to_scorestruct[code1][code2].set_dist('phonetic', dist)


def add_unchanged(code1, code2, dist_name, dist):
    if dist != 'None':
        dist = float(dist)
        code_to_code_to_scorestruct[code1][code2].set_dist(dist_name, dist)


def load_uriel_unchanged():
    with open('uriel.dists.clean', 'r') as uriel_dist_file:
        uriel_dist_file.readline()
        for line in uriel_dist_file:
            code1, code2, u_avg, u_composite, u_genetic, u_geo, u_p, u_s = line.rstrip().split('\t')
            add_unchanged(code1, code2, 'u_avg', u_avg)
            add_unchanged(code1, code2, 'u_composite', u_composite)
            add_unchanged(code1, code2, 'u_genetic', u_genetic)
            add_unchanged(code1, code2, 'u_geo', u_geo)
            add_unchanged(code1, code2, 'u_p', u_p)
            add_unchanged(code1, code2, 'u_s', u_s)


def get_phoible_similarity():
    listing = glob.glob('/auto/nlg-05/deri/gazetteer/ipa/phoneme_sets/*.set')
    phon_to_phon_to_bitdist = read_in_bitdist()
    all_phoible_langs = set()
    phoneme_to_output = dict()

    for i, filename in enumerate(listing):
        all_phoible_langs.add(filename[len('/auto/nlg-05/deri/gazetteer/ipa/phoneme_sets/'):].split('.')[0])

    lang_to_phoible_set = dict()
    for lang in all_phoible_langs:
        phoneme_set = get_lang_phoneme_set(lang)
        if len(phoneme_set) != 0:
            phoneme_set.remove('_')
            lang_to_phoible_set[lang] = phoneme_set

    for lang1 in sorted(lang_to_phoible_set.keys()):
        print(lang1)
        phoneme_set1 = lang_to_phoible_set[lang1]
        if len(phoneme_set1) == 0:
            continue

        code2_to_dist = dict()

        i = 0
        for lang2 in sorted(lang_to_phoible_set.keys()):
            i += 1
            phoneme_set2 = lang_to_phoible_set[lang2]

            code2_to_dist[lang2] = compute_phoible_similarity(lang1, lang2, phoneme_set1, phoneme_set2,
                                                              phoneme_to_output, phon_to_phon_to_bitdist)

        min_score = min(code2_to_dist.values())
        max_score = max(code2_to_dist.values())
        # print(min_score, max_score)
        for lang2, dist in code2_to_dist.items():
            dist = (dist - min_score) / (max_score - min_score)
            code2_to_dist[lang2] = dist
            code_to_code_to_scorestruct[lang1][lang2].set_dist('phonetic', dist)


def append_to_indiv_vals(code2, indices_with_none, indiv_lang, list_of_list_of_indiv_vals_1,
                         list_of_list_of_indiv_vals_2):
    if indiv_lang in code_to_code_to_scorestruct and code2 in code_to_code_to_scorestruct[indiv_lang]:
        # print('indiv_lang to code2', indiv_lang, code2)
        indiv_code_values = code_to_code_to_scorestruct[indiv_lang][code2].get_dist_vals()
        relevant_indiv_values = [indiv_code_values[i] for i in indices_with_none]
        # print(indiv_code_values, relevant_indiv_values)
        for i, indiv_value in enumerate(relevant_indiv_values):
            if indiv_value is not None:
                list_of_list_of_indiv_vals_1[i].append(indiv_value)
    if code2 in code_to_code_to_scorestruct and indiv_lang in code_to_code_to_scorestruct[code2]:
        indiv_code_values = code_to_code_to_scorestruct[code2][indiv_lang].get_dist_vals()
        relevant_indiv_values = [indiv_code_values[i] for i in indices_with_none]
        # print(indiv_code_values, relevant_indiv_values)
        for i, indiv_value in enumerate(relevant_indiv_values):
            if indiv_value is not None:
                list_of_list_of_indiv_vals_2[i].append(indiv_value)


def get_unified_macro_lang_info():
    macro_to_indiv = iso_codes.parse_language_codes.get_macro_to_indiv()
    orig_codes = {key for key in code_to_code_to_scorestruct}
    for macro_code in sorted(macro_to_indiv.keys()):

        for code2 in orig_codes:
            if macro_code in orig_codes and code2 in code_to_code_to_scorestruct[macro_code]:
                macro_code_values = code_to_code_to_scorestruct[macro_code][code2].get_dist_vals()
                indices_with_none = [i for i, x in enumerate(macro_code_values) if x is None]
            else:
                indices_with_none = [i for i, x in enumerate(DIST_ATTR_LIST)]
            # print(macro_code_values, indices_with_none)

            list_of_list_of_indiv_vals_1 = []  #create all the individual language values
            for i in range(len(indices_with_none)):
                list_of_list_of_indiv_vals_1.append([])
            list_of_list_of_indiv_vals_2 = []  #create all the individual language values
            for i in range(len(indices_with_none)):
                list_of_list_of_indiv_vals_2.append([])

            for indiv_lang in macro_to_indiv[macro_code]:
                if code2 not in macro_to_indiv:
                    append_to_indiv_vals(code2, indices_with_none, indiv_lang, list_of_list_of_indiv_vals_1,
                                         list_of_list_of_indiv_vals_2)
                else:
                    for indiv_lang_2 in macro_to_indiv[code2]:
                        append_to_indiv_vals(indiv_lang_2, indices_with_none, indiv_lang,
                                             list_of_list_of_indiv_vals_1, list_of_list_of_indiv_vals_2)

            # pprint.pprint(list_of_list_of_indiv_vals_1)
            # pprint.pprint(list_of_list_of_indiv_vals_2)

            avg_vals_1 = []
            avg_vals_2 = []
            for i, lst_1 in enumerate(list_of_list_of_indiv_vals_1):
                lst_2 = list_of_list_of_indiv_vals_2[i]
                if len(lst_1) == 0:
                    avg_vals_1.append(None)
                else:
                    avg_vals_1.append(sum(lst_1) / len(lst_1))

                if len(lst_2) == 0:
                    avg_vals_2.append(None)
                else:
                    avg_vals_2.append(sum(lst_2) / len(lst_2))
            # pprint.pprint(avg_vals_1)

            for i, index_with_none in enumerate(indices_with_none):
                avg_val_1 = avg_vals_1[i]
                if avg_val_1 is None:
                    continue
                dist_attr_string = DIST_ATTR_LIST[index_with_none]
                # print(dist_attr_string, avg_val_1)
                code_to_code_to_scorestruct[macro_code][code2].set_dist(dist_attr_string, avg_val_1)

            for i, index_with_none in enumerate(indices_with_none):
                avg_val_2 = avg_vals_2[i]
                if avg_val_2 is None:
                    continue
                dist_attr_string = DIST_ATTR_LIST[index_with_none]
                # print(dist_attr_string, avg_val_2)
                code_to_code_to_scorestruct[code2][macro_code].set_dist(dist_attr_string, avg_val_2)

            # print('FINAL')
            # print(macro_code, code2, code_to_code_to_scorestruct[macro_code][code2].get_dist_vals())
            # print(code2, macro_code, code_to_code_to_scorestruct[code2][macro_code].get_dist_vals())



def get_lang_dists():
    """metrics"""
    # load_uriel()
    # load_uriel_unchanged()
    print('loaded uriel')

    get_lang_pared_char_sets_dists()
    print('got pared char distances')

    """don't get omniglot scripts!!!"""
    # get_omniglot_scripts()
    # print('got omniglot scripts')
    # get_phoible_similarity()


    get_phoible_similarity_unchanged()
    get_unified_macro_lang_info() #this needs to come after all other distances are created

    #
    # """features"""
    # get_named_entity_counts(code_to_code_to_scorestruct)
    # print('got named entity counts')
    # #
    # add_wiki_info_and_europarl(code_to_code_to_scorestruct)
    #
    #
    # print('getting alphabet information')
    # get_same_alph()

    # avg_dict('avg', 'u_avg')
    #
    print_dict_to_file(DISTS_FILE)


def get_script_dists():
    get_script_unicode_dists()
    avg_dict_script()
    get_script_named_entity_counts(script_to_script_to_scorestruct)
    script_print_dict_to_file(SCRIPT_DISTS_FILE)


if __name__ == '__main__':
    # x = ScoreStruct()
    # print(x)


    # lorelei_codes = 'ben hau tam tgl tha tur urd uzb'.split(' ')
    # iso_code_set = set(europarl_iso_codes + lorelei_codes)
    # print(iso_code_set)

    code_to_code_to_scorestruct = defaultdict(lambda: defaultdict(ScoreStruct))

    # load_uriel(iso_code_set)
    get_lang_dists()

    script_to_script_to_scorestruct = defaultdict(lambda: defaultdict(ScriptScoreStruct))

    # get_script_dists()

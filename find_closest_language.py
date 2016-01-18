import argparse
import os
import pprint
from subprocess import check_output, Popen, PIPE
import sys
sys.path.append('/nfs/guest2/aderi/unidecode/lib/python3.4/site-packages/')

from unidecode import unidecode

__author__ = 'aderi'

# import sys

sys.path.append('/auto/nlg-05/deri/gazetteer')
sys.path.append('/')
try:
    from lang_lang_dist.calc_lang_lang_dist import get_feat_attr_list, get_dist_attr_list
except ImportError:
    from calc_lang_lang_dist import get_feat_attr_list, get_dist_attr_list

LANG_DISTS = '/auto/nlg-05/deri/gazetteer/lang_lang_dist/lang.dists'
if not os.path.exists(LANG_DISTS):
    LANG_DISTS = 'lang.dists'
if not os.path.exists(LANG_DISTS):
    LANG_DISTS = '/users/aderi/lang.dists'


from iso_codes import parse_language_codes

extra_wiki_to_lang = {'bat-smg': 'Samogitian',
                      'be-x-old': 'Old Belarusian',
                      'cbk-zam': 'Zamboanga Chavacano',
                      'eml': 'Emilian-Romagnol',
                      'fiu-vro': 'Võro',
                      'map-bms': 'Banyumasan Basa', 'mo': 'Moldovan', 'nah': 'Nahuatl',
                      'nds-nl': 'Dutch Low Saxon',
                      'roa-rup': 'Aromanian',
                      'roa-tara': 'Tarantino',
                      'simple': 'Simple English',
                      'zh-classical': 'Classical Chinese',
                      'zh-min-nan': 'Min Nan',
                      'zh-yue': 'Cantonese'
}

getVar = lambda searchList, ind: [searchList[i] for i in ind]


def parse_arguments():
    global il, sort_by, get_top, second_sort, wiki, europarl, same_alph, named_entity_count, cap_nones, print_all
    parser = argparse.ArgumentParser()
    parser.add_argument('--il', action='store', type=str, help='incident language')
    parser.add_argument('--sort_by', action='store', nargs='?', default='avg', type=str)
    parser.add_argument('--top', action='store', nargs='?', default=10, type=int)
    parser.add_argument('--second_sort', action='store', nargs='?', type=str)
    parser.add_argument('--wiki', action='store_true')
    parser.add_argument('--europarl', action='store_true')
    parser.add_argument('--same_alph', action='store_true')
    parser.add_argument('--print_all', action='store_true')
    parser.add_argument('--cap_nones', action='store', type=int, const=4, nargs='?')
    parser.add_argument('--named_entity_count', action='store', type=int, nargs='?', const=1, default=0)
    # parser.add_argument('--d', action='store_true')
    args = parser.parse_args()

    il = args.il
    sort_by = args.sort_by
    get_top = args.top
    second_sort = args.second_sort
    wiki = args.wiki
    europarl = args.europarl
    same_alph = args.same_alph
    named_entity_count = args.named_entity_count
    cap_nones = args.cap_nones
    print_all = args.print_all


def make_pretty_float(f):
    if f is None:
        return 'None'
    if type(f) is not float:
        return str(f)
    # if f == 1.0 or f == 0.0:
    # return str(f)
    return "%0.2f" % f


def compare_none_and_int(elem):
    if elem == 'None':
        return 100
    else:
        return elem


if __name__ == '__main__':
    parse_arguments()

    DIST_ATTR_LIST = get_dist_attr_list()
    FEAT_ATTR_LIST = get_feat_attr_list()

    assert sort_by in DIST_ATTR_LIST
    assert second_sort is None or second_sort in DIST_ATTR_LIST

    dist_to_index = dict()
    feat_to_index = dict()
    dist_and_feat_to_index = dict()
    with open(LANG_DISTS, 'r') as dists_file:
        line = dists_file.readline().rstrip().split('\t')
        for i, elem in enumerate(line):
            if elem in DIST_ATTR_LIST:
                dist_and_feat_to_index[elem] = i
                dist_to_index[elem] = i
            if elem in FEAT_ATTR_LIST:
                feat_to_index[elem] = i
                dist_and_feat_to_index[elem] = i

    sort_by_index = dist_to_index[sort_by]
    indices_to_print = [0, 1, sort_by_index]
    named_entities_index = feat_to_index['named_entity_count']
    same_alph_index = feat_to_index['same_alph']
    

    command1 = ['grep', '^{0}\t'.format(il), LANG_DISTS]
    p1 = Popen(command1, stdout=PIPE)
    output = p1.communicate()[0].decode('utf-8').split('\n')

    # command2 = ['sort', '-V', '-k{0}'.format(sort_by_index + 1)]
    # p2 = Popen(command2, stdin=p1.stdout, stdout=PIPE)
    # p1.stdout.close()
    # output = p2.communicate()[0].decode('utf-8').split('\n')

    for i, line in enumerate(output):
        line = line.split('\t')
        for j, elem in enumerate(line):
            try:
                if j == named_entities_index or (j == same_alph_index and elem == '0'):
                    line[j] = int(elem)
                    # print(type(line[j]))
                else:
                    line[j] = float(elem)
            except ValueError:
                pass
        output[i] = line
    if len(output[len(output) - 1]) == 0 or len(output[len(output) - 1]) == 1:
        output.pop(len(output) - 1)

    if cap_nones is not None:
        output = [line for line in output if line.count('None') <= cap_nones]

    output.sort(key=lambda x: compare_none_and_int(x[sort_by_index]))

    features_to_print = []
    if wiki or europarl or same_alph or named_entity_count > 0:
        if wiki:
            wiki_index = feat_to_index['wiki']
            output = [line for line in output if line[wiki_index] == '+']
            features_to_print.append(wiki_index)
        if europarl:
            europarl_index = feat_to_index['europarl']
            output = [line for line in output if line[europarl_index] == '+']
            features_to_print.append(europarl_index)
        if same_alph:
            same_alph_index = feat_to_index['same_alph']
            output = [line for line in output if line[same_alph_index] == '+']
            features_to_print.append(same_alph_index)
        if named_entity_count > 0:
            named_entities_index = feat_to_index['named_entity_count']
            output = [line for line in output if line[named_entities_index] > named_entity_count]
            features_to_print.append(named_entities_index)

    if second_sort is None:
        top_output = output[: get_top]

    else:
        assert second_sort in DIST_ATTR_LIST
        second_sort_index = dist_to_index[second_sort]
        indices_to_print.append(second_sort_index)

        top_output = output[:get_top]

        top_output.sort(key=lambda x: compare_none_and_int(x[second_sort_index]))

    indices_to_print += features_to_print

    top_output_to_print = list()
    for i, line in enumerate(top_output):
        top_output[i] = [make_pretty_float(item) for item in line]

    # print(indices_to_print)

    names_to_print = ['lang1', 'lang2']

    if not print_all:
        top_output = [getVar(line, indices_to_print) for line in top_output]
    else:
        indices_to_print = [0, 1] + sorted(list(dist_to_index.values())) + sorted(list(feat_to_index.values()))

    for i in indices_to_print:
        names_to_print += [k for k, v in dist_and_feat_to_index.items() if v == i]

    for i, line in enumerate(top_output):
        lang_name = parse_language_codes.find_lang_for_code(line[1])
        if lang_name is None:
            lang_name = extra_wiki_to_lang[line[1]]
        top_output[i].insert(2, lang_name)
    names_to_print.insert(2, 'name')
    top_output.insert(0, names_to_print)

    for line in top_output:
        print(unidecode('\t'.join(line)))



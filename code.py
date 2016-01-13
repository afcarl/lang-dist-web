import pprint
import subprocess
import web
import web.form as form
import sys

sys.path.append('/')
from iso_codes.parse_language_codes import get_code_to_lang, find_lang_for_code
from calc_lang_lang_dist import get_dist_attr_list
from unidecode import unidecode

# from web.template import render

render = web.template.render('.')

urls = (
    '/', 'index'
)


def get_code_lang_tuples():
    with open('included-langs', 'r') as lang_file:
        code_to_lang = get_code_to_lang()
        code_lang_tuples = ['{0}-{1}'.format(code.rstrip(), unidecode(code_to_lang[code.rstrip()])) for code in
                            lang_file if code.rstrip() in code_to_lang]
    # code_lang_tuples = sorted(['{0}-{1}'.format(code, unidecode(lang)) for code, lang in get_code_to_lang().items()])
    return code_lang_tuples


def get_dist_drop_down(include_none=False):
    dist_drop_down = [tuple([dist, dist]) for dist in get_dist_attr_list()]
    if include_none:
        dist_drop_down.insert(0, tuple(['None', 'None']))
    return dist_drop_down


myform = form.Form(
    # form.Textbox('isocode'),
    form.Dropdown('isocode', get_code_lang_tuples()),
    form.Dropdown('sort by', get_dist_drop_down()),
    form.Dropdown('second sort', get_dist_drop_down(True)),
    form.Textbox('# returned', form.regexp('\d*', 'Must be a digit')),
    form.Textbox('max # Nones', form.regexp('\d*', 'Must be a digit')),
    form.Textbox('min # named entity pairs', form.regexp('\d*', 'Must be a digit')),
    form.Checkbox('wikipedia', value='blah'),
    form.Checkbox('europarl', value='blah'),
    form.Checkbox('same alphabet', value='blah'),
    form.Checkbox('print all values', value='blah'),
    form.Button('go!', type='submit'),
)


class index:
    def GET(self):
        f = myform()
        return render.formtest(f, "")

    def POST(self):
        f = myform()
        f.validates()
        # if not f.validates():
        # return render.formtest(form)
        # else:
        # form.d.boe and form['boe'].value are equivalent ways of
        # extracting the validated arguments from the form.

        # return render.formtest(f, "Grrreat success! boe: %s, bax: %s" % (f.d.isocode, f['wikipedia'].value))

        pprint.pprint(f.d)

        # -il IL               incident language
        # --sort_by [SORT_BY]
        # --top [TOP]
        # --second_sort [SECOND_SORT]
        # --wiki
        # --europarl
        # --same_alph
        # --print_all
        # --cap_nones [CAP_NONES]
        # --named_entity_count [NAMED_ENTITY_COUNT]
        il = f['isocode'].value.split('-')[0]
        sort_by = f['sort by'].value
        second_sort = f['second sort'].value
        top = f['# returned'].value
        cap_nones = f['max # Nones'].value
        named_entity_count = f['min # named entity pairs'].value
        wiki = f['wikipedia'].checked
        europarl = f['europarl'].checked
        same_alph = f['same alphabet'].checked
        print_all = f['print all values'].checked

        all_vars = [il, sort_by, second_sort, top, cap_nones, named_entity_count, wiki, europarl, same_alph, print_all]
        str_to_print = ""
        for var in all_vars:
            str_to_print += str(var) + ' '

        print(all_vars)

        command = ['python3', 'find_closest_language.py', '--il={0}'.format(il), '--sort_by={0}'.format(sort_by)]

        if second_sort != 'None':
            command.append('--second_sort={0}'.format(second_sort))

        if top != '':
            command.append('--top={0}'.format(top))

        if cap_nones != '':
            command.append('--cap_nones={0}'.format(cap_nones))

        if named_entity_count != '':
            command.append('--named_entity_count={0}'.format(named_entity_count))

        if wiki:
            command.append('--wiki')
        if europarl:
            command.append('--europarl')
        if same_alph:
            command.append('--same_alph')
        if print_all:
            command.append('--print_all')

        print ' '.join(command)
        p1 = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p1.communicate()[0].decode('utf-8').split('\n')
        output = [line.split('\t') for line in output]

        # return render.formtest(f, "Grrreat success! isocode: %s, wikipedia: %s, europarl: %s" % (
        #     f.d.isocode, f['wikipedia'].checked, f.d.europarl))
        return render.formtest(f, output)


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

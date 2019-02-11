import sys
import os
from os import path
import urwid
import urwid.curses_display
import urwid.raw_display
import urwid.web_display
import urwid.util
import subprocess
import fuzzywuzzy.process
import logging
import yaml
from appdirs import AppDirs

a = 'hello'
dirs = AppDirs("term-cheat", "Select")
commands_file_path = path.join(dirs.user_data_dir, 'commands.yaml')

# If the base commands do not exist copy them from the main app.
if not os.path.exists(dirs.user_data_dir):
    os.makedirs(dirs.user_data_dir)
if not path.isfile(commands_file_path):
    original_commands = []
    with open(path.join(path.dirname(path.abspath(__file__)), 'commands.yaml'), 'r') as stream:
        original_commands = yaml.load(stream)
    with open(commands_file_path, 'w') as stream:
        yaml.dump(original_commands, stream, default_flow_style=False)


# disable logging or fuzzywuzzy will destroy the UI
logging.basicConfig(level=logging.ERROR)

app_state = {
    'mode': 'list',
    'filterd': False,
    'commandIndex': 0,
    'editor': {
        'name': None,
        'command': None,
        'description': None,
        'tags': None,
    },
    'commands': [],
    'commands_unfilterd': [],
    'commands_lookup': {},
    'commands_unfilterd_lookup': {},
}


def indexCommands():
    for key in ['commands', 'commands_unfilterd']:
        commands = app_state[key]
        for idx, c in enumerate(commands):
            c['all'] = ' '.join([v for k, v in c.items() if k not in ('all', 'index')])
            c['index'] = idx
            app_state[key + '_lookup'][c['all']] = c


with open(commands_file_path, 'r') as stream:
    app_state['commands'] = yaml.load(stream)
    app_state['commands_unfilterd'] = app_state['commands'].copy()
indexCommands()


color_grey = 'g93'
color_grey1 = 'g89'
color_tourquise = '#6da'
color_blue = '#6af'
palette = [
    # name, foreground, background, mono, foreground_high, background_high
    ('header', 'black,underline', 'light gray', 'standout,underline', 'white', color_tourquise),
    ('headerEnd', 'black,underline', 'light gray', 'standout,underline', color_tourquise, ''),
    ('footer', 'black,underline', 'light gray', 'standout,underline', 'black', color_grey),
    ('commandCol', 'black,underline', '', '', color_blue, ''),
    ('reversed', 'standout', '', '', '', color_blue),
    ('reversed2', 'standout', '', '', '#f00', color_blue),
    ('hightlightKey', 'standout', '', '', 'white', 'g70'),
    ('seperator', 'black', '', '', '#fff', color_grey),
    ('editor', '', '', '', '#8ad', color_grey1),
    ('editField', '', '', '', '#000', '#fff'),
    ('editButtons', '', '', '', '#000', color_grey1),
    ('editButtonsActive', '', '', '', '#fff', color_tourquise),
]


def unhandledInput(key):
    # ui_message.set_text(str(key) + ' ' + str(app_state['commandIndex']) + app_state['mode'])
    if key in ('Q', 'q', 'ctrl c'):
        exit()

    if app_state['mode'] is 'edit':
        if key is 'tab':
            footer = app_state['editListBox']
            if footer.focus_position < 4:
                footer.set_focus(footer.focus_position + 1)
        if key == 'ctrl o':
            saveEdit()
        if key is 'esc':
            cancelEdit()
        return

    if app_state['mode'] is 'list':
        if key in ('e', 'c'):
            startEditOrClone(key)
        if key is 'd':
            deleteCommand()
        if key is '/':
            startFilter()
        if key == 'shift up' and not app_state['filterd']:  # FIXME this is not working yet
            item = app_state['commands'][app_state['commandIndex']]
            del app_state['commands'][app_state['commandIndex']]
            new_index = app_state['commandIndex'] - 1
            app_state['commands'].insert(new_index, item)
            ui_main_frame.body = menu(app_state['commands'])
            ui_main_frame.body.set_focus(new_index)
        if key in ('a', 'ctrl n'):
            startEditOrClone('a')
        if key is 'esc':
            if app_state['filterd']:
                app_state['filterd'] = False
                ui_esc_filtered.set_text('')
                ui_input_filter.edit_text = ''
                ui_main_frame.body = menu(app_state['commands_unfilterd'])
            else:
                exit()
        return

    if app_state['mode'] is 'filter':
        if key is 'esc':
            ui_input_filter.edit_text = ''
            ui_main_frame.body = menu(app_state['commands_unfilterd'])
        if key is 'enter':
            app_state['filterd'] = True
            app_state['filterd']
        if key in ('esc', 'enter'):
            app_state['mode'] = 'list'
            ui_body.footer = ui_footer
            ui_body.focus_position = 'body'


def newCommand(command=False):
    if not command:
        return {'name': '', 'command': '', 'description': '', 'tags': ''}
    new_command = dict([(k, v) for k, v in command.items() if k != 'name'])
    new_command['name'] = ''
    return new_command


def deleteCommand(e=None):
    command = app_state['commands'][app_state['commandIndex']]
    ui_yes = customButton('Delete', onDeleteConfirmed)
    ui_no = customButton('Cancel', closePopUp)
    openPopUp(urwid.Pile([
        urwid.Text('Delete entry "' + command['command']+'"'),
        urwid.Divider(),
        urwid.Columns([ui_no, ui_yes])
    ]))


def onDeleteConfirmed(e=None):
    key = app_state['commands'][app_state['commandIndex']]['all']
    del app_state['commands_unfilterd'][app_state['commands_unfilterd_lookup'][key]['index']]
    del app_state['commands'][app_state['commandIndex']]
    ui_main_frame.body = menu(app_state['commands'])
    if (app_state['commandIndex'] >= len(app_state['commands']) - 1):
        app_state['commandIndex'] -= 1
    ui_main_frame.body.set_focus(app_state['commandIndex'])
    indexCommands()
    saveCommands()
    closePopUp()


def startEditOrClone(key):
    command = app_state['commands'][app_state['commandIndex']]
    if key == 'c':  # if the command should be cloned
        command = newCommand(app_state['commands'][app_state['commandIndex']])
        app_state['commandIndex'] = -1  # indicate that we are not editing an existing entry anmymore
    if key == 'a':  # if new command
        command = newCommand()
        app_state['commandIndex'] = -1  # indicate that we are not editing an existing entry anmymore
    ui_main_frame.footer = uiEditor(command)
    ui_main_frame.focus_position = 'footer'
    # ui_body.footer = ui_editor_footer
    app_state['mode'] = 'edit'


def startFilter(e=None):
    app_state['mode'] = 'filter'
    ui_body.footer = ui_filter
    ui_body.focus_position = 'footer'
    ui_input_filter.edit_text = ''
    ui_esc_filtered.set_text('')


class BoxButton(urwid.WidgetWrap):
    signals = ["click"]

    def __init__(self, widgets, on_press=None, user_data=None):
        padding_size = 2
        # cursor_position = len(border) + padding_size
        self.widgets = widgets
        self.widget = urwid.Columns(widgets)
        if on_press:
            urwid.connect_signal(self, 'click', on_press, user_data)
        super(BoxButton, self).__init__(self.widget)

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self._command_map[key] != urwid.ACTIVATE:
            return key
        self._emit('click')

    def mouse_event(self, size, event, button, x, y, focus):
        if button != 1 or not urwid.util.is_mouse_press(event):
            return False
        self._emit('click')
        return True


def setCommandIndex():
    app_state['commandIndex'] = ui_main_frame.body.focus_position
    ui_message.set_text('index ' + str(app_state['commandIndex']))


def menu(commands):
    app_state['commands'] = commands
    list_items = []
    for c in commands:
        button = BoxButton([
            ('weight', 1, urwid.Text(c['name'], wrap='clip')),
            ('pack', urwid.Text(' ')),
            ('weight', 1, urwid.AttrMap(urwid.Text(c['command'], wrap='clip'), 'commandCol', 'reversed2')),
            ('pack', urwid.Text(' ')),
            ('weight', 4, urwid.Text(c['description'], wrap='clip'))
        ])
        urwid.connect_signal(button, 'click', itemChosen, c)
        list_items.append(urwid.AttrMap(button, None, focus_map='reversed'))
    walker = urwid.SimpleFocusListWalker(list_items)
    urwid.connect_signal(walker, 'modified', setCommandIndex)
    return urwid.ListBox(walker)


def runCommand(e=None, command_string=None):
    loop.stop()
    urwid.ExitMainLoop()
    if not command_string:
        command_string = app_state['commands'][app_state['commandIndex']]['command']
    # subprocess.Popen(['bash', '-ic', 'set -o history; history -s "$1"', '_', command_string])
    subprocess.Popen(['zsh', '-ic', 'print -s "$1"', '_', command_string])
    # os.system('fc -S "%s"'%command_string)
    # subprocess.Popen('history -s "%s"'%command_string, shell=True, executable=os.environ['SHELL'])
    # subprocess.Popen(command_string, shell=True)
    os.system(command_string)
    sys.exit()


def itemChosen(button, choice):
    runCommand(command_string=choice['command'])


def onFilter(text, other):
    if (ui_input_filter.edit_text):
        hits = fuzzywuzzy.process.extract(ui_input_filter.edit_text, [c['all'] for c in app_state['commands_unfilterd']])
        ui_num_results.set_text(' %s matches' % (len(hits)))
        ui_main_frame.body = menu([app_state['commands_unfilterd_lookup'][r[0]] for r in hits])
        ui_esc_filtered.set_text('')
        ui_esc_filtered.set_text([('hightlightKey', 'Esc'), ' clear filter'])
        return
    ui_main_frame.body = menu(app_state['commands_unfilterd'])
    ui_num_results.set_text(' %s matches' % (len(app_state['commands_unfilterd'])))


def createEditText(name, command, height=1):
    value = command[name.lower()]
    ui_edit = urwid.Edit(edit_text=value, multiline=height > 1)
    app_state['editor'][name.lower()] = ui_edit
    return urwid.LineBox(urwid.AttrMap(ui_edit, 'editField'), name, 'left')


def cancelEdit(e=None):
    app_state['mode'] = 'list'
    ui_main_frame.focus_position = 'body'
    ui_main_frame.footer = urwid.Divider()
    ui_body.footer = ui_footer


def saveCommands():
    out = app_state['commands_unfilterd'].copy()
    for x in out:
        del x['all']
        del x['index']
    with open(commands_file_path, 'w') as stream:
        yaml.dump(out, stream, default_flow_style=False)


def saveEdit(e=None):
    old_command = app_state['commands'][app_state['commandIndex']]
    new_command = dict([[key, ui_editor.get_edit_text()] for key, ui_editor in app_state['editor'].items()])
    if app_state['commandIndex'] <= 0:  # new command will be created
        app_state['commands'].append(new_command)
        app_state['commands_unfilterd'].append(new_command)
    else:
        for k, v in new_command.items():
            old_command[k] = v
        # app_state['commands_unfilterd'][app_state['commands_unfilterd_lookup'][old_command['all']]['index']] = new_command
        # app_state['commands'][app_state['commandIndex']] = new_command
    indexCommands()
    ui_main_frame.body = menu(app_state['commands'])
    cancelEdit()
    if app_state['commandIndex'] <= 0:  # new command
        ui_main_frame.body.set_focus(len(app_state['commands']) - 1)
    saveCommands()


def exit(e=None):
    raise urwid.ExitMainLoop()


class CustomButton(urwid.Button):
    button_left = urwid.Text('[')
    button_right = urwid.Text(']')

    def __init__(self, label, on_press=None, user_data=None):
        super(CustomButton, self).__init__(label)
        self._label.align = 'center'


def customButton(label, callback):
    button = CustomButton(label)
    urwid.connect_signal(button, 'click', callback)
    return urwid.AttrMap(button, 'editButtons', 'editButtonsActive')


class CustomButtonFooter(urwid.WidgetWrap):
    signals = ["click"]

    def __init__(self, label, on_press=None, user_data=None):
        self.widget = urwid.Text(label)
        if on_press:
            urwid.connect_signal(self, 'click', on_press, user_data)
        super(CustomButtonFooter, self).__init__(self.widget)

    def keypress(self, size, key):
        if self._command_map[key] != urwid.ACTIVATE:
            return key
        self._emit('click')

    def mouse_event(self, size, event, button, x, y, focus):
        if button != 1 or not urwid.util.is_mouse_press(event):
            return False
        self._emit('click')
        return True


def customButtonFooter(label1, label2, callback):
    button = CustomButtonFooter([('hightlightKey', label1), label2 + ' '])
    urwid.connect_signal(button, 'click', callback)
    return ('pack', button)


def uiEditor(command):
    edit_buttons = [
        urwid.Divider(),
        customButton('Save', saveEdit),
        urwid.Divider(),
        customButton('Cancel', cancelEdit),
        urwid.Divider(),
    ]

    app_state['editListBox'] = urwid.ListBox([
        urwid.AttrMap(urwid.Text('Edit'), 'header'),
        urwid.Divider(),
        urwid.Columns([
            createEditText('Name', command),
            createEditText('Command', command),
        ]),
        createEditText('Description', command, 2),
        urwid.Columns([
            createEditText('Tags', command),
            urwid.Pile([
                urwid.Divider(),
                urwid.AttrMap(urwid.Columns(edit_buttons), 'editButtons')
            ])
        ])
    ])
    return urwid.BoxAdapter(urwid.AttrMap(app_state['editListBox'], 'editor'), 12)


def openPopUp(widget):
    w = urwid.Overlay(
        urwid.AttrMap(
            urwid.LineBox(urwid.Filler(urwid.Padding(widget, 'center', 36))),
            'footer'
        ),
        ui_body,
        align='center',
        width=40,
        valign='middle',
        height=9
    )
    loop.widget = w


def closePopUp(e=None):
    loop.widget = ui_body


ui_editor_footer = urwid.AttrMap(urwid.Text([
    ('hightlightKey', 'Ctrl o'), ' save ',
    ('seperator', u'\uE0B1'), ' ',
    ('hightlightKey', 'Esc'), ' cancel ',
    ('seperator', u'\uE0B1'), ' ',
]), 'footer')

divider = urwid.Divider(u' ')
ui_header = urwid.BoxAdapter(urwid.Filler(urwid.Columns([
    ('pack', urwid.Text(('header', '⭐ Term Cheat  '))),
    urwid.Text(('headerEnd', u'\uE0B0'))  # power line symbol, must be installed or it looks crap
])), 2)
ui_input_filter = urwid.Edit()
ui_num_results = urwid.Text(('footer', ' %s matches' % (len(app_state['commands']))))
ui_filter = urwid.AttrMap(urwid.Columns([
    ('pack', urwid.Text('/')),
    ui_input_filter,
    ('pack', urwid.Text([('seperator', u'\uE0B1'), ' '])),
    ('pack', ui_num_results),
    ('pack', urwid.Text([
        ('seperator', u'\uE0B1'), ' ', ('hightlightKey', 'Enter'), ' to accept',
        ('seperator', u'\uE0B1'), ' ', ('hightlightKey', 'Esc'), ' to clear',
    ]))
]), 'footer')
urwid.connect_signal(ui_input_filter, 'postchange', onFilter)
ui_esc_filtered = urwid.Text('')
ui_message = urwid.Text('')


def seperator(): return ('pack', urwid.Text([('seperator', u'\uE0B1'), ' ']))


ui_footer = urwid.AttrMap(urwid.Columns([
    customButtonFooter('Enter', ' run', runCommand),
    seperator(),
    customButtonFooter('/', ' filter', startFilter),
    seperator(),
    customButtonFooter('a', 'dd  ', lambda x: startEditOrClone('a')),
    seperator(),
    customButtonFooter('e', 'dit ', lambda x: startEditOrClone('e')),
    seperator(),
    customButtonFooter('c', 'lone', lambda x: startEditOrClone('c')),
    seperator(),
    customButtonFooter('d', 'elete', deleteCommand),
    seperator(),
    customButtonFooter('q', 'uit ', exit),
    ui_esc_filtered,
    ('pack', ui_message),
]), 'footer')

ui_main_frame = urwid.Frame(menu(app_state['commands']))
ui_body = urwid.Frame(
    ui_main_frame,
    header=ui_header,
    footer=ui_footer,
)


if urwid.web_display.is_web_request():
    Screen = urwid.web_display.Screen
else:
    Screen = urwid.raw_display.Screen
screen = Screen()
# loop = urwid.MainLoop(ui_body, palette, screen, unhandled_input=unhandledInput)
loop = urwid.MainLoop(ui_body, palette, screen, unhandled_input=unhandledInput, pop_ups=True)


def run(enable_filter=False):
    loop.screen.set_terminal_properties(colors=256)
    if enable_filter:
        startFilter()
    loop.run()


if '__main__' == __name__ or urwid.web_display.is_web_request():
    run()

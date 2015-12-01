#!/usr/bin/env python3

import numpy
import urwid

palette = [
    ('bold', 'default,bold', 'default'),
    ('point', 'black', 'white'),
    ('bg_point', 'light gray', 'black'),
    ]

class PointInputBox(urwid.LineBox):
    def __init__(self, callback=None):
        if callback is None:
            self.callback = lambda p:None
        else:
            self.callback = callback

        self._setup_GUI()

    def _setup_GUI(self):
        self.xcontainer = urwid.Pile([urwid.Text('Channel\n', align='center')])
        self.ycontainer = urwid.Pile([urwid.Text('Energy\n', align='center')])
        xfill = urwid.AttrMap(urwid.Filler(self.xcontainer, valign='top'),
                              'bg_point')
        yfill = urwid.AttrMap(urwid.Filler(self.ycontainer, valign='top'),
                              'bg_point')
        self.columns = urwid.Columns([xfill, yfill],
                                     min_width=5, dividechars=1, focus_column=0)
        super().__init__(self.columns, title='Points')

        self.focus_y = 0

    def AddPoint(self):
        self.xcontainer.widget_list.append(urwid.Edit('--'))
        self.ycontainer.widget_list.append(urwid.Edit('--'))

    @property
    def point_list(self):
        output = []
        for (xentry,_), (yentry,_) in zip(self.xcontainer.contents[1:],
                                  self.ycontainer.contents[1:]):
            try:
                output.append((float(xentry.edit_text), float(yentry.edit_text)))
            except ValueError:
                pass
        return output

    @property
    def focus_x(self):
        return self.columns.focus_position

    @focus_x.setter
    def focus_x(self, val):
        self.columns.focus_position = max(0, min(val,1))

    @property
    def focus_y(self):
        return self.xcontainer.focus_position - 1

    @focus_y.setter
    def focus_y(self, val):
        val = max(0, min(val, self.nrows))
        if val==self.nrows:
            self.AddPoint()
        self.xcontainer.focus_position = val+1
        self.ycontainer.focus_position = val+1

    @property
    def nrows(self):
        return len(self.xcontainer.contents)-1

    def tab_stop(self):
        if self.focus_x==1:
            self.focus_x = 0
            self.focus_y += 1
        else:
            self.focus_x += 1

    def keypress(self, size, key):
        if key not in ['left', 'right', 'up', 'down','tab','enter']:
            super().keypress(size, key)
            self.callback(self.point_list)
            return

        if key=='down':
            self.focus_y += 1
        elif key=='up':
            self.focus_y -= 1
        elif key=='left':
            self.focus_x -= 1
        elif key=='right':
            self.focus_x += 1
        elif key=='tab':
            self.tab_stop()


class MainWindow(urwid.Columns):
    def __init__(self):
        self.result = urwid.Text('Energy = ')
        div = urwid.Divider()
        self.exit_button = urwid.Button('Exit', on_press=exit_program)
        exit_fill = urwid.Padding(self.exit_button, align='right', width=8)

        pile = urwid.Pile([self.result, div, exit_fill])
        fill = urwid.Filler(pile)

        self.points = PointInputBox(self.RefitPoints)
        super().__init__([fill,(40,self.points)])

    def RefitPoints(self, points):
        if len(points)<2:
            return

        xvals = [x for x,y in points]
        yvals = [y for x,y in points]
        result = numpy.polyfit(xvals, yvals, 1)

        terms = []
        for i,val in enumerate(result):
            power = len(result) - i - 1
            if power == 0:
                format_str = '{val:.3f}'
            elif power == 1:
                format_str = '{val:.3f}*Chan'
            else:
                format_str = '{val:.3f}*Chan^{power}'
            terms.append(format_str.format(val=val,power=power))

        res = 'Energy = ' + ' + '.join(terms)

        self.result.set_text(res)

def exit_program(button):
    raise urwid.ExitMainLoop()

window = MainWindow()
loop = urwid.MainLoop(window, palette)
loop.run()

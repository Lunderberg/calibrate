#!/usr/bin/env python3

from ensure_venv import ensure_venv
ensure_venv('requirements.txt', system_site_packages=True)

import urwid
import sys

from polynomial import Polynomial

palette = [
    ('bold', 'default,bold', 'default'),
    ('active', 'white', 'dark gray', '', 'white', 'g20'),
    ('inactive', 'white', 'black'),
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
        self.xentries = []
        self.yentries = []

        xfill = urwid.Filler(self.xcontainer, valign='top')
        yfill = urwid.Filler(self.ycontainer, valign='top')
        self.columns = urwid.Columns([xfill, yfill],
                                     min_width=5, dividechars=1, focus_column=0)
        super().__init__(self.columns, title='Points')

        self.focus_y = 0

    def AddPoint(self, xvalue=None, yvalue=None):
        xedit = urwid.Edit(edit_text = '' if xvalue is None else str(xvalue))
        xmap = urwid.AttrMap(xedit,'active')
        self.xcontainer.widget_list.append(xmap)
        self.xentries.append(xedit)

        yedit = urwid.Edit(edit_text = '' if yvalue is None else str(yvalue))
        ymap = urwid.AttrMap(yedit,'active')
        self.ycontainer.widget_list.append(ymap)
        self.yentries.append(yedit)

    @property
    def point_list(self):
        output = []
        for (xentry,yentry) in zip(self.xentries, self.yentries):
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
        if key not in ['left', 'right', 'up', 'down', 'tab', 'enter']:
            super().keypress(size, key)
            self.callback()
            return

        if key=='down':
            self.focus_y += 1
        elif key=='up':
            if self.focus_y == 0:
                return key
            self.focus_y -= 1
        elif key=='left':
            if self.focus_x == 0:
                return key
            self.focus_x -= 1
        elif key=='right':
            if self.focus_x == 1:
                return key
            self.focus_x += 1
        elif key=='tab':
            self.tab_stop()



class Conversion(urwid.LineBox):
    def __init__(self, title='', callback=None):
        self.callback = callback

        self.input_box = urwid.Edit()
        urwid.connect_signal(self.input_box, 'change', self._on_change)

        input_map = urwid.AttrMap(self.input_box, 'active')
        self.output_box = urwid.Text('')
        pile = urwid.Pile([input_map, self.output_box])
        super().__init__(pile, title=title)

    def _on_change(self, widget, new_text):
        if self.callback is not None:
            self.callback(self, new_text)

    @property
    def text_input(self):
        return self.input_box.edit_text

    @text_input.setter
    def text_input(self, val):
        self.input_box.set_edit_text(val)

    @property
    def text_output(self):
        return self.output_box.text

    @text_output.setter
    def text_output(self, val):
        self.output_box.set_text(val)



class MainWindow(urwid.AttrMap):
    def __init__(self):
        self.fit = None
        self._setup_GUI()

    def _setup_GUI(self):
        self.degree_box = urwid.Edit(('inactive','Degree = '),'1')
        urwid.connect_signal(self.degree_box, 'change', self.RefitPoints)
        degree_map = urwid.AttrMap(self.degree_box, 'active')
        degree_padded = urwid.Padding(degree_map, align='left', width=15)

        self.polyfit_box = urwid.Text('Energy = ')
        self.chi2_box = urwid.Text('Chi^2 = ')
        div = urwid.Divider()

        self.conversion = Conversion(title='Chan -> Energy',
                                     callback=self.OnConversionChange)
        self.back_conversion = Conversion(title='Energy -> Chan',
                                          callback=self.OnReverseConversionChange)
        conversion_columns = urwid.Columns([(20,self.conversion),
                                            (20,self.back_conversion)])

        exit_button = urwid.Button('Exit', on_press=exit_program)
        exit_map = urwid.AttrMap(exit_button, 'active')
        exit_fill = urwid.Padding(exit_map, align='left', width=8)

        pile = urwid.Pile([degree_padded, div,
                           self.polyfit_box, self.chi2_box, div,
                           conversion_columns, div,
                           exit_fill])
        fill = urwid.Filler(pile)

        self.point_box = PointInputBox(self.RefitPoints)
        columns = urwid.Columns([(40,self.point_box),fill])
        super().__init__(columns, 'inactive')

    def degree(self, degree_text=None):
        if degree_text is None:
            degree_text = self.degree_box.edit_text

        try:
            output = int(degree_text)
        except ValueError:
            return None

        if output<0:
            return None
        else:
            return output

    def RefitPoints(self, widget=None, degree_text=None):
        points = self.point_box.point_list
        degree = self.degree(degree_text)

        if degree is None or len(points)<degree+1:
            self.fit = None
            self.polyfit_box.set_text('Energy = ')
            self.chi2_box.set_text('Chi^2 = ')
        else:
            xvals = [x for x,y in points]
            yvals = [y for x,y in points]
            self.fit = Polynomial.FromFit(xvals, yvals, degree,
                                          xvar='Chan', yvar='Energy')
            self.polyfit_box.set_text(str(self.fit))
            chi2 = self.fit.chi2(xvals,yvals)
            self.chi2_box.set_text('Chi^2 = {:.03f}'.format(chi2))

        self.OnConversionChange(self.conversion)
        self.OnConversionChange(self.back_conversion)

    def OnConversionChange(self, widget, new_text = None):
        if new_text is None:
            new_text = widget.text_input

        try:
            x = float(new_text)
        except ValueError:
            x = None

        if self.fit is None or x is None:
            widget.text_output = ''
        else:
            widget.text_output = str(self.fit(x))

    def OnReverseConversionChange(self, widget, new_text = None):
        if new_text is None:
            new_text = widget.text_input

        try:
            y = float(new_text)
        except ValueError:
            y = None

        if self.fit is None or y is None:
            widget.text_output = ''
        else:
            roots = self.fit.reverse(y)
            real_roots = [r.real for r in roots if abs(r.imag)<1e-6]
            if real_roots:
                output = ', '.join(str(r) for r in real_roots)
            else:
                output = 'No real roots'
            widget.text_output = output


def exit_program(button):
    raise urwid.ExitMainLoop()

window = MainWindow()
loop = urwid.MainLoop(window, palette)
loop.screen.set_terminal_properties(colors=256)
loop.run()

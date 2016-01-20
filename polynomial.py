import numpy

class Polynomial:
    def __init__(self, coefficients, xvar='x', yvar='y'):
        self.coeff = list(coefficients)
        self.xvar = xvar
        self.yvar = yvar

    @classmethod
    def FromFit(cls, xvals, yvals, degree=1, **kwargs):
        coeff = numpy.polyfit(xvals, yvals, degree)
        return cls(coeff, **kwargs)

    def __call__(self, x):
        output = 0.0
        for val in self.coeff:
            output *= x
            output += val
        return output

    def reverse(self, y):
        copy = self.coeff[:]
        copy[-1] -= y
        return numpy.roots(copy)

    def chi2(self, xvals, yvals):
        output = 0.0
        for x,y in zip(xvals, yvals):
            yfit = self(x)
            output += (y-yfit)*(y-yfit)
        return output

    def __str__(self):
        terms = []
        for i,val in enumerate(self.coeff):
            power = len(self.coeff) - i - 1
            if power == 0:
                format_str = '{val:.3f}'
            elif power == 1:
                format_str = '{val:.6f}*{{xvar}}'
            else:
                format_str = '{val:.6f}*{{xvar}}^{power}'
            terms.append(format_str.format(val=val,power=power))

        output = '{yvar} = ' + ' + '.join(terms)
        return output.format(xvar=self.xvar, yvar=self.yvar)

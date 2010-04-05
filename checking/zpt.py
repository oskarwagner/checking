import re
from zope.interface import implements
from repoze.bfg.security import has_permission
from chameleon.core import types
from chameleon.zpt.expressions import ExpressionTranslator
from chameleon.zpt.interfaces import IExpressionTranslator


class PermissionTranslator(ExpressionTranslator):
    implements(IExpressionTranslator)

    symbol = '_has_permission'
    re_name = re.compile(r'^[a-z_-]+$')

    def translate(self, string, escape=None):
        if not string:
            return None
        string = string.strip()

        if self.re_name.match(string) is None:
            raise SyntaxError(string)

        value = types.value("%s('%s', context, request)" % (self.symbol, string))
        value.symbol_mapping[self.symbol] = has_permission
        return value


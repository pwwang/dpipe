import pytest

from pipda import register_verb, register_func
from pipda.function import *
from pipda.context import Context, ContextEval
from pipda.symbolic import ReferenceAttr, Symbolic

from . import f, identity, identity2, iden, iden2, add2


def test_function_repr(identity):
    fun = Function(identity, (), {})
    assert (
        repr(fun) == "Function(func=identity.<locals>.<lambda>, dataarg=True)"
    )
    assert str(fun) == 'identity()'
    fun = Function(
        ReferenceAttr(ReferenceAttr(Symbolic("f"), "x"), "mean"),
        (1,),
        {"a": 2},
        dataarg=False,
    )
    assert (
        repr(fun)
        == "Function(func=ReferenceAttr(parent=ReferenceAttr(parent=<Symbolic:f>, ref='x'), ref='mean'), dataarg=False)"
    )
    assert str(fun) == 'x.mean(1, a=2)'


def test_function_eval(f, identity):
    out = Function(identity, (), {})._pipda_eval(1, context=Context.EVAL.value)
    assert out == 1
    out = Function(f.__len__, (), {}, False)._pipda_eval(
        [1, 2], context=Context.EVAL.value
    )
    assert out == 2


def test_eval_with_different_context():
    class MyContext(ContextEval):
        args = ContextEval()
        kwargs = ContextEval()

    @register_verb(context=MyContext())
    def add_all(data, a, b):
        return data + a + b

    out = 1 >> add_all(2, 3)
    assert out == 6


def test_extra_contexts(f, identity2):
    iden2 = register_verb(extra_contexts={"y": Context.SELECT})(identity2)
    out = iden2(1, f[2])
    assert out == (1, 2)

    iden3 = register_verb(extra_contexts={"z": Context.SELECT})(identity2)
    with pytest.raises(KeyError):
        iden3(1, 2)


def test_context_retrieval(f, iden, iden2):
    @register_func(None, context=Context.UNSET)
    def get_context(dat, _context=None):
        return _context

    out = iden2([1, 2], get_context(f[1]))
    assert isinstance(out[1], ContextEval)


def test_eval_with_pending_context(f, iden2):
    @register_func(context=Context.PENDING)
    def iden(data, arg):
        return arg

    out = 1 >> iden2(iden(f[2]))
    assert out == (1, 2)


def test_expr_func(f):
    """Test that we can use expr as a function"""
    class Data:
        def __init__(self, data) -> None:
            self.data = data

        @property
        def attr(self):
            return self

        def get_data(self):
            return self.data

    fun = Function(f.attr.get_data, (), {}, False)
    out = fun._pipda_eval(
        f, context=Context.EVAL.value
    )._pipda_eval(
        Data(3), context=Context.EVAL.value
    )
    assert isinstance(out, int)
    assert out == 3

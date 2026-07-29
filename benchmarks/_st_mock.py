"""Inject lightweight fakes for streamlit and optional heavy packages."""
import sys
import types

_INJECTED = []


def _cache_data(*args, **kwargs):
    def wrap(fn):
        if not hasattr(fn, "clear"):
            fn.clear = lambda: None
        return fn
    return wrap(args[0]) if args and callable(args[0]) else wrap


def _noop(*a, **k):
    pass


def _make_st():
    st = types.ModuleType("streamlit")
    st.cache_data = _cache_data
    st.cache_resource = _cache_data
    st.session_state = {}
    for n in ("error","warning","info","success","write","title","header",
              "subheader","text","markdown","spinner","sidebar","columns",
              "button","selectbox","file_uploader","plotly_chart","metric"):
        setattr(st, n, _noop)
    return st


def _make_pdfplumber():
    m = types.ModuleType("pdfplumber")
    class _PDF:
        pages = []
        def __enter__(self): return self
        def __exit__(self, *_): return False
    m.open = lambda *a, **k: _PDF()
    return m


def _make_pytesseract():
    m = types.ModuleType("pytesseract")
    m.image_to_string = lambda *a, **k: ""
    return m


def _make_reportlab():
    mods = {}
    def sub(name):
        m = types.ModuleType(name); mods[name] = m; return m
    rl  = sub("reportlab")
    pl  = sub("reportlab.platypus")
    lib = sub("reportlab.lib")
    sty = sub("reportlab.lib.styles")
    class _Doc:
        def __init__(self, *a, **k): pass
        def build(self, *a, **k): pass
    class _Para:
        def __init__(self, t, s=None, *a, **k): pass
    pl.SimpleDocTemplate = _Doc
    pl.Paragraph = _Para
    class _SS(dict):
        def __getitem__(self, k): return k
    sty.getSampleStyleSheet = _SS
    return mods


def install_streamlit_mock():
    for name, factory in [("streamlit", _make_st),
                           ("pdfplumber", _make_pdfplumber),
                           ("pytesseract", _make_pytesseract)]:
        if name not in sys.modules:
            sys.modules[name] = factory()
            _INJECTED.append(name)
    for name, mod in _make_reportlab().items():
        if name not in sys.modules:
            sys.modules[name] = mod
            _INJECTED.append(name)


def remove_streamlit_mock():
    for k in list(_INJECTED):
        sys.modules.pop(k, None)
    _INJECTED.clear()

import importlib.util
import sys
import pathlib

root = pathlib.Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(root))

base = root / 'StockSageAI' / 'pages'

# Prepare a minimal session_state to avoid attribute errors when importing pages
try:
    import streamlit as st
    if not hasattr(st, 'session_state'):
        # ensure session_state exists
        st.session_state.update({'user': {'username': 'test'}})
    else:
        if 'user' not in st.session_state:
            st.session_state['user'] = {'username': 'test'}
except Exception:
    # running outside of Streamlit runtime; pages may still import but warn
    pass
print('Scanning pages in', base)

results = {}
for p in sorted(base.glob('*.py')):
    name = p.stem
    print('-> Loading', name)
    try:
        spec = importlib.util.spec_from_file_location(f'tests.pages.{name}', str(p))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        results[name] = 'ok'
    except Exception as e:
        results[name] = f'ERROR: {e.__class__.__name__}: {str(e)[:200]}'

print('\nSummary:')
for k, v in results.items():
    print(f'{k}: {v}')

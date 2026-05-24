import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from StockSageAI.app import main
except Exception as e:
    import traceback
    tb = traceback.format_exc()
    # Write full traceback to a log file to aid debugging in deployment environments
    try:
        with open(os.path.join(ROOT_DIR, 'import_error.log'), 'w', encoding='utf-8') as fh:
            fh.write('ImportError while importing StockSageAI.app\n')
            fh.write('Working dir: ' + ROOT_DIR + '\n')
            fh.write(tb)
    except Exception:
        # Best-effort; ignore file write errors
        pass
    raise ImportError(
        f"Unable to import StockSageAI.app. Full traceback written to import_error.log (if writable). Original error: {e}"
    ) from e


if __name__ == "__main__":
    main()

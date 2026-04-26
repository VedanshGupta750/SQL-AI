import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import glob
import tempfile
import io


SAFE_BUILTINS = {
    "True": True,
    "False": False,
    "None": None,
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "frozenset": frozenset,
    "int": int,
    "isinstance": isinstance,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "print": print,
    "range": range,
    "reversed": reversed,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
}

BLOCKED_PATTERNS = [
    "__import__", "__subclasses__", "__bases__", "__globals__",
    "__builtins__", "__code__", "__reduce__",
    "subprocess", "shutil", "socket", "requests", "http",
    "eval(", "exec(", "compile(",
    "getattr(", "setattr(", "delattr(",
    "breakpoint",
]


class VizService:
    @staticmethod
    def _validate_script(script: str) -> None:
        script_lower = script.lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern.lower() in script_lower:
                raise SecurityError(f"Blocked pattern detected: '{pattern}'")

    @staticmethod
    def _make_safe_open(allowed_dir: str):
        def safe_open(path, mode="r", **kwargs):
            resolved = os.path.realpath(path)
            allowed = os.path.realpath(allowed_dir)
            if not resolved.startswith(allowed):
                raise PermissionError(f"Access denied: can only read files in the temp directory")
            if mode not in ("r", "rb"):
                raise PermissionError(f"Access denied: only read mode is allowed")
            return open(path, mode, **kwargs)
        return safe_open

    @staticmethod
    def safe_exec_globals(temp_dir: str):
        safe_builtins = dict(SAFE_BUILTINS)
        safe_builtins["open"] = VizService._make_safe_open(temp_dir)

        return {
            "__builtins__": safe_builtins,
            "pd": pd,
            "np": np,
            "plt": plt,
            "sns": sns,
        }

    @staticmethod
    def generate_visualizations(df: pd.DataFrame, query: str, ai_service, temp_dir: str) -> list:
        matplotlib.use('Agg')
        plt.switch_backend('Agg')

        csv_path = os.path.join(temp_dir, "data.csv")
        df.to_csv(csv_path, index=False)

        sample_rows = df.head(3).to_string(index=False)
        dtypes_info = df.dtypes.to_string()

        viz_prompt = f"""
        Visualize this data. Context: {query}.
        Input CSV: '{csv_path}'.
        Columns: {df.columns.tolist()}.
        Data Types:
        {dtypes_info}
        Sample Data (first 3 rows):
        {sample_rows}

        Output: Save charts to '{temp_dir}' using plt.savefig().

        STRICT RULES:
        - NO plt.show(). NO exit(). NO quit().
        - NO import statements. All libraries (pd, np, plt, sns) are pre-loaded.
        - Do NOT use infer_datetime_format parameter in pd.to_datetime().
        - For date parsing, use pd.to_datetime(col, format='mixed') or pd.to_datetime(col, format='ISO8601'). NEVER guess a manual format string.
        - Always use plt.tight_layout() before saving.
        - Use plt.figure() for each chart.
        - When using seaborn plots with a 'palette', you MUST also assign the 'hue' parameter (e.g. `hue=x` or `hue=y`) and set `legend=False` to avoid FutureWarnings.
        """
        py_script = ai_service.gemini_call(viz_prompt, "Generate Viz Code")

        max_retries = 1
        attempts = 0
        graphs = []

        while attempts <= max_retries:
            try:
                plt.close('all')

                VizService._validate_script(py_script)

                exec_globals = VizService.safe_exec_globals(temp_dir)
                exec(py_script, exec_globals)
                for img in glob.glob(os.path.join(temp_dir, "*.png")):
                    with open(img, "rb") as f:
                        graphs.append(base64.b64encode(f.read()).decode('utf-8'))
                break
            except SecurityError as e:
                print(f"[BLOCKED] Security violation in AI-generated code: {e}")
                break
            except Exception as e:
                attempts += 1
                if attempts <= max_retries:
                    print(f"[RETRY] Viz error on attempt {attempts}: {e}. Retrying with corrected script...")
                    for stale_img in glob.glob(os.path.join(temp_dir, "*.png")):
                        try:
                            os.remove(stale_img)
                        except OSError:
                            pass
                    fix_prompt = f"""
                    The following Python visualization script failed with an error.
                    Fix the script and return ONLY the corrected Python code. No markdown.

                    Original Script:
                    {py_script}

                    Error:
                    {e}

                    STRICT RULES:
                    - Save output to '{temp_dir}' using plt.savefig().
                    - NO plt.show(). NO exit(). NO quit().
                    - NO import statements. All libraries (pd, np, plt, sns) are pre-loaded.
                    - Do NOT use infer_datetime_format parameter in pd.to_datetime().
                    - For date parsing, use pd.to_datetime(col, format='mixed') or pd.to_datetime(col, format='ISO8601'). NEVER guess a manual format string.
                    - When using seaborn plots with a 'palette', you MUST also assign the 'hue' parameter (e.g. `hue=x` or `hue=y`) and set `legend=False` to avoid FutureWarnings.
                    - Input CSV is at '{csv_path}' with columns: {df.columns.tolist()}.
                    - Sample data:
                    {sample_rows}
                    """
                    py_script = ai_service.gemini_call(fix_prompt, "Fix Viz Code")
                    if not py_script:
                        print("[ERROR] AI failed to generate corrected viz script.")
                        break
                else:
                    print(f"[ERROR] Viz generation failed after {max_retries + 1} attempts: {e}")
            finally:
                plt.close('all')

        return graphs


class SecurityError(Exception):
    pass

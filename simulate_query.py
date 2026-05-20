"""
Simulation script: mirrors the app's question→code→execute→retry flow.
Run with: python3 simulate_query.py
Requires ANTHROPIC_API_KEY in environment or .env file.
"""
import os, io, sys, re, traceback
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import anthropic
from dotenv import load_dotenv

load_dotenv()

CSV = "spotify_2014_2020_dataset.csv"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
QUESTION = "What are the ten newest songs by release date?"

df = pd.read_csv(CSV)


def build_system_prompt(df, filename):
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()
    return f"""You are DataChat, an expert data analyst assistant. The user has uploaded a CSV file called "{filename}".

Here is the dataset schema:
{info_str}

First 3 rows:
{df.head(3).to_string()}

Summary statistics:
{df.describe(include='all').to_string()}

You help users explore, analyze, and visualize their data.

When a question requires computation or visualization:
1. Write clean Python code using pandas (df is already loaded) and matplotlib
2. Wrap ALL executable code in a single ```python code block
3. For charts, call plt.savefig('chart.png', bbox_inches='tight', dpi=150) then plt.close() — do NOT call plt.show()
4. After the code block, explain the results in plain English
5. Keep explanations concise and insight-focused

When a question can be answered directly without code, just answer it clearly.

Rules:
- The dataframe variable is named `df` and is already loaded — never re-read a CSV file
- Always use matplotlib for charts, never other libraries
- Always call plt.close() after saving a chart
- Print any tabular results using print(result.to_string()) so they appear in output
"""


def extract_code(text):
    pattern = r"```python\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0].strip() if matches else None


def execute_code(code, df):
    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()
    local_vars = {"__builtins__": __builtins__, "df": df.copy(), "pd": pd, "plt": plt}
    error = None
    try:
        exec(code, local_vars)
    except Exception:
        error = traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        plt.close("all")
    return mystdout.getvalue(), error


client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

print("=" * 60)
print(f"QUESTION: {QUESTION}")
print("=" * 60)

# --- First call ---
api_messages = [{"role": "user", "content": QUESTION}]
response = client.messages.create(
    model=MODEL,
    max_tokens=MAX_TOKENS,
    system=build_system_prompt(df, CSV),
    messages=api_messages,
)
full_reply = response.content[0].text
print("\n--- Claude's first reply ---")
print(full_reply)

code = extract_code(full_reply)
if not code:
    print("\n(No code block — direct answer, done.)")
    sys.exit(0)

print("\n--- Extracted code ---")
print(code)

output, error = execute_code(code, df)

if not error:
    print("\n--- Output (first attempt) ---")
    print(output)
    sys.exit(0)

# --- Error path ---
print("\n!!! EXECUTION ERROR !!!")
print(error)
print("\n--- Actual column names and dtypes ---")
print(df.dtypes.to_string())
print("\n--- Release_Date sample values ---")
print(df["Release_Date"].dropna().head(10).tolist())

# --- Self-correction retry (mirrors app.py logic) ---
print("\n--- Sending error back to Claude for self-correction ---")
col_info = "\n".join(f"  {col}: {dtype}" for col, dtype in df.dtypes.items())
correction_prompt = (
    f"The code you generated raised an error during execution:\n\n"
    f"```\n{error}\n```\n\n"
    f"The actual column names and dtypes in the dataframe are:\n"
    f"{col_info}\n\n"
    f"Please rewrite the code to fix this error."
)
retry_messages = api_messages + [
    {"role": "assistant", "content": full_reply},
    {"role": "user", "content": correction_prompt},
]
retry_response = client.messages.create(
    model=MODEL,
    max_tokens=MAX_TOKENS,
    system=build_system_prompt(df, CSV),
    messages=retry_messages,
)
retry_reply = retry_response.content[0].text
print("\n--- Claude's corrected reply ---")
print(retry_reply)

retry_code = extract_code(retry_reply)
if retry_code:
    print("\n--- Executing corrected code ---")
    output2, error2 = execute_code(retry_code, df)
    if error2:
        print("\n!!! STILL FAILING AFTER RETRY !!!")
        print(error2)
    else:
        print("\n--- Output (after self-correction) ---")
        print(output2)
else:
    print("\n(No code block in retry reply)")

import os
import io
import sys
import uuid
import tempfile
import traceback
import re

import streamlit as st
import pandas as pd
import anthropic
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

# ── Constants ──────────────────────────────────────────────────────────────────
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
FREE_QUERY_LIMIT = 10  # queries allowed before asking for a personal API key

DEMO_CSV = "sales_data_sample.csv"
DEMO_QUESTIONS = [
    "What are the top 10 customers by revenue?",
    "Show a bar chart of sales by product line",
    "Which country has the highest total sales?",
    "What is the monthly sales trend over time?",
    "Are there any unusually large or small orders?",
]

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataChat",
    page_icon="📊",
    layout="wide"
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fb; }
    .stChatMessage { border-radius: 12px; }
    .block-container { padding-top: 2rem; }
    h1 { color: #1F4E79; }
    .subtitle { color: #555; font-size: 1.05rem; margin-top: -10px; margin-bottom: 20px; }

    /* Code output blocks */
    .stCode code, pre code { color: #1a1a1a !important; }

    /* Chat message text — assistant and user bubbles */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] ol,
    [data-testid="stChatMessage"] ul,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] td,
    [data-testid="stChatMessage"] th { color: #1a1a1a !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 DataChat")
st.markdown(
    '<p class="subtitle">Ask questions about the sample sales dataset in plain English — no code required.</p>',
    unsafe_allow_html=True
)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    # Auto-load sample dataset on first run
    try:
        for enc in ["utf-8", "latin-1", "windows-1252", "utf-8-sig"]:
            try:
                st.session_state.df = pd.read_csv(DEMO_CSV, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            st.session_state.df = None
    except Exception:
        st.session_state.df = None
if "df_name" not in st.session_state:
    st.session_state.df_name = DEMO_CSV
def get_env_key():
    """Get API key from Streamlit Secrets (cloud) or .env (local)."""
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY", "")

if "api_key" not in st.session_state:
    st.session_state.api_key = get_env_key()
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False
# Temp dir persisted across reruns so chart images survive
if "chart_dir" not in st.session_state:
    st.session_state.chart_dir = tempfile.mkdtemp()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Setup")

    # Never pre-fill the input — avoids exposing the key visually on load
    if st.session_state.api_key:
        st.success("✅ API key loaded", icon="🔑")
    api_key_input = st.text_input(
        "Anthropic API Key",
        value="",
        type="password",
        placeholder="sk-ant-..." if not st.session_state.api_key else "Key already set — paste to update",
        help="Get your key at console.anthropic.com — or set ANTHROPIC_API_KEY in .env",
        key="api_key_field",
    )
    if api_key_input:
        st.session_state.api_key = api_key_input

    # Show query counter when running on shared/env key (no personal key entered)
    using_shared_key = bool(get_env_key()) and not api_key_input
    if using_shared_key:
        remaining = max(0, FREE_QUERY_LIMIT - st.session_state.query_count)
        st.caption(f"Free queries remaining: **{remaining} / {FREE_QUERY_LIMIT}**")
        st.progress(st.session_state.query_count / FREE_QUERY_LIMIT)

    st.divider()

    # Data preview — always the sample dataset
    st.header("🔍 Data Preview")
    if st.session_state.df is not None:
        st.dataframe(st.session_state.df.head(5), use_container_width=True)
        st.caption(f"Columns: {', '.join(st.session_state.df.columns.tolist())}")
        st.download_button(
            label="⬇️ Download Sample CSV",
            data=st.session_state.df.to_csv(index=False).encode("utf-8"),
            file_name=DEMO_CSV,
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("**💡 Try asking:**")
    for q in DEMO_QUESTIONS:
        st.markdown(f"- *{q}*")

    st.divider()
    st.markdown("**🔒 Data & Privacy**")
    st.caption(
        "This demo uses a public sample sales dataset. "
        "Your questions are sent to Anthropic&#39;s Claude API to generate "
        "analysis code — only the dataset schema and a few sample rows "
        "are included for context. No personal data is collected or stored. "
        "By using DataChat you agree to "
        "[Anthropic's usage policies](https://www.anthropic.com/legal/usage-policy)."
    )


# ── Helper: build system prompt ────────────────────────────────────────────────
def build_system_prompt(df: pd.DataFrame, filename: str) -> str:
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


# ── Helper: execute generated code ────────────────────────────────────────────
def execute_code(code: str, df: pd.DataFrame, chart_dir: str):
    """Safely execute LLM-generated pandas/matplotlib code."""
    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()

    # Unique chart path per execution — prevents history images overwriting each other
    chart_filename = f"chart_{uuid.uuid4().hex[:8]}.png"
    chart_path = os.path.join(chart_dir, chart_filename)

    # Rewrite any chart.png references to the unique temp path
    code = code.replace("'chart.png'", f"'{chart_path}'")
    code = code.replace('"chart.png"', f'"{chart_path}"')

    local_vars = {
        "__builtins__": __builtins__,
        "df": df.copy(),
        "pd": pd,
        "plt": plt,
    }
    saved_chart = None
    error = None

    try:
        exec(code, local_vars)  # noqa: S102
        if os.path.exists(chart_path):
            saved_chart = chart_path
    except Exception:
        error = traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        plt.close("all")  # always clean up figures to prevent memory leaks

    output = mystdout.getvalue()
    return output, saved_chart, error


# ── Helper: extract code blocks ────────────────────────────────────────────────
def extract_code(text: str) -> str | None:
    """Extract the first python code block from markdown."""
    pattern = r"```python\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0].strip() if matches else None


# ── Main chat area ─────────────────────────────────────────────────────────────
if st.session_state.df is None:
    st.warning("⚠️ Could not load sample dataset. Make sure sales_data_sample.csv is in the project root.")
elif not st.session_state.api_key:
    st.warning("👈 Enter your Anthropic API key in the sidebar to start chatting.")
else:
    # Free query cap — only enforced when using the shared env key (not a personal key)
    using_shared_key = bool(get_env_key()) and not api_key_input
    if using_shared_key and st.session_state.query_count >= FREE_QUERY_LIMIT:
        st.warning(
            f"⚠️ You've used all {FREE_QUERY_LIMIT} free queries. "
            "Add your own Anthropic API key in the sidebar to keep going — "
            "it's free to sign up at [console.anthropic.com](https://console.anthropic.com)."
        )
        st.stop()
    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("chart") and os.path.exists(msg["chart"]):
                st.image(msg["chart"])
            if msg.get("output"):
                st.code(msg["output"], language="")

    # Chat input
    user_input = st.chat_input("Ask anything about your data...")

    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build message history for API (text content only — no chart/output metadata)
        api_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        # Call Claude with streaming
        with st.chat_message("assistant"):
            reply_placeholder = st.empty()
            full_reply = ""

            try:
                # Key resolution order:
                # 1. Key typed in sidebar by user
                # 2. Streamlit Secrets (cloud) or .env (local)
                resolved_key = st.session_state.api_key or get_env_key()
                if not resolved_key:
                    st.error(
                        "❌ No API key found. "
                        "Enter your Anthropic API key in the sidebar, "
                        "or add it to Streamlit Secrets (Settings → Secrets → ANTHROPIC_API_KEY)."
                    )
                    st.stop()
                client = anthropic.Anthropic(api_key=resolved_key)

                with client.messages.stream(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=build_system_prompt(st.session_state.df, st.session_state.df_name),
                    messages=api_messages,
                ) as stream:
                    for text_chunk in stream.text_stream:
                        full_reply += text_chunk
                        reply_placeholder.markdown(full_reply + "▌")

                reply_placeholder.markdown(full_reply)

                # Increment usage counter (for shared-key rate limiting)
                st.session_state.query_count += 1

                # Execute any code blocks in the response
                code = extract_code(full_reply)
                chart_img = None
                code_output = None

                if code:
                    code_output, chart_path, error = execute_code(
                        code, st.session_state.df, st.session_state.chart_dir
                    )
                    if error:
                        st.error(f"Code execution error:\n```\n{error}\n```")
                    else:
                        if code_output:
                            st.code(code_output, language="")
                        if chart_path:
                            st.image(chart_path)
                            chart_img = chart_path

                # Save assistant turn to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_reply,
                    "chart": chart_img,
                    "output": code_output,
                })

            except anthropic.AuthenticationError:
                st.error("❌ Invalid API key. Please check your Anthropic API key.")
            except anthropic.RateLimitError:
                st.error("⏳ Rate limit hit. Please wait a moment and try again.")
            except anthropic.APIConnectionError:
                st.error("🌐 Connection error. Check your internet and try again.")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
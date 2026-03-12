import streamlit as st
import pandas as pd
import anthropic
import io
import sys
import traceback
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 DataChat")
st.markdown('<p class="subtitle">Upload a CSV and ask questions about your data in plain English.</p>', unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "df_name" not in st.session_state:
    st.session_state.df_name = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Setup")

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your key at console.anthropic.com"
    )

    st.divider()
    st.header("📁 Upload Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.df = df
            st.session_state.df_name = uploaded_file.name
            st.session_state.messages = []  # reset chat on new upload
            st.success(f"✅ Loaded {len(df):,} rows × {len(df.columns)} columns")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    if st.session_state.df is not None:
        st.divider()
        st.header("🔍 Data Preview")
        st.dataframe(st.session_state.df.head(5), use_container_width=True)
        st.caption(f"Columns: {', '.join(st.session_state.df.columns.tolist())}")

    st.divider()
    st.markdown("**Example questions:**")
    st.markdown("- What are the top 5 values by sales?")
    st.markdown("- Show a bar chart of revenue by category")
    st.markdown("- Are there any missing values?")
    st.markdown("- What's the correlation between columns?")
    st.markdown("- Summarize the key trends in this data")

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
3. For charts, use plt.savefig('chart.png', bbox_inches='tight', dpi=150) at the end — do NOT call plt.show()
4. After the code block, explain the results in plain English
5. Keep explanations concise and insight-focused

When a question can be answered directly without code, just answer it clearly.

The dataframe variable is named `df` and is already loaded — never re-read a CSV file.
Always use matplotlib for charts, never other libraries.
"""

# ── Helper: execute generated code ────────────────────────────────────────────
def execute_code(code: str, df: pd.DataFrame):
    """Safely execute LLM-generated pandas/matplotlib code."""
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()

    local_vars = {"df": df.copy(), "pd": pd, "plt": plt}
    chart_path = None
    error = None

    try:
        exec(code, local_vars)
        # Check if a chart was saved
        if "chart.png" in code:
            chart_path = "chart.png"
    except Exception:
        error = traceback.format_exc()
    finally:
        sys.stdout = old_stdout

    output = mystdout.getvalue()
    return output, chart_path, error

# ── Helper: extract code blocks ────────────────────────────────────────────────
def extract_code(text: str):
    """Extract python code from markdown code blocks."""
    import re
    pattern = r"```python\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0].strip() if matches else None

# ── Main chat area ─────────────────────────────────────────────────────────────
if st.session_state.df is None:
    st.info("👈 Upload a CSV file in the sidebar to get started.")
elif not api_key:
    st.warning("👈 Enter your Anthropic API key in the sidebar to start chatting.")
else:
    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("chart"):
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

        # Build message history for API
        api_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        # Call Claude
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2000,
                        system=build_system_prompt(st.session_state.df, st.session_state.df_name),
                        messages=api_messages
                    )
                    reply = response.content[0].text

                    # Display text response
                    st.markdown(reply)

                    # Try to execute any code in the response
                    code = extract_code(reply)
                    chart_img = None
                    code_output = None

                    if code:
                        code_output, chart_path, error = execute_code(code, st.session_state.df)
                        if error:
                            st.error(f"Code execution error:\n{error}")
                        else:
                            if code_output:
                                st.code(code_output, language="")
                            if chart_path:
                                try:
                                    st.image(chart_path)
                                    chart_img = chart_path
                                except:
                                    pass

                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": reply,
                        "chart": chart_img,
                        "output": code_output
                    })

                except anthropic.AuthenticationError:
                    st.error("Invalid API key. Please check your Anthropic API key.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

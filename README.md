# 📊 DataChat

An AI-powered data analysis agent built with [Claude](https://anthropic.com) and [Streamlit](https://streamlit.io). Upload any CSV file and ask questions about your data in plain English — DataChat writes and executes Python code to deliver insights and visualizations in real time.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.32%2B-red)
![Anthropic](https://img.shields.io/badge/claude-sonnet--4-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

- **Natural language querying** — ask questions like *"What are the top 10 customers by revenue?"* without writing any code
- **Agentic code execution** — Claude writes Python/pandas code, executes it live, and returns results
- **Automatic visualizations** — ask for charts and get matplotlib plots rendered inline
- **Streaming responses** — answers stream token-by-token, no waiting for the full response
- **Multi-turn conversation** — follow-up questions retain full context from earlier in the chat
- **Persistent chart history** — all charts from the session stay visible as you scroll
- **Any CSV** — works on sales data, survey results, financial records, marketing data, and more

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/datachat.git
cd datachat
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your API key

Option A — create a `.env` file:
```bash
cp .env.example .env
# edit .env and paste your ANTHROPIC_API_KEY
```

Option B — paste it directly in the app sidebar (no file needed).

Get a key at [console.anthropic.com](https://console.anthropic.com).

### 4. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Try It With Sample Data

A `sample_data.csv` is included — it contains 6 months of regional product sales. Try these questions to see DataChat in action:

- *"What is total revenue by product?"*
- *"Show a bar chart of monthly revenue for each region"*
- *"Which region has higher average customer ratings?"*
- *"Are there any months with unusually high returns?"*
- *"What's the correlation between units sold and revenue?"*

---

## 🏗️ How It Works

```
User question
     │
     ▼
Claude (claude-sonnet-4)
  ├── Receives: question + full chat history + dataset schema + sample rows
  ├── Decides: answer directly OR write Python code
  └── Returns: explanation + optional ```python code block
     │
     ▼
Code executor (exec in sandboxed local scope)
  ├── Runs pandas operations on the loaded DataFrame
  ├── Saves any matplotlib charts to a unique temp file
  └── Captures stdout (print statements)
     │
     ▼
Streamlit renders: text + code output + chart image
```

---

## 📁 Project Structure

```
datachat/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── sample_data.csv     # Example dataset to try
├── .env.example        # API key template
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

| Variable | Where | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | `.env` or sidebar | Your Anthropic API key |
| `MODEL` | `app.py` line 13 | Claude model to use (default: `claude-sonnet-4-20250514`) |
| `MAX_TOKENS` | `app.py` line 14 | Max tokens per response (default: `4096`) |

---

## 🔒 Security Notes

- API keys entered in the sidebar are stored only in Streamlit session state (browser memory) — never written to disk
- Generated code runs in an isolated local scope with only `df`, `pd`, and `plt` available
- Do not deploy with sensitive data without adding authentication

---

## 📦 Deploying to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Add `ANTHROPIC_API_KEY` in the app's **Secrets** settings (Settings → Secrets)
4. Deploy — users can still paste their own key in the sidebar if you prefer

---

## 🤝 Contributing

Pull requests welcome! Some ideas for contributions:

- Support for Excel (`.xlsx`) files
- Export conversation as PDF or markdown
- More chart types (plotly, seaborn)
- Data cleaning suggestions
- Auto-generated data summary on upload

---

## 📄 License

MIT — see [LICENSE](LICENSE).

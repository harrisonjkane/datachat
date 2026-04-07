# 📊 DataChat — Agentic CSV Analysis Assistant

An AI-powered data analysis agent built with Claude (Anthropic) and Streamlit. Upload any CSV file and ask questions about your data in plain English — DataChat writes and executes Python code to deliver insights and visualizations in real time.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)
![Claude](https://img.shields.io/badge/Claude-Sonnet-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---


---

## ✨ Features

- **Natural language querying** — ask questions like "What are the top 10 customers by revenue?" without writing any code
- **Agentic code execution** — Claude writes Python/pandas code, executes it live, and returns results
- **Automatic visualizations** — ask for charts and get matplotlib plots rendered inline
- **Multi-turn conversation** — follow-up questions retain context from earlier in the chat
- **Any CSV** — works on sales data, survey results, financial records, marketing data, and more

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Claude Sonnet (Anthropic API) |
| Frontend | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualization | Matplotlib |
| Language | Python 3.10+ |

---

## 📦 Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/datachat.git
cd datachat

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

You'll need an **Anthropic API key** — get one free at [console.anthropic.com](https://console.anthropic.com).

---

## ☁️ Deploy to Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set `app.py` as the main file
5. Deploy — your app gets a public URL instantly

---

## 💡 Example Questions to Try

- *"Summarize the key trends in this dataset"*
- *"Show a bar chart of sales by category"*
- *"Which rows have missing values?"*
- *"What's the correlation between price and quantity?"*
- *"Who are the top 5 customers by total spend?"*
- *"Create a time series plot of revenue by month"*

---

## 🧠 How It Works

```
User uploads CSV → Pandas loads data → Schema + sample rows sent to Claude
         ↓
User asks question → Full conversation history sent to Claude API
         ↓
Claude generates Python/pandas code → App executes code in sandbox
         ↓
Results + charts rendered in Streamlit UI → User asks follow-up
```

Claude receives the dataset schema, column types, summary statistics, and sample rows as context on every turn — enabling it to write accurate, data-aware code without ever hallucinating column names.

---

## 📁 Project Structure

```
datachat/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 👤 Author

Built by **[Your Name]** — Senior Data Scientist specializing in ML deployment, media mix modeling, and agentic AI systems.

- 🔗 [LinkedIn](YOUR_LINKEDIN)
- 💼 [Portfolio](YOUR_PORTFOLIO)

---

## 📄 License

MIT License — free to use, modify, and distribute.

# 🕵️‍♂️ CVsAgent: The Ultimate CV Intelligence Tool 🚀

> **Extract insights, rate candidates, and simplify hiring with the power of AI!** ✨

**CVsAgent** (formerly ResumeGPT) is a next-gen tool that transforms PDF CVs into structured, actionable data. Powered by LangChain and OpenAI, it helps HR professionals and recruiters extract 23+ data points, rate candidates, and export everything to Excel – all in seconds! ⏱️

---

## 🌟 Features

| 🧠 **Intelligent Extraction** | 📊 **Structured Output** | ⚡ **Batch Processing** |
|-----------------------------|------------------------|---------------------|
| Uses advanced LLMs (`gpt-5-mini` etc.) to understand context. | Exports strictly typed data to Excel. | Process hundreds of CVs in parallel. |

| 🎨 **Beautiful UI** | 🐳 **Docker Ready** | 🔍 **Dynamic Analysis** |
|-------------------|-------------------|---------------------|
| Rich CLI with spinners & logging. | Run anywhere with zero setup. | **Target Job Matching** & **Custom Fields**. |

---

## 🛠️ Installation

### Option 1: Docker (Recommended 🐳)
Run the entire pipeline in a container without worrying about Python versions.

```bash
# Build and Run
docker-compose up --build
```

### Option 2: Local Setup 💻

1. **Clone & Install**
   ```bash
   git clone https://github.com/your-repo/CVsAgent.git
   cd CVsAgent
   pip install -r requirements.txt
   ```

2. **Setup Environment**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=sk-your-api-key-here
   ```

---

## 🚀 Usage

Place your PDF CVs in the `CVs` directory.

### Quick Start
```bash
python main.py
```

### 🎯 Dynamic & Advanced Usage

**1. Custom Fields Extraction**:
Extract additional specific info like Visa Status or Driver's License.
```bash
python main.py --add_fields "VisaStatus" "DriverLicense"
```

**2. Target Job Matching**:
Rate candidates against a specific job description (text or file).
```bash
python main.py --job_description_file "job_descriptions/job_description.txt"
# OR
python main.py --job_description "Seeking a Senior Python Developer with AWS experience..."
```

**3. Full Customization**:
```bash
python main.py --cv_dir "My_CVs" --output_dir "Results" --model "gpt-4o" --add_fields "GitHubStars"
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--cv_dir` | `CVs` | Folder containing input PDFs. |
| `--output_dir` | `Output` | Folder for the Excel report. |
| `--model` | `gpt-5-mini-2025-08-07` | OpenAI model to use. |
| `--add_fields` | `None` | List of custom fields to extract. |
| `--job_description_file` | `None` | Path to job description text file. |
| `--job_description` | `None` | Job description string. |

---

## 📊 Extracted Data

The tool extracts **23+ default features** plus any custom fields you define:

- **🎓 Education**: University, Major, GPA, Graduation Date (Bachelor, Masters, PhD).
- **💼 Experience**: Companies, Titles, Top Responsibilities, Dates.
- **🛠️ Skills**: Top 5 Technical & Soft Skills.
- **📜 Certifications & Awards**: Top 5 Achievements.
- **🌍 Personal**: Nationality, Residence, Employment Status, Portfolio URLs.
- **📈 Analysis**: Top 5 Suitable Positions, Candidate Rating (0-10).
- **🎯 Job Match**: Suitability (True/False) and Reasoning (if job provided).

---

## 🤝 Contributing
Feel free to open issues or submit PRs! Let's make hiring smarter together. 💡

---
*Built with ❤️ using [LangChain](https://langchain.com) and [Rich](https://github.com/Textualize/rich)*
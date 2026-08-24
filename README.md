# AgroPulse AI

**Offline AI-powered poultry disease decision support and Smart Farm Operations platform for African farmers.**

Built for the **Africa Deep Tech Challenge 2026 — Laptop LLM track**.

## What It Is

AgroPulse AI is an offline-first platform designed to help poultry farmers, agricultural extension officers, and veterinary field workers make better day-to-day decisions. It combines poultry disease decision support with practical farm management tools so that important information can still be accessed when internet connectivity is limited or unavailable.

The system runs its AI components locally on the user's laptop. Farm records are stored locally, veterinary knowledge is retrieved locally, and the application does not depend on cloud APIs during normal operation.

## The Problem

Many poultry farmers in Nigeria and across sub-Saharan Africa have limited access to timely veterinary support. When disease symptoms appear, delays in identifying possible problems or taking appropriate action can lead to serious flock losses.

At the same time, many farming areas have unreliable internet connectivity. This makes cloud-dependent AI applications difficult to use consistently. AgroPulse AI was built around this constraint: the core system should remain useful even without an internet connection.

## The Solution

AgroPulse AI provides a local disease decision-support pipeline together with farm management and operational intelligence.

The platform can:

- Perform rule-based symptom triage against a curated poultry veterinary knowledge base
- Retrieve relevant veterinary information using a local RAG pipeline
- Generate structured advisory responses using a local Phi-3 Mini model
- Track livestock, mortality, feed, medication, vaccination, and egg production
- Calculate farm performance and risk indicators
- Provide smart recommendations for daily farm operations
- Detect potential mortality and disease trends
- Provide offline voice input and text-to-speech
- Generate PDF veterinary reports
- Provide demo cases and one-click sample farm data for quick evaluation

## Key Features

### Offline AI Disease Decision Support

- Weighted symptom matching
- Coverage of 12 poultry diseases
- Veterinary knowledge retrieval using ChromaDB
- Local LLM advisory responses
- Safety-oriented language that avoids claiming a confirmed diagnosis

### Farm Intelligence

- Farm Risk Score
- Biosecurity intelligence
- Outbreak detection
- Mortality trend analysis
- Disease consultation history
- Farm health timeline

### Smart Farm Operations

- Farm Performance Score
- Smart recommendations
- Feed planning
- Mortality intelligence
- Egg production intelligence
- Vaccination calendar
- Daily farm summaries
- "What Changed" tracking between visits

### Farm Management

- Livestock records
- Mortality records
- Feed inventory
- Medication records
- Vaccination records
- Egg production records

### Additional Tools

- Offline voice input using Whisper
- Offline text-to-speech
- Interactive Plotly analytics
- PDF report export
- Demo Mode
- One-click sample farm data

## Architecture

```text
Farmer input (text or voice)
            |
            v
     Triage Engine
     (rule-based)
            |
            v
   RAG Knowledge Retrieval
   (ChromaDB + embeddings)
            |
            v
      Local LLM
     (Phi-3 Mini)
            |
            v
 Structured advisory response
 + risk intelligence
 + recommendations
            |
            v
      Local SQLite
   farm and consultation data
```

## Technology Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | Phi-3 Mini via Ollama |
| Model format | GGUF |
| Runtime requirement | llama.cpp |
| Embeddings | sentence-transformers |
| Vector store | ChromaDB |
| Database | SQLite |
| Voice input | OpenAI Whisper |
| Voice output | pyttsx3 |
| Analytics | Plotly |
| Reports | ReportLab |

### Model and ADTC Runtime Compliance

The submission uses a **GGUF-format Phi-3 Mini model**. The ADTC submission metadata specifies `llama.cpp` as the required model runtime and `GGUF` as the model format.

The application uses Ollama locally to manage and serve the model during development and demonstration. The repository does not commit the model weights; the submission's `download_model.sh` is responsible for obtaining the model into the `model/` directory.

The local model was verified to expose a GGUF weight file through the installed Ollama model configuration.

## Offline-First Design

AgroPulse AI is designed to operate without internet access after the required models and dependencies have been installed.

- The LLM runs locally
- Embeddings are cached and used locally
- ChromaDB is local
- SQLite stores farm data locally
- Whisper runs locally after its model has been downloaded
- Text-to-speech runs locally
- No cloud AI API is required during normal application use

For evaluation, all external downloads should be completed before the offline inference test begins.

## Installation

### Prerequisites

- Python 3.10 or later
- Ollama installed for the development/demo setup
- Sufficient RAM for the local model and application

### Setup

Clone the repository:

```bash
git clone https://github.com/PurposeOluwadahunsi/agropulse-ai-adtc-2026.git
cd agropulse-ai-adtc-2026
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

On Windows:

```powershell
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Download the model using the submission script:

```bash
bash download_model.sh
```

For the local Ollama development/demo setup:

```bash
ollama pull phi3:mini
```

### Build the Knowledge Base

```bash
python knowledge/ingest.py
```

## Running the Application

```bash
python -m streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Demo Mode

AgroPulse AI includes a Demo Mode containing pre-written poultry disease scenarios. These allow a user or evaluator to explore the disease-support pipeline without manually entering a case.

Example scenarios include:

- Newcastle Disease
- Gumboro Disease
- Coccidiosis
- Fowl Cholera
- Chronic Respiratory Disease
- Egg Drop Syndrome

## Sample Farm Data

When the database is empty, the application provides a **Load Sample Farm Data** option.

This loads realistic sample records for:

- Livestock
- Mortality
- Feed
- Vaccination
- Egg production

This allows the farm-management and Smart Operations features to be demonstrated quickly.

## Running Fully Offline

After all required models and dependencies have been downloaded and prepared:

1. Disconnect the laptop from the internet.
2. Make sure the local model runtime is available.
3. Launch the application:

```bash
python -m streamlit run app.py
```

4. Test disease decision support, farm management, analytics, voice features, and report generation without an internet connection.

## Responsible AI

AgroPulse AI is a **decision-support tool**, not a replacement for a veterinarian or laboratory diagnosis.

The system uses language such as "possible", "likely", and "consistent with" rather than presenting its output as a confirmed diagnosis. Veterinary professionals should be consulted before treatment decisions are made, especially for serious or potentially contagious diseases.

## Known Limitations

- Response time can be significant on CPU-only laptops with limited RAM.
- The current veterinary knowledge base covers 12 poultry diseases.
- Vague symptom descriptions may produce no strong match rather than forcing a prediction.
- Voice recognition accuracy can vary by language and recording quality.
- The system does not replace laboratory testing or an in-person veterinary examination.
- The "What Changed" comparison is session-based and resets when the application session is restarted.
- The AI insight panel is data-driven and templated rather than a separate generative model.

## Project Structure

```text
agropulse-ai-adtc-2026/
├── app.py
├── main.py
├── core/
├── db/
├── farm/
├── knowledge/
├── model/
├── ui/
├── voice/
├── metadata.json
├── download_model.sh
├── REPORT.md
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE
```

Model weights are intentionally excluded from Git. The evaluator should obtain the model through `download_model.sh`.

## Africa Deep Tech Challenge 2026

AgroPulse AI was developed for the **Africa Deep Tech Challenge 2026 Laptop LLM track**, with a focus on agriculture and the practical constraints faced by farmers who may have limited connectivity and computing resources.

The project combines local AI, retrieval-augmented generation, veterinary knowledge, and farm-management intelligence into one offline-first platform.

## License

This project is released under the **GNU General Public License v3.0**.

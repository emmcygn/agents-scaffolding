# Deployment Guide

## Streamlit Community Cloud

1. Push the repo to GitHub
2. Go to share.streamlit.io
3. Connect your GitHub repository
4. Set the main file to `streamlit_app.py`
5. Set Python version to 3.10+
6. Deploy

### Environment Variables
Set in Streamlit Cloud's "Advanced settings":
- `VOYAGE_API_KEY` (optional) — enables Voyage AI embeddings

### Limitations
- Streamlit Cloud has limited memory (~1GB)
- sentence-transformers models are large (~500MB each)
- For lightweight deployment, use `requirements-dashboard.txt` without embedding deps
- Pre-compute results locally and upload JSON to the dashboard

## Local Deployment

```bash
pip install -e ".[all]"
streamlit run src/scaffolder/dashboard/app.py
```

## Docker (optional)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[dashboard]"
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501"]
```

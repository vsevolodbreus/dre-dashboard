FROM python:3.10-slim-buster

ENV APP_DIR /app

WORKDIR ${APP_DIR}

COPY setup.py ${APP_DIR}
RUN pip install -e .

COPY DRE_Dashboard.py ${APP_DIR}
COPY .streamlit ${APP_DIR}/.streamlit
COPY utils ${APP_DIR}/utils
COPY users.yaml ${APP_DIR}
RUN pip install -e . --no-deps

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "DRE_Dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]

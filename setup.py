from setuptools import setup

REQUIRED_PACKAGES = [
    "duckdb==0.7.1",
    "ipython==8.11.0",
    "plotly==5.14.1",
    "pydantic==1.10.7",
    "streamlit==1.21",
    "streamlit-authenticator==0.2.1",
]

name = "dre_dashboard"
version = "0.1.0"
description = "DRE Insights Dashboard Streamlit POC"

setup(
    name=name,
    author="Vsevolod Breus",
    description=description,
    version=version,
    python_requires=">=3.10",
    include_package_data=True,
    install_requires=REQUIRED_PACKAGES,
    package_dir={"": "."},
)

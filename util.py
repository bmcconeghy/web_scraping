import attrs
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from datatypes import JobPosting


def get_html(url: str) -> BeautifulSoup:
    html = requests.get(url)
    soup = BeautifulSoup(html.text, "html.parser")
    return soup


def fetch_job_pages(links: list[str]) -> list[Tag]:
    """Fetch all content from job postings."""
    job_pages = []
    for link in links:
        job_page = get_html(link)
        # Skip the first generic posting
        if "DO YOU DREAM BIG" in job_page.h1.string.upper():
            continue
        job_pages.append(job_page)
    return job_pages


def structure_job_postings(job_pages: list[Tag]) -> list[JobPosting]:
    return [JobPosting.from_tag(job_page) for job_page in job_pages]


def job_postings_to_df(job_postings: list[JobPosting]) -> pd.DataFrame:
    return pd.DataFrame([attrs.asdict(jp) for jp in job_postings])


def plot_salary_ranges(
    df: pd.DataFrame,
    salary_to_benchmark_against: int,
    title="Salaries at AbCellera (Job Postings)",
):
    # Drop postings that lack salary data
    df = df.dropna()
    fig = px.box(
        df.sort_values("salary_low_end", ascending=True),
        x="role",
        y=["salary_low_end", "salary_high_end"],
        labels={"role": "Role", "value": "$"},
    )
    fig = fig.update_layout(title=dict(text=title, font=dict(size=30)))
    fig.add_hline(
        y=salary_to_benchmark_against,
        line_width=3,
        line_dash="dash",
        line_color="green",
    )
    fig.add_annotation(
        y=salary_to_benchmark_against,
        x=1,
        showarrow=True,
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        text=f"Salary to compare (${salary_to_benchmark_against:,})",
    )
    return fig

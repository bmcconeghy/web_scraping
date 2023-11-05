import attr
import json
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pathlib import Path

from datatypes import converter, JobPosting


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
    return pd.DataFrame([attr.asdict(jp) for jp in job_postings])


def plot_salary_ranges(df: pd.DataFrame, salary_to_benchmark_against: int):
    # Drop postings that lack salary data
    df = df.dropna()
    df["Low End"] = df["salary_range"].apply(lambda x: x[0])
    df["High End"] = df["salary_range"].apply(lambda x: x[1])
    fig = px.bar(
        df.sort_values("Low End", ascending=False),
        y="role",
        x=["High End", "Low End"],
        barmode="group",
        labels={"variable": "Salary", "role": "Role", "value": "$"},
    )
    fig = fig.update_layout(
        title=dict(text="Salaries at AbCellera (Job Postings)", font=dict(size=30))
    )
    fig.add_vline(
        x=salary_to_benchmark_against,
        line_width=3,
        line_dash="dash",
        line_color="green",
    )
    fig.add_annotation(
        x=salary_to_benchmark_against,
        y=1,
        yref="paper",
        showarrow=True,
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        text="Salary to compare",
    )
    return fig


if __name__ == "__main__":
    DEFAULT_SALARY = 50000
    user_salary = (
        input(
            f"Please enter salary to benchmark against (in integer format, e.g. 50000 for $50,000)\n(Press ENTER to set benchmark salary to ${DEFAULT_SALARY:,})\n"
        )
        or DEFAULT_SALARY
    )
    job_postings_path = Path("job_postings.json")
    if not job_postings_path.exists():
        url = "https://abcellera.com/careers-openings/"
        careers_page = get_html(url=url)
        links = careers_page.find_all("a")
        job_page_links = [
            f"{url}{link.get('href')}"
            for link in links
            if link.string and "View position" in link.string
        ]
        job_pages = fetch_job_pages(job_page_links)
        job_postings = structure_job_postings(job_pages)
        with open("job_postings.json", "w") as fh:
            json.dump(converter.unstructure(job_postings), fh)
    else:
        with open(job_postings_path) as fh:
            job_postings = converter.structure(json.load(fh), list[JobPosting])
    job_postings_df = job_postings_to_df(job_postings)
    fig = plot_salary_ranges(job_postings_df, salary_to_benchmark_against=user_salary)
    fig.write_html("abcellera_salaries.html")
    fig.write_image("abcellera_salaries.png", width=2000, height=1000)

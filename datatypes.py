import attrs
import re
from bs4.element import Tag
from cattr import Converter
from datetime import datetime


converter = Converter()
converter.register_unstructure_hook(datetime, lambda d: str(d))
converter.register_structure_hook(
    datetime, lambda d, _: datetime.strptime(d, "%Y-%m-%d").date()
)


@attrs.define
class JobPosting:
    role: str
    date: datetime
    id: str
    salary_low_end: int | None
    salary_high_end: int | None

    @classmethod
    def from_tag(cls, job_posting: Tag):
        article = job_posting.body.article.contents[1]

        salary_description = [
            s.text for s in job_posting.find_all("p") if "hiring range" in s.text
        ]

        salary_low_end, salary_high_end = (
            int(e.replace(",", ""))
            for e in re.findall(r"\d{2,3},\d{3}", next(iter(salary_description)))
        )

        return cls(
            role=job_posting.h1.string,
            date=datetime.strptime(
                article.find("span", class_="date").string, "%B %d, %Y"
            ).date(),
            id=article.find("span", class_="id").string.split(": ")[1],
            salary_low_end=salary_low_end,
            salary_high_end=salary_high_end,
        )

import attr
import re
from bs4.element import Tag
from cattr import Converter
from datetime import datetime
from typing import Optional


converter = Converter()
converter.register_unstructure_hook(datetime, lambda d: str(d))
converter.register_structure_hook(
    datetime, lambda d, _: datetime.strptime(d, "%Y-%m-%d").date()
)


@attr.define
class JobPosting:
    role: str
    date: datetime
    id: str
    salary_range: Optional[tuple[int, int]]

    @classmethod
    def from_tag(cls, job_posting: Tag):
        article = job_posting.body.article.contents[1]

        salary_range_tuple = None
        salary_description = [
            s.string
            for s in job_posting.find_all("p")
            if s.string and "hiring range" in s.string
        ]
        if salary_description:
            salary_range = re.findall(r"\$\d+,\d+", salary_description[0])
            # Convert salary range to tuple of integers representing low and high end of range
            salary_range_tuple = (
                tuple([int(re.sub("\$|\,", "", s)) for s in salary_range]) or None
            )

        return cls(
            role=job_posting.h1.string,
            date=datetime.strptime(
                article.find("span", class_="date").string, "%B %d, %Y"
            ).date(),
            id=article.find("span", class_="id").string.split(": ")[1],
            salary_range=salary_range_tuple,
        )

    @property
    def salary_low_end(self) -> Optional[int]:
        try:
            return self.salary_range[0]
        except Exception:
            return None

    @property
    def salary_high_end(self) -> Optional[int]:
        try:
            return self.salary_range[1]
        except Exception:
            return None

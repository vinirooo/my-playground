from __future__ import annotations

import re
import time

from typing import Iterator

import requests
from bs4 import BeautifulSoup
import pandas as pd
import OpenDartReader
import markdownify
import mdformat
import OpenDartReader

from langchain_core.documents import Document
from langchain_community.document_loaders.base import BaseLoader

import os
from dotenv import load_dotenv

# API 키 정보 로드
load_dotenv()

# Set the option to opt-in to the future behavior
pd.set_option("future.no_silent_downcasting", True)


class DartDocumentLoader(BaseLoader):
    """
    DartDocumentLoader는 OpenDartReader를 사용하여 Dart 보고서 문서를 로드하는 클래스입니다.

    Args:
        rcept_no (str): 보고서 고유번호.

    Attributes:
        rcept_no (str): 보고서 고유번호.
        dart (OpenDartReader): OpenDartReader 인스턴스.

    Methods:
        _get_webpage_content(url: str) -> BeautifulSoup:
            주어진 URL에서 웹페이지 내용을 가져와 BeautifulSoup 객체로 반환합니다.

        _modify_html_tags(soup: BeautifulSoup, selector: str, tag_name: str) -> BeautifulSoup:
            주어진 CSS 선택자를 사용하여 BeautifulSoup 객체의 태그 이름을 변경합니다.

        _webpage_to_markdown(url: str) -> str:
            주어진 URL의 웹페이지를 Markdown 형식으로 변환하여 반환합니다.

        lazy_load() -> Iterator[Document]:
            보고서 문서를 지연 로드하여 Document 객체를 생성하는 제너레이터 함수입니다.
    """

    def __init__(self, rcept_no: str):
        api_key = os.environ["OPENDART_API_KEY"]

        self.rcept_no = rcept_no
        self.dart = OpenDartReader(api_key=api_key)

    def _get_webpage_content(self, url):
        """
        주어진 URL에서 웹페이지 내용을 가져와 BeautifulSoup 객체로 반환합니다.

        Args:
            url (str): 웹페이지 URL.

        Returns:
            BeautifulSoup: 웹페이지 내용을 담고 있는 BeautifulSoup 객체.
        """
        response = requests.get(url)
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")
        return soup

    def _modify_html_tags(self, soup, selector, tag_name):
        """
        주어진 CSS 선택자를 사용하여 BeautifulSoup 객체의 태그 이름을 변경합니다.

        Args:
            soup (BeautifulSoup): BeautifulSoup 객체.
            selector (str): CSS 선택자.
            tag_name (str): 변경할 태그 이름.

        Returns:
            BeautifulSoup: 태그 이름이 변경된 BeautifulSoup 객체.
        """
        tags = soup.select(selector)
        for tag in tags:
            tag.name = tag_name
            tag.string = tag.get_text()

        return soup

    def _webpage_to_markdown(self, url):
        """
        주어진 URL의 웹페이지를 Markdown 형식으로 변환하여 반환합니다.

        Args:
            url (str): 웹페이지 URL.

        Returns:
            str: Markdown 형식의 웹페이지 내용.
        """
        soup = self._get_webpage_content(url)

        # CSS 셀렉터를 사용하여 태그 이름 변경
        soup = self._modify_html_tags(soup, "p.cover-title", "h1")
        soup = self._modify_html_tags(soup, "p.section-1", "h1")
        soup = self._modify_html_tags(soup, "p.section-2", "h2")

        markdown_content = markdownify.markdownify(str(soup.body), heading_style="ATX")
        markdown_content = mdformat.text(markdown_content)
        return markdown_content

    def _get_dart_docs_info(self):
        """
        Dart 보고서 문서의 정보를 가져오는 함수입니다.

        Returns:
            pd.DataFrame: 보고서 문서의 정보를 담고 있는 DataFrame 객체.
        """
        df_docs = self.dart.sub_docs(self.rcept_no)
        df_docs = df_docs[~df_docs["title"].str.startswith("【")]
        df_docs = df_docs[~df_docs["title"].str.contains("전문가")]
        df_docs["level"] = df_docs["title"].apply(
            lambda x: (1 if re.match(r"^[IVX]+\.", x) else 2 if x[0].isdigit() else 0)
        )
        df_docs.loc[df_docs["level"].isin([0, 1]), "section"] = df_docs["title"]
        df_docs["section"] = df_docs["section"].ffill()
        df_docs = df_docs[df_docs["level"] != 1]
        df_docs = df_docs[["section", "title", "url"]].reset_index(drop=True)
        df_docs["section"] = df_docs["section"].fillna(df_docs["title"])
        df_docs = df_docs.reset_index()

        return df_docs

    def _generate_document(self, doc_info) -> Document:
        """
        주어진 문서 정보를 기반으로 Document 객체를 생성합니다.

        Parameters:
            doc_info (dict): 문서 정보를 담고 있는 딕셔너리입니다.
                - url (str): 문서의 URL
                - title (str): 문서의 제목
                - section (str): 문서의 섹션

        Returns:
            Document: 생성된 Document 객체
        """
        index = doc_info["index"]
        url = doc_info["url"]
        title = doc_info["title"]
        section = doc_info["section"]

        markdown = self._webpage_to_markdown(url)
        metadata = {
            "index": index,
            "url": url,
            "title": title,
            "section": section,
        }

        return Document(
            page_content=markdown,
            metadata=metadata,
        )

    def lazy_load(self) -> Iterator[Document]:

        df_docs = self._get_dart_docs_info()

        for index, row in df_docs.iterrows():
            document = self._generate_document(row)
            time.sleep(0.1)
            yield document


def get_recent_report_no(stock_code):
    api_key = os.environ["OPENDART_API_KEY"]
    dart = OpenDartReader(api_key=api_key)
    df_reports = dart.list(stock_code, kind="A")
    df_reports = df_reports[df_reports["report_nm"].str.contains("사업보고서")]

    rcept_no = df_reports.iloc[0]["rcept_no"]

    return rcept_no

# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import re


def detect_domains(string_meta_analysis, string_value):
    """
    Detect if the given string is a url.
    :param string_meta_analysis: class:'StringMetaAnalysis'
    :param string_value: str
    :return: True if it is a parsable url.
    """
    from urllib.parse import urlparse
    isValidUrl = False
    # Check https://regex101.com/r/A326u1/5 for reference
    DOMAIN_FORMAT = re.compile(
        r"(?:^(\w{1,255}):(.{1,255})@|^)"  # http basic authentication [optional]
        r"(?:(?:(?=\S{0,253}(?:$|:))"  # check full domain length to be less than or equal to 253 (starting after http basic auth, stopping before port)
        r"((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"  # check for at least one subdomain (maximum length per subdomain: 63 characters), dashes in between allowed
        r"(?:[a-z0-9]{1,63})))"  # check for top level domain, no dashes allowed
        r"|localhost)"  # accept also "localhost" only
        r"(:\d{1,5})?",  # port [optional]
        re.IGNORECASE
    )
    SCHEME_FORMAT = re.compile(
        r"^(http|hxxp|ftp|fxp)s?$",  # scheme: http(s) or ftp(s)
        re.IGNORECASE
    )
    try:
        url = string_value
        url = url.strip()

        if not url:
            raise ValueError("No URL specified")

        if len(url) > 2048:
            raise ValueError("URL exceeds its maximum length of 2048 characters (given length={})".format(len(url)))

        parsed_url = urlparse(url)

        if not parsed_url.scheme:
            raise ValueError("No URL scheme specified")
        elif not re.fullmatch(SCHEME_FORMAT, parsed_url.scheme):
            raise ValueError(f"URL scheme must either be http(s) or ftp(s) (given scheme={parsed_url.scheme})")
        elif not parsed_url.netloc:
            raise ValueError("No URL domain specified")
        elif not re.fullmatch(DOMAIN_FORMAT, parsed_url.netloc):
            raise ValueError(f"URL domain malformed (domain={parsed_url.netloc})")

        string_meta_analysis.url_scheme = parsed_url.scheme
        string_meta_analysis.url_domain = parsed_url.netloc
        string_meta_analysis.url_path = parsed_url.path
        string_meta_analysis.url_params = parsed_url.params
        string_meta_analysis.url_query = parsed_url.query
        string_meta_analysis.url_fragment = parsed_url.fragment

        isValidUrl = True
    except ValueError as err:
        logging.debug(err)
        pass
    return isValidUrl

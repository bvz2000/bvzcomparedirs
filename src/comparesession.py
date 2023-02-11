#! /usr/bin/env python3

import os.path

from canonicaldir import CanonicalDir
from querydir import QueryDir

import comparefiles


class Session(object):
    """
    A class to manage a scan and compareFolders session.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 query_dir,
                 canonical_dir,
                 skip_sub_dir=False,
                 skip_hidden=False,
                 skip_zero_len=True,
                 incl_dir_regex=None,
                 excl_dir_regex=None,
                 incl_file_regex=None,
                 excl_file_regex=None,
                 report_frequency=1000):
        """
        Init.

        :param query_dir: The full query directory path.
        :param canonical_dir: The full canonical directory path.
        :param skip_sub_dir: If True, then no subdirectories will be included (only the top-level directory will be
               scanned). Defaults to False.
        :param skip_hidden: If True, then hidden files will be ignored in the scan. Defaults to False.
        :param skip_zero_len: If True, then files of zero length will be skipped. Defaults to True.
        :param incl_dir_regex: A regular expression to filter matching directories. Only those that match this regex
               will be INCLUDED. If None, no filtering will be done. Defaults to None.
        :param excl_dir_regex: A regular expression to filter matching directories. Those that match this regex
               will be EXCLUDED. If None, no filtering will be done. Defaults to None.
        :param incl_file_regex: A regular expression to filter matching files. Only those that match this regex
               will be INCLUDED. If None, no filtering will be done. Defaults to None.
        :param excl_file_regex: A regular expression to filter matching files. Those that match this regex
               will be EXCLUDED. If None, no filtering will be done. Defaults to None.
        :param report_frequency: How many files to scan before reporting back a count of scanned files to the calling
               function.
        """

        self.canonical_scan = None
        self.query_scan = None

        self.query_dir = query_dir
        self.canonical_dir = canonical_dir
        self.skip_sub_dir = skip_sub_dir
        self.skip_hidden = skip_hidden
        self.skip_zero_len = skip_zero_len
        self.incl_dir_regex = incl_dir_regex
        self.excl_dir_regex = excl_dir_regex
        self.incl_file_regex = incl_file_regex
        self.excl_file_regex = excl_file_regex
        self.report_frequency = report_frequency

        self.actual_matches = dict()
        self.unique = set()

        self.source_error_files = set()
        self.possible_match_error_files = set()

        self.pre_computed_checksum_count = 0

    # ------------------------------------------------------------------------------------------------------------------
    def do_query_scan(self):
        """
        Execute the query scan.

        :return: Nothing.
        """

        self.query_scan = QueryDir(scan_dir=self.query_dir)
        for file_count in self.query_scan.scan(skip_sub_dir=self.skip_sub_dir,
                                               skip_hidden=self.skip_hidden,
                                               skip_zero_len=self.skip_zero_len,
                                               incl_dir_regexes=self.incl_dir_regex,
                                               excl_dir_regexes=self.excl_dir_regex,
                                               incl_file_regexes=self.incl_file_regex,
                                               excl_file_regexes=self.excl_file_regex,
                                               report_frequency=self.report_frequency):
            yield file_count

    # ------------------------------------------------------------------------------------------------------------------
    def do_canonical_scan(self):
        """
        Execute the canonical scan.

        :return: Nothing.
        """

        self.canonical_scan = CanonicalDir(scan_dir=self.canonical_dir)
        for file_count in self.canonical_scan.scan(skip_sub_dir=self.skip_sub_dir,
                                                   skip_hidden=self.skip_hidden,
                                                   skip_zero_len=self.skip_zero_len,
                                                   incl_dir_regexes=self.incl_dir_regex,
                                                   excl_dir_regexes=self.excl_dir_regex,
                                                   incl_file_regexes=self.incl_file_regex,
                                                   excl_file_regexes=self.excl_file_regex,
                                                   report_frequency=self.report_frequency):
            yield file_count

    # ------------------------------------------------------------------------------------------------------------------
    def add_unique(self,
                   file_p):
        """
        Adds a file path to the list of unique files.

        :param file_p: The path to the unique file.

        :return: Nothing.
        """

        self.unique.add(file_p)

    # ------------------------------------------------------------------------------------------------------------------
    def do_compare(self,
                   name=False,
                   file_type=False,
                   parent=False,
                   rel_path=False,
                   ctime=False,
                   mtime=False,
                   skip_checksum=False):
        """
        Compare query scan to canonical scan. Any attributes that are set to True will be used as part of the
        comparison. Size is always used as a comparison attribute.

        :param name: If True, then also compare on name. Defaults to False.
        :param file_type: If True, then also compare on the file type. Defaults to False.
        :param parent: If True, then also compare on the parent directory name. Defaults to False.
        :param rel_path: If True, then also compare on teh relative path. Defaults to False.
        :param ctime: If True, then also compare on the creation time. Defaults to False.
        :param mtime: If True, then also compare on the modification time. Defaults to False.
        :param skip_checksum: If True, then only compare on the other metrics passed via the arguments. Requires that
               name is set to True or an assertion error is raised.

        :return: A dictionary of matching files where the key is the file in the query directory and the value is a list
                 of files in the canonical directory which match.
        """

        if skip_checksum:
            assert name is True

        count = 0

        for file_path, metadata in self.query_scan.files.items():

            count += 1
            yield count

            if name:
                name = metadata["name"]
            else:
                name = None

            if file_type:
                file_type = metadata["file_type"]
            else:
                file_type = None

            if parent:
                parent = metadata["parent"]
            else:
                parent = None

            if rel_path:
                rel_path = metadata["rel_path"]
            else:
                rel_path = None

            if ctime:
                ctime = metadata["ctime"]
            else:
                ctime = None

            if mtime:
                mtime = metadata["mtime"]
            else:
                mtime = None

            possible_matches = self.canonical_scan.get_intersection(size=metadata["size"],
                                                                    name=name,
                                                                    file_type=file_type,
                                                                    parent=parent,
                                                                    rel_path=rel_path,
                                                                    ctime=ctime,
                                                                    mtime=mtime)

            if len(possible_matches) == 0:
                self.add_unique(file_path)
                continue

            match = False
            for possible_match in possible_matches:

                if file_path == possible_match:  # Do not want to compare a file to itself - that is not a duplicate.
                    continue

                if skip_checksum:
                    match = True
                    # TODO: Break this out into a separate function (same as below)
                    try:
                        self.actual_matches[file_path].append(possible_match)
                    except KeyError:
                        self.actual_matches[file_path] = [possible_match]
                    continue

                possible_match_checksum = self.canonical_scan.get_checksum(possible_match)

                if possible_match_checksum is not None:
                    self.pre_computed_checksum_count += 1

                try:
                    checksum = comparefiles.compare(file_a_path=file_path,
                                                    file_b_path=possible_match,
                                                    file_b_checksum=possible_match_checksum,
                                                    single_pass=True)
                except AssertionError:
                    if not os.path.exists(file_path):
                        self.source_error_files.add(file_path)
                    if not os.path.exists(possible_match):
                        self.possible_match_error_files.add(possible_match)
                    continue

                if checksum:
                    # TODO: Break this out into a separate function (same as above)
                    match = True
                    self.canonical_scan.checksum[possible_match] = checksum
                    try:
                        self.actual_matches[file_path].append(possible_match)
                    except KeyError:
                        self.actual_matches[file_path] = [possible_match]

            if not match:
                self.add_unique(file_path)

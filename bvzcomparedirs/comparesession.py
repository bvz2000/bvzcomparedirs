#! /usr/bin/env python3

import os.path

from . canonicalfiles import CanonicalFiles
from . options import Options
from . queryfiles import QueryFiles

from . import comparefiles


class Session(object):
    """
    A class to manage a scan and compareFolders session.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 query_items,
                 canonical_dir,
                 skip_sub_dir=False,
                 skip_hidden=False,
                 skip_zero_len=True,
                 incl_dir_regexes=None,
                 excl_dir_regexes=None,
                 incl_file_regexes=None,
                 excl_file_regexes=None,
                 report_frequency=10):
        """
        :param query_items:
               A list of query directories or files (must include the full path). Also accepts: a set, a tuple, as well
               as a single string containing a single path.
        :param canonical_dir:
               The full canonical directory path.
        :param skip_sub_dir:
               If True, then no subdirectories will be included (only the top-level directory will be scanned). Defaults
               to False.
        :param skip_hidden:
               If True, then hidden files will be ignored in the scan. Defaults to False.
        :param skip_zero_len:
               If True, then files of zero length will be skipped. Defaults to True.
        :param incl_dir_regexes:
               A list of regular expressions to filter matching directories. Only those that match any of these regexes
               will be INCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex. If None,
               no filtering will be done. Defaults to None.
        :param excl_dir_regexes:
               A list of regular expressions to filter matching directories. Those that match any of these regexes will
               be EXCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex. If None, no
               filtering will be done. Defaults to None.
        :param incl_file_regexes:
               A list of regular expressions to filter matching files. Only those that match any of these regexes will
               be INCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex. If None, no
               filtering will be done. Defaults to None.
        :param excl_file_regexes:
               A list of regular expressions to filter matching files. Those that match any of these regexes will be
               EXCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex. If None, no
               filtering will be done. Defaults to None.
        :param report_frequency:
               How many files to scan before reporting back a count of scanned files to the calling function. Defaults
               to 10.
        """

        assert type(query_items) in [list, set, tuple, str]
        assert type(canonical_dir) is str
        assert type(skip_sub_dir) is bool
        assert type(skip_hidden) is bool
        assert type(skip_zero_len) is bool
        assert incl_dir_regexes is None or type(incl_dir_regexes) in [list, set, tuple, str]
        assert excl_dir_regexes is None or type(excl_dir_regexes) in [list, set, tuple, str]
        assert incl_file_regexes is None or type(incl_file_regexes) in [list, set, tuple, str]
        assert excl_file_regexes is None or type(excl_file_regexes) in [list, set, tuple, str]
        assert type(report_frequency) is int

        options = Options(skip_sub_dir=skip_sub_dir,
                          skip_hidden=skip_hidden,
                          skip_zero_len=skip_zero_len,
                          incl_dir_regexes=self._parameter_to_list(incl_dir_regexes),
                          excl_dir_regexes=self._parameter_to_list(excl_dir_regexes),
                          incl_file_regexes=self._parameter_to_list(incl_file_regexes),
                          excl_file_regexes=self._parameter_to_list(excl_file_regexes),
                          report_frequency=report_frequency)

        self.canonical_scan = CanonicalFiles(options)
        self.query_scan = QueryFiles(options)

        self.query_items = self._parameter_to_list(query_items)
        self.canonical_dir = canonical_dir

        self.actual_matches = dict()
        self.unique = set()
        self.skipped_self = set()

        self.source_error_files = set()
        self.possible_match_error_files = set()

        self.pre_computed_checksum_count = 0

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _parameter_to_list(param_value):
        """
        Given a parameter (param_value) checks to see if it is a list or None. If so, the parameter is returned
        unchanged. If it is not a list and is not None, param_value is embedded in a list and that list is returned.

        :param param_value:
               The parameter value that is to be turned into a list if it is not already a list.

        :return: The param_value embedded in a list. If param_value is already a list or is None, returns param_value
                 unchanged.
        """

        if param_value is None:
            return None

        if type(param_value) in [list, set, tuple]:
            return param_value

        return [param_value]

    # ------------------------------------------------------------------------------------------------------------------
    def do_query_scan(self):
        """
        Execute the query scan on the list of files or directories.

        :return: Nothing.
        """

        directories_p = list()
        files_p = list()

        for query_item in self.query_items:
            if os.path.isdir(query_item):
                directories_p.append(query_item)
            else:
                files_p.append(query_item)

        for item_count in self.query_scan.scan_directories(scan_dirs=directories_p):
            yield item_count

        for item_count in self.query_scan.scan_files(files_p=files_p):
            yield item_count

    # ------------------------------------------------------------------------------------------------------------------
    def do_canonical_scan(self):
        """
        Execute the canonical scan.

        :return: Nothing.
        """

        for file_count in self.canonical_scan.scan_directory(scan_dir=self.canonical_dir):
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
    def append_match(self,
                     file_p,
                     match_p):
        """
        Appends the possible match to the list of actual matches.

        :param file_p: The full path to the file in the canonical dir.
        :param match_p: The full path to the file in the query dir that matches the file_p.

        :return: Nothing.
        """

        try:
            self.actual_matches[file_p].append(match_p)
        except KeyError:
            self.actual_matches[file_p] = [match_p]

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

        for file_p, metadata in self.query_scan.files.items():

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
                self.add_unique(file_p)
                continue

            match = False
            skip = False
            for possible_match_p in possible_matches:

                if file_p == possible_match_p:  # Do not want to compare a file to itself - that is not a duplicate.
                    skip = True
                    self.skipped_self.add(file_p)
                    continue

                if skip_checksum:
                    match = True
                    self.append_match(file_p, possible_match_p)
                    continue

                possible_match_checksum = self.canonical_scan.get_checksum(possible_match_p)

                if possible_match_checksum is not None:
                    self.pre_computed_checksum_count += 1

                try:
                    checksum = comparefiles.compare(file_a_path=file_p,
                                                    file_b_path=possible_match_p,
                                                    file_b_checksum=possible_match_checksum,
                                                    single_pass=True)
                except AssertionError:
                    if not os.path.exists(file_p):
                        self.source_error_files.add(file_p)
                    if not os.path.exists(possible_match_p):
                        self.possible_match_error_files.add(possible_match_p)
                    continue

                if checksum:
                    match = True
                    self.canonical_scan.checksum[possible_match_p] = checksum
                    self.append_match(file_p, possible_match_p)

            if not match:
                if not skip or (skip and len(possible_matches) > 1):
                    self.add_unique(file_p)

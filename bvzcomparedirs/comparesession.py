#! /usr/bin/env python3

import os.path

from . canonicalfiles import CanonicalFiles
from bvzscanfilesystem.options import Options
from bvzscanfilesystem.scanfiles import ScanFiles

import bvzcomparefiles.comparefiles as comparefiles


class Session(object):
    """
    A class to manage a scan and compare session.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 query_items,
                 canonical_dir,
                 query_skip_sub_dir=False,
                 query_skip_hidden_files=False,
                 query_skip_hidden_dirs=False,
                 query_skip_zero_len=True,
                 query_incl_dir_regexes=None,
                 query_excl_dir_regexes=None,
                 query_incl_file_regexes=None,
                 query_excl_file_regexes=None,
                 canonical_skip_sub_dir=False,
                 canonical_skip_hidden_files=False,
                 canonical_skip_hidden_dirs=False,
                 canonical_skip_zero_len=True,
                 canonical_incl_dir_regexes=None,
                 canonical_excl_dir_regexes=None,
                 canonical_incl_file_regexes=None,
                 canonical_excl_file_regexes=None,
                 report_frequency=10):
        """
        :param query_items:
            A list of query directories or files (must include the full path). Also accepts: a set, a tuple, as well as
            a single string containing a single path.
        :param canonical_dir:
            The full canonical directory path.
        :param query_skip_sub_dir:
            If True, then no subdirectories of the query directory will be included (only the top-level directory will
            be scanned). Defaults to False.
        :param query_skip_hidden_files:
            If True, then hidden files in the query list will be ignored in the scan. Defaults to False.
        :param query_skip_hidden_dirs:
            If True, then hidden directories in the query list will be ignored in the scan. Defaults to False.
        :param query_skip_zero_len:
            If True, then files of zero length in the query list will be skipped. Defaults to True.
        :param query_incl_dir_regexes:
            A list of regular expressions to filter matching query subdirectories. Only those that match any of these
            regexes will be INCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex. If
            None, no filtering will be done. Defaults to None.
        :param query_excl_dir_regexes:
            A list of regular expressions to filter matching query subdirectories. Those that match any of these regexes
            will be EXCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex. If None, no
            filtering will be done. Defaults to None.
        :param query_incl_file_regexes:
            A list of regular expressions to filter matching files in the query list. Only those that match any of these
            regexes will be INCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex. If
            None, no filtering will be done. Defaults to None.
        :param query_excl_file_regexes:
            A list of regular expressions to filter matching files in the query list. Those that match any of these
            regexes will be EXCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex. If
            None, no filtering will be done. Defaults to None.
        :param canonical_skip_sub_dir:
            If True, then no subdirectories of the canonical directory will be included (only the top-level directory
            will be scanned). Defaults to False.
        :param canonical_skip_hidden_files:
            If True, then hidden files in the canonical directory will be ignored in the scan. Defaults to False.
        :param canonical_skip_hidden_dirs:
            If True, then hidden directories in the canonical directory will be ignored in the scan. Defaults to False.
        :param canonical_skip_zero_len:
            If True, then files of zero length in the canonical directory will be skipped. Defaults to True.
        :param canonical_incl_dir_regexes:
            A list of regular expressions to filter matching canonical subdirectories. Only those that match any of
            these regexes will be INCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex.
            If None, no filtering will be done. Defaults to None.
        :param canonical_excl_dir_regexes:
            A list of regular expressions to filter matching canonical subdirectories. Those that match any of these
            regexes will be EXCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex. If
            None, no filtering will be done. Defaults to None.
        :param canonical_incl_file_regexes:
            A list of regular expressions to filter matching files in the canonical directory. Only those that match any
            of these regexes will be INCLUDED. Also accepts a set, a tuple, as well as a string containing a single
            regex. If None, no filtering will be done. Defaults to None.
        :param canonical_excl_file_regexes:
            A list of regular expressions to filter matching files in the canonical directory. Those that match any of
            these regexes will be EXCLUDED. Also accepts a set, a tuple, as well as a string containing a single regex.
            If None, no filtering will be done. Defaults to None.
        :param report_frequency:
            How many files to scan before reporting back a count of scanned files to the calling function. Defaults to
            an integer value of 10.
        """

        assert type(query_items) in [list, set, tuple, str]
        assert type(canonical_dir) is str
        assert type(query_skip_sub_dir) is bool
        assert type(query_skip_hidden_files) is bool
        assert type(query_skip_hidden_dirs) is bool
        assert type(query_skip_zero_len) is bool
        assert query_incl_dir_regexes is None or type(query_incl_dir_regexes) in [list, set, tuple, str]
        assert query_excl_dir_regexes is None or type(query_excl_dir_regexes) in [list, set, tuple, str]
        assert query_incl_file_regexes is None or type(query_incl_file_regexes) in [list, set, tuple, str]
        assert query_excl_file_regexes is None or type(query_excl_file_regexes) in [list, set, tuple, str]
        assert type(canonical_skip_sub_dir) is bool
        assert type(canonical_skip_hidden_files) is bool
        assert type(canonical_skip_hidden_dirs) is bool
        assert type(canonical_skip_zero_len) is bool
        assert canonical_incl_dir_regexes is None or type(canonical_incl_dir_regexes) in [list, set, tuple, str]
        assert canonical_excl_dir_regexes is None or type(canonical_excl_dir_regexes) in [list, set, tuple, str]
        assert canonical_incl_file_regexes is None or type(canonical_incl_file_regexes) in [list, set, tuple, str]
        assert canonical_excl_file_regexes is None or type(canonical_excl_file_regexes) in [list, set, tuple, str]
        assert type(report_frequency) is int

        query_options = Options(skip_sub_dir=query_skip_sub_dir,
                                skip_hidden_files=query_skip_hidden_files,
                                skip_hidden_dirs=query_skip_hidden_dirs,
                                skip_zero_len=query_skip_zero_len,
                                incl_dir_regexes=self._parameter_to_list(query_incl_dir_regexes),
                                excl_dir_regexes=self._parameter_to_list(query_excl_dir_regexes),
                                incl_file_regexes=self._parameter_to_list(query_incl_file_regexes),
                                excl_file_regexes=self._parameter_to_list(query_excl_file_regexes),
                                report_frequency=report_frequency)

        canonical_options = Options(skip_sub_dir=canonical_skip_sub_dir,
                                    skip_hidden_files=canonical_skip_hidden_files,
                                    skip_hidden_dirs=canonical_skip_hidden_dirs,
                                    skip_zero_len=canonical_skip_zero_len,
                                    incl_dir_regexes=self._parameter_to_list(canonical_incl_dir_regexes),
                                    excl_dir_regexes=self._parameter_to_list(canonical_excl_dir_regexes),
                                    incl_file_regexes=self._parameter_to_list(canonical_incl_file_regexes),
                                    excl_file_regexes=self._parameter_to_list(canonical_excl_file_regexes),
                                    report_frequency=report_frequency)

        self.canonical_scan = CanonicalFiles(canonical_options)
        self.query_scan = ScanFiles(query_options)

        self.query_items = self._parameter_to_list(query_items)
        self.canonical_dir = canonical_dir

        self.actual_matches = dict()
        self.unique = set()
        self.skipped_self = set()

        self.source_error_files = set()
        self.possible_match_error_files = set()

        self.checksum = dict()
        self.pre_computed_checksum_count = 0

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _parameter_to_list(param_value):
        """
        Given a parameter (param_value) checks to see if it is a list, tuple, set, or None. If so, the parameter is
        returned unchanged. If it is not a list, tuple, set, or None, param_value is embedded in a list and that list is
        returned.

        :param param_value:
            The parameter value that is to be turned into a list if it is not already a list.

        :return:
            The param_value embedded in a list. If param_value is already a list or is None, returns param_value
            unchanged.
        """

        if param_value is None:
            return None

        if type(param_value) in [list, set, tuple]:
            return param_value

        return [param_value]

    # ------------------------------------------------------------------------------------------------------------------
    def _store_checksum_in_cache(self,
                                 file_p,
                                 checksum):
        """
        Caches the checksum for the given file path in a dictionary.

        :param file_p:
            The path to the file for which we want to store the checksum.
        :param checksum:
            The checksum value to be cached

        :return:
            Nothing.
        """

        assert type(file_p) is str
        assert type(checksum) is str

        self.checksum[file_p] = checksum

    # ------------------------------------------------------------------------------------------------------------------
    def _retrieve_checksum_from_cache(self,
                                      file_p):
        """
        Tries to load the checksum from the checksum dictionary. If there is no checksum available, returns None.

        :param file_p:
            The path to the file for which we want to get the stored checksum.

        :return:
            The checksum that was stored. If there was no stored checksum, returns None.
        """

        assert type(file_p) is str

        try:
            return self.checksum[file_p]
        except KeyError:
            return None

    # ------------------------------------------------------------------------------------------------------------------
    def do_query_scan(self):
        """
        Execute the query scan on the list of files and/or directories.

        :return:
            Nothing.
        """

        directories_p = list()
        files_p = list()

        for query_item in self.query_items:
            if os.path.isdir(query_item):
                directories_p.append(query_item)
            else:
                files_p.append(query_item)

        if directories_p:
            for file_count in self.query_scan.scan_directories(scan_dirs=directories_p):
                yield file_count

        # TODO: do a better job getting the root path
        if files_p:
            for file_count in self.query_scan.scan_files(files_p=files_p, root_p=os.path.sep):
                yield file_count

    # ------------------------------------------------------------------------------------------------------------------
    def do_canonical_scan(self):
        """
        Execute the canonical scan.

        :return:
            Nothing.
        """

        for file_count in self.canonical_scan.scan_directories(scan_dirs=[self.canonical_dir]):
            yield file_count

    # ------------------------------------------------------------------------------------------------------------------
    def _add_unique(self,
                    file_p):
        """
        Adds a file path to the list of unique files.

        :param file_p:
            The path to the unique file.

        :return:
            Nothing.
        """

        self.unique.add(file_p)

    # ------------------------------------------------------------------------------------------------------------------
    def _append_match(self,
                      canonical_p,
                      query_p):
        """
        Appends the possible match to the list of actual matches.

        :param canonical_p:
            The full path to the file in the canonical dir.
        :param query_p:
            The full path to the file in the query dir that matches the file_p.

        :return:
            Nothing.
        """

        try:
            self.actual_matches[canonical_p].append(query_p)
        except KeyError:
            self.actual_matches[canonical_p] = [query_p]

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

        :param name:
            If True, then also compare on name. Defaults to False.
        :param file_type:
            If True, then also compare on the file type. Defaults to False.
        :param parent:
            If True, then also compare on the parent directory name. Defaults to False.
        :param rel_path:
            If True, then also compare on teh relative path. Defaults to False.
        :param ctime:
            If True, then also compare on the creation time. Defaults to False.
        :param mtime:
            If True, then also compare on the modification time. Defaults to False.
        :param skip_checksum:
            If True, then only compare on the other metrics passed via the arguments. Requires that name is set to True
            or an assertion error is raised.

        :return:
            A dictionary of matching files where the key is the file in the query directory and the value is a list of
            files in the canonical directory which match.
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
                self._add_unique(file_p)
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
                    self._append_match(file_p, possible_match_p)
                    continue

                possible_match_checksum = self._retrieve_checksum_from_cache(possible_match_p)

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
                    self._store_checksum_in_cache(file_p=possible_match_p, checksum=checksum)
                    self._append_match(file_p, possible_match_p)

            if not match:
                if not skip or (skip and len(possible_matches) > 1):
                    self._add_unique(file_p)

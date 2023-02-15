#! /usr/bin/env python3

import errno
import os.path
import re


class ScanFiles(object):
    """
    A class to scan and store the attributes of every file in a single directory. Alternately has the ability to work
    with an arbitrary list of files instead of a scanned directory. This class should be subclassed and not used
    directly.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """
        """

        self.scan_dir = None

        self.dir_permission_err_files = set()
        self.dir_generic_err_files = set()
        self.file_permission_err_files = set()
        self.file_generic_err_files = set()
        self.file_not_found_err_files = set()

        self.initial_count = 0
        self.checked_count = 0
        self.skipped_links = 0
        self.error_count = 0
        self.skipped_zero_len = 0
        self.skipped_hidden = 0
        self.skipped_exclude = 0
        self.skipped_include = 0

    # ------------------------------------------------------------------------------------------------------------------
    def _get_metadata(self,
                      file_path):
        """
        Gets the metadata for the given file path.

        :param file_path:
               The path to the file to add

        :return: A dictionary of attributes.
        """

        attrs = dict()
        attrs["size"] = os.path.getsize(file_path)
        attrs["name"] = os.path.split(file_path)[1]
        attrs["file_type"] = os.path.splitext(attrs["name"])[1]
        attrs["parent"] = os.path.split(os.path.split(file_path)[0])[1]
        attrs["rel_path"] = os.path.relpath(file_path, self.scan_dir)
        attrs["ctime"] = os.stat(file_path).st_ctime  # Not always the creation time, but as close as it gets.
        attrs["mtime"] = os.stat(file_path).st_mtime

        return attrs

    # ------------------------------------------------------------------------------------------------------------------
    def _append_to_scan(self,
                        file_path,
                        metadata):
        """
        To be overridden in subclass

        :return: Nothing.
        """

        raise NotImplementedError

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

        if type(param_value) is list:
            return param_value

        return [param_value]

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _match_regex(regexes,
                     items):
        """
        Given a list of regex expressions and a list of items, returns True if any of the items match any of the regex
        expressions.

        :param regexes:
               A list of regex expressions to check against.
        :param items:
               A list of items to run the regex against.

        :return: True if any item matches any regex. False otherwise.
        """

        for regex in regexes:
            for item in items:
                if re.match(str(regex), item) is not None:
                    return True
        return False

    # ------------------------------------------------------------------------------------------------------------------
    def _os_walk_error(self,
                       exception_obj):
        """
        Handle errors during the os.walk scan of the dir

        :param exception_obj:
               The exception that occurred.

        :return: Nothing.
        """

        self.error_count += 1

        if os.path.isdir(exception_obj.filename):
            if exception_obj.errno == errno.EACCES:
                self.dir_permission_err_files.add(exception_obj.filename)
            else:
                self.dir_generic_err_files.add(exception_obj.filename)
        else:
            if exception_obj.errno == errno.EACCES:
                self.file_permission_err_files.add(exception_obj.filename)
            else:
                self.file_generic_err_files.add(exception_obj.filename)

    # ------------------------------------------------------------------------------------------------------------------
    def scan_directory(self,
                       scan_dir,
                       skip_sub_dir=False,
                       skip_hidden=False,
                       skip_zero_len=True,
                       incl_dir_regexes=None,
                       excl_dir_regexes=None,
                       incl_file_regexes=None,
                       excl_file_regexes=None,
                       report_frequency=1000):
        """
        Scan an entire directory and store the metadata for every file (optionally include subdirectories).

        :param scan_dir:
               A full path to the directory to scan.
        :param skip_sub_dir:
               If True, then no subdirectories will be included (only the top-level directory will be scanned). Defaults
               to False.
        :param skip_hidden:
               If True, then hidden files will be ignored in the scan. Defaults to False.
        :param skip_zero_len:
               If True, then files of zero length will be skipped. Defaults to True.
        :param incl_dir_regexes:
               A regular expression (or list of regular expressions) to filter matching directories. Only those that
               match this regex will be INCLUDED. If None, no filtering will be done. Defaults to None.
        :param excl_dir_regexes:
               A regular expression (or list of regular expressions) to filter matching directories. Those that match
               this regex will be EXCLUDED. If None, no filtering will be done. Defaults to None.
        :param incl_file_regexes:
               A regular expression (or list of regular expressions) to filter matching files. Only those that match
               this regex will be INCLUDED. If None, no filtering will be done. Defaults to None.
        :param excl_file_regexes:
               A regular expression (or list of regular expressions) to filter matching files. Those that match this
               regex will be EXCLUDED. If None, no filtering will be done. Defaults to None.
        :param report_frequency:
               After this many files have been scanned, report back to the calling function via a yield statement (to
               keep allow the calling function to report on the progress or interrupt it in some way.)  Defaults to 1000
               files.

        :return: Nothing.
        """

        assert type(scan_dir) is str

        if not scan_dir:
            raise IOError("No directory has been set to scan.")

        if not os.path.exists(scan_dir):
            raise IOError(f"The directory {scan_dir} does not exist")

        if not os.path.isdir(scan_dir):
            raise IOError(f"The path {scan_dir} is not a directory")

        self.scan_dir = scan_dir

        incl_dir_regexes = self._parameter_to_list(incl_dir_regexes)
        excl_dir_regexes = self._parameter_to_list(excl_dir_regexes)
        incl_file_regexes = self._parameter_to_list(incl_file_regexes)
        excl_file_regexes = self._parameter_to_list(excl_file_regexes)

        for root, sub_folders, files_n in os.walk(self.scan_dir, onerror=self._os_walk_error):

            files_p = [os.path.join(root, file_n) for file_n in files_n]

            for _ in self.scan_files(files_p=files_p,
                                     skip_hidden=skip_hidden,
                                     skip_zero_len=skip_zero_len,
                                     incl_dir_regexes=incl_dir_regexes,
                                     excl_dir_regexes=excl_dir_regexes,
                                     incl_file_regexes=incl_file_regexes,
                                     excl_file_regexes=excl_file_regexes,
                                     report_frequency=report_frequency):
                yield self.checked_count

            if skip_sub_dir:
                sub_folders[:] = []

    # ------------------------------------------------------------------------------------------------------------------
    def scan_files(self,
                   files_p,
                   skip_hidden=False,
                   skip_zero_len=True,
                   incl_dir_regexes=None,
                   excl_dir_regexes=None,
                   incl_file_regexes=None,
                   excl_file_regexes=None,
                   report_frequency=1000):
        """
        Scan a specific list of files and store the metadata for every file.

        :param files_p:
               A list of files (with full paths).
        :param skip_hidden:
               If True, then hidden files will be ignored in the scan. Defaults to False.
        :param skip_zero_len:
               If True, then files of zero length will be skipped. Defaults to True.
        :param incl_dir_regexes:
               A regular expression (or list of regular expressions) to filter matching directories. Only those that
               match this regex will be INCLUDED. If None, no filtering will be done. Defaults to None.
        :param excl_dir_regexes:
               A regular expression (or list of regular expressions) to filter matching directories. Those that match
               this regex will be EXCLUDED. If None, no filtering will be done. Defaults to None.
        :param incl_file_regexes:
               A regular expression (or list of regular expressions) to filter matching files. Only those that match
               this regex will be INCLUDED. If None, no filtering will be done. Defaults to None.
        :param excl_file_regexes:
               A regular expression (or list of regular expressions) to filter matching files. Those that match this
               regex will be EXCLUDED. If None, no filtering will be done. Defaults to None.
        :param report_frequency:
               After this many files have been scanned, report back to the calling function via a yield statement (to
               keep allow the calling function to report on the progress or interrupt it in some way.)  Defaults to
               1000 files.

        :return: Nothing.
        """

        assert type(files_p) is list

        for file_p in files_p:

            self.checked_count += 1

            file_d, file_n = os.path.split(file_p)
            path_items = [item for item in file_d.split(os.path.sep) if item != ""]

            # This needs to come before testing access, because a link always fails the os.R_OK test
            if os.path.islink(file_p):
                self.skipped_links += 1
                continue

            if not os.access(file_p, os.R_OK):
                self.error_count += 1
                self.file_permission_err_files.add(file_p)
                continue

            if self.checked_count % report_frequency == 0:
                yield self.checked_count

            if skip_hidden and file_n[0] == ".":
                self.skipped_hidden += 1
                continue

            if incl_dir_regexes:
                if not self._match_regex(regexes=incl_dir_regexes, items=path_items):
                    self.skipped_include += 1
                    continue

            if excl_dir_regexes is not None:
                if self._match_regex(regexes=excl_dir_regexes, items=path_items):
                    self.skipped_exclude += 1
                    continue

            if incl_file_regexes is not None:
                if not self._match_regex(regexes=incl_file_regexes, items=[file_n]):
                    self.skipped_include += 1
                    continue

            if excl_file_regexes is not None:
                if self._match_regex(regexes=excl_file_regexes, items=[file_n]):
                    self.skipped_exclude += 1
                    continue

            try:
                file_size = os.path.getsize(file_p)
            except FileNotFoundError:
                self.file_not_found_err_files.add(file_p)
                self.error_count += 1
                continue

            if skip_zero_len:
                if file_size == 0:
                    self.skipped_zero_len += 1
                    continue

            self.initial_count += 1

            file_metadata = self._get_metadata(file_p)

            self._append_to_scan(file_path=file_p,
                                 metadata=file_metadata)
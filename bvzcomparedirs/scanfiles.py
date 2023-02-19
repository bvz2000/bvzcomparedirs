#! /usr/bin/env python3

import os.path
import re
import stat


class ScanFiles(object):
    """
    A class to scan and store the attributes of every file in multiple directories and/or an arbitrary list of files.
    This class should be subclassed and not used directly.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 scan_options):
        """
        :param scan_options:
            An options object containing the preferences for the scan parameters.
        """

        self.options = scan_options

        self.file_permission_err_files = set()
        self.dir_permission_err_dirs = set()
        self.file_not_found_err_files = set()
        self.dir_generic_err_dirs = set()
        self.file_generic_err_files = set()

        self.initial_count = 0
        self.checked_count = 0
        self.skipped_links = 0
        self.error_count = 0
        self.skipped_zero_len = 0
        self.skipped_hidden_files = 0
        self.skipped_hidden_dirs = 0
        self.skipped_exclude_dirs = 0
        self.skipped_include_dirs = 0
        self.skipped_exclude_files = 0
        self.skipped_include_files = 0

        self.checksum = dict()

        self.scanned_files = set()

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _get_filesystem_root():
        """
        Returns the root of the filesystem. On Unix-type systems this will be "/". On Windows god only knows what
        abomination they have come up with. For now, only Unix-style systems are supported. But this method is here so
        that I can add Windows compatibility in the future.

        :return:
            The path to the root of the filesystem.
        """

        return os.path.sep

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _is_hidden(file_p):
        """
        Returns whether the given file path is a hidden file. On Unix-type systems this is simply if the file name
        begins with a dot. On Windows there is some other mechanism at play that I don't feel like dealing with right
        now. But this method exists so that I can add Windows compatibility in the future.

        :param file_p:
            The path to the file that we want to determine whether it is hidden or not.

        :return:
            True if the file is hidden. False otherwise.
        """

        assert type(file_p) is str

        return os.path.split(file_p)[1][0] == "."

    # ------------------------------------------------------------------------------------------------------------------
    def store_checksum_in_cache(self,
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
    def retrieve_checksum_from_cache(self,
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
    @staticmethod
    def _has_file_read_permissions(st_mode,
                                   file_uid,
                                   file_gid,
                                   uid,
                                   gid):
        """
        Returns true if the uid and gid passed has read permissions for the passed file's st_mode, file_uid, and
        file_gid.

        :param st_mode:
            The results of an os.stat.st_mode on the file in question.
        :param file_uid:
            The user id of the file in question.
        :param file_gid:
            The group id of the file in question.
        :param uid:
            The user id of the user who we are testing against.
        :param gid:
            The group id of the user who we are testing against.

        :return:
            True if the user has read permissions.
        """

        assert type(st_mode) is int
        assert type(file_uid) is int
        assert type(file_gid) is int
        assert type(uid) is int
        assert type(gid) is int

        if file_uid == uid:
            return bool(stat.S_IRUSR & st_mode)

        if file_gid == gid:
            return bool(stat.S_IRGRP & st_mode)

        return bool(stat.S_IROTH & st_mode)

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _get_metadata(file_p,
                      root_p):
        """
        Gets the metadata for the given file path.

        :param file_p:
            The path to the file to add.
        :param root_p:
            The path to the root against which a relative path is determined.

        :return:
            A dictionary of attributes.
        """

        assert type(file_p) is str
        assert type(root_p) is str

        attrs = dict()

        file_stat = os.stat(file_p, follow_symlinks=False)

        attrs["name"] = os.path.split(file_p)[1]
        attrs["file_type"] = os.path.splitext(attrs["name"])[1]
        attrs["parent"] = os.path.split(os.path.split(file_p)[0])[1]
        attrs["rel_path"] = os.path.relpath(file_p, root_p)
        attrs["size"] = file_stat.st_size
        attrs["ctime"] = file_stat.st_ctime  # Not always the creation time, but as close as it gets.
        attrs["mtime"] = file_stat.st_mtime
        attrs["isdir"] = stat.S_ISDIR(file_stat.st_mode)
        attrs["islink"] = stat.S_ISLNK(file_stat.st_mode)
        attrs["st_mode"] = file_stat.st_mode
        attrs["file_uid"] = file_stat.st_uid
        attrs["file_gid"] = file_stat.st_gid

        return attrs

    # ------------------------------------------------------------------------------------------------------------------
    def _append_to_scan(self,
                        file_path,
                        metadata):
        """
        To be overridden in subclass

        :return:
            Nothing.
        """

        raise NotImplementedError

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _match_any_regex(regexes,
                         item):
        """
        Given a list of regex expressions and an item, returns True if the item matches ALL the regex expressions.

        :param regexes:
            A list of regex expressions to check against.
        :param item:
            A string to run the regex against.

        :return:
            True if any item matches any regex. False otherwise.
        """

        assert type(regexes) in [list, set, tuple]
        for regex in regexes:
            assert type(regex) is str

        for regex in regexes:
            if re.search(str(regex), item) is not None:
                return True
        return False

    # ------------------------------------------------------------------------------------------------------------------
    def scan_directories(self,
                         scan_dirs,
                         uid,
                         gid):
        """
        Scan a list of directories and store the metadata for every file (optionally include subdirectories).

        :param scan_dirs:
            A list containing full paths to directories to scan.
        :param uid:
            The user id of the user running the script
        :param gid:
            The group id of the user running the script

        :return:
            Nothing.
        """

        assert type(scan_dirs) in [list, set, tuple]
        assert type(uid) is int
        assert type(gid) is int

        for scan_dir in scan_dirs:
            for _ in self.scan_directory(scan_dir=scan_dir, root_p=scan_dir, uid=uid, gid=gid):
                yield self.checked_count

    # ------------------------------------------------------------------------------------------------------------------
    def scan_directory(self,
                       scan_dir,
                       root_p,
                       uid,
                       gid):
        """
        Recursively scan an entire directory and its subdirectories and store the metadata for every file.

        :param scan_dir:
            A full path to the directory to scan.
        :param root_p:
            The path to the root directory (for comparing relative paths)
        :param uid:
            The user id of the user running the script
        :param gid:
            The group id of the user running the script

        :return:
            Nothing.
        """

        assert type(scan_dir) is str
        assert type(root_p) is str
        assert type(uid) is int
        assert type(gid) is int

        if not scan_dir:
            raise IOError("No directory has been set to scan.")

        if not os.path.exists(scan_dir):
            raise IOError(f"The directory {scan_dir} does not exist")

        if not os.path.isdir(scan_dir):
            raise IOError(f"The path {scan_dir} is not a directory")

        try:

            for entry in os.scandir(scan_dir):

                if entry.is_dir(follow_symlinks=False) and not self.options.skip_sub_dir:

                    if self.options.skip_hidden_dirs and entry.name[0] == ".":
                        self.skipped_hidden_dirs += 1
                        yield self.checked_count
                        continue

                    if self.options.incl_dir_regexes:
                        if not self._match_any_regex(regexes=self.options.incl_dir_regexes, item=entry.path):
                            self.skipped_include_dirs += 1
                            yield self.checked_count
                            continue

                    if self.options.excl_dir_regexes is not None:
                        if self._match_any_regex(regexes=self.options.excl_dir_regexes, item=entry.path):
                            self.skipped_exclude_dirs += 1
                            yield self.checked_count
                            continue

                    yield from self.scan_directory(scan_dir=entry.path, root_p=root_p, uid=uid, gid=gid)
                    continue

                self.scan_file(file_p=entry.path, root_p=root_p, uid=uid, gid=gid)
                if self.checked_count % self.options.report_frequency == 0:
                    yield self.checked_count

        except PermissionError:

            self.error_count += 1
            self.dir_permission_err_dirs.add(scan_dir)

    # ------------------------------------------------------------------------------------------------------------------
    def scan_files(self,
                   files_p,
                   root_p,
                   uid,
                   gid):
        """
        Scan a specific list of files and store the metadata for every file.

        :param files_p:
            A list, set, or tuple of files (with full paths).
        :param root_p:
            The root path against which a relative path for the files can be extracted.
        :param uid:
            The user id of the user running the script
        :param gid:
            The group id of the user running the script

        :return:
            Nothing.
        """

        assert type(files_p) in [list, set, tuple]
        assert type(root_p) is str
        assert type(uid) is int
        assert type(gid) is int

        for file_p in files_p:

            if os.path.islink(file_p):
                self.skipped_links += 1
                return

            self.scan_file(file_p=file_p, root_p=root_p, uid=uid, gid=gid)
            if self.checked_count % self.options.report_frequency == 0:
                yield self.checked_count

    # ------------------------------------------------------------------------------------------------------------------
    def scan_file(self,
                  file_p,
                  root_p,
                  uid,
                  gid):
        """
        Scan a single file and stores its metadata.

        :param file_p:
            A full path toa file to scan.
        :param root_p:
            The root path against which a relative path for the files can be extracted.
        :param uid:
            The user id of the user running the script
        :param gid:
            The group id of the user running the script

        :return:
            Nothing.
        """

        assert type(file_p) is str
        assert type(root_p) is str
        assert type(uid) is int
        assert type(gid) is int

        self.checked_count += 1

        file_d, file_n = os.path.split(file_p)

        if self.options.skip_hidden_files:
            if self._is_hidden(file_p=file_p):
                self.skipped_hidden_files += 1
                return

        if self.options.incl_dir_regexes:
            if not self._match_any_regex(regexes=self.options.incl_dir_regexes, item=file_d):
                self.skipped_include_files += 1
                return

        if self.options.excl_dir_regexes is not None:
            if self._match_any_regex(regexes=self.options.excl_dir_regexes, item=file_d):
                self.skipped_include_files += 1
                return

        if self.options.incl_file_regexes is not None:
            if not self._match_any_regex(regexes=self.options.incl_file_regexes, item=file_n):
                self.skipped_include_files += 1
                return

        if self.options.excl_file_regexes is not None:
            if self._match_any_regex(regexes=self.options.excl_file_regexes, item=file_n):
                self.skipped_exclude_files += 1
                return

        try:
            attrs = self._get_metadata(file_p=file_p, root_p=root_p)
        except FileNotFoundError:
            self.error_count += 1
            self.file_not_found_err_files.add(file_p)
            return

        if attrs["islink"]:
            self.skipped_links += 1
            return

        if not self._has_file_read_permissions(st_mode=attrs["st_mode"],
                                               file_uid=attrs["file_uid"],
                                               file_gid=attrs["file_gid"],
                                               uid=uid,
                                               gid=gid):
            self.error_count += 1
            self.file_permission_err_files.add(file_p)
            return

        if self.options.skip_zero_len:
            if attrs["size"] == 0:
                self.skipped_zero_len += 1
                return

        self.initial_count += 1

        self._append_to_scan(file_path=file_p,
                             metadata=attrs)

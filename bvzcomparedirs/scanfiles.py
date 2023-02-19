#! /usr/bin/env python3

import errno
import os.path
import re
import stat


class ScanFiles(object):
    """
    A class to scan and store the attributes of every file in a single directory. Alternately has the ability to work
    with an arbitrary list of files instead of a scanned directory. This class should be subclassed and not used
    directly.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 options):
        """
        :param options:
            An options object containing the preferences for the scan parameters.
        """

        self.options = options

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
            Norhing.
        """

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

        try:
            return self.checksum[file_p]
        except KeyError:
            return None

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _has_read_permissions(st_mode,
                              file_uid,
                              file_gid,
                              uid,
                              gid):
        """
        Returns true if the uid passed has read permissions for the passed file stat

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
    def _match_regex(regexes,
                     items):
        """
        Given a list of regex expressions and a list of items, returns True if any of the items match any of the regex
        expressions.

        :param regexes:
            A list of regex expressions to check against.
        :param items:
            A list of items to run the regex against.

        :return:
            True if any item matches any regex. False otherwise.
        """

        for regex in regexes:
            for item in items:
                if re.search(str(regex), item) is not None:
                    return True
        return False

    # ------------------------------------------------------------------------------------------------------------------
    def _os_walk_error(self,
                       exception_obj):
        """
        Handle errors during the os.walk scan of the dir

        :param exception_obj:
            The exception that occurred.

        :return:
            Nothing.
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

        if not scan_dir:
            raise IOError("No directory has been set to scan.")

        if not os.path.exists(scan_dir):
            raise IOError(f"The directory {scan_dir} does not exist")

        if not os.path.isdir(scan_dir):
            raise IOError(f"The path {scan_dir} is not a directory")

        for entry in os.scandir(scan_dir):

            if entry.is_dir(follow_symlinks=False) and not self.options.skip_sub_dir:

                if self.options.incl_dir_regexes:
                    if not self._match_regex(regexes=self.options.incl_dir_regexes, items=[entry.path]):
                        self.skipped_include_dirs += 1
                        yield self.checked_count
                        continue

                if self.options.excl_dir_regexes is not None:
                    if self._match_regex(regexes=self.options.excl_dir_regexes, items=[entry.path]):
                        self.skipped_exclude_dirs += 1
                        yield self.checked_count
                        continue

                yield from self.scan_directory(scan_dir=entry.path, root_p=root_p, uid=uid, gid=gid)
                continue

            self.scan_file(file_p=entry.path, root_p=root_p, uid=uid, gid=gid)
            if self.checked_count % self.options.report_frequency == 0:
                yield self.checked_count

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
        assert root_p is None or type(root_p) is str

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
        assert root_p is None or type(root_p) is str

        self.checked_count += 1

        file_d, file_n = os.path.split(file_p)

        if self.options.skip_hidden:
            if self._is_hidden(file_p=file_p):
                self.skipped_hidden += 1
                return

        if self.options.incl_dir_regexes:
            if not self._match_regex(regexes=self.options.incl_dir_regexes, items=[file_d]):
                self.skipped_include_files += 1
                return

        if self.options.excl_dir_regexes is not None:
            if self._match_regex(regexes=self.options.excl_dir_regexes, items=[file_d]):
                self.skipped_include_files += 1
                return

        if self.options.incl_file_regexes is not None:
            if not self._match_regex(regexes=self.options.incl_file_regexes, items=[file_n]):
                self.skipped_include_files += 1
                return

        if self.options.excl_file_regexes is not None:
            if self._match_regex(regexes=self.options.excl_file_regexes, items=[file_n]):
                self.skipped_exclude_files += 1
                return

        try:
            attrs = self._get_metadata(file_p=file_p, root_p=root_p)
        except FileNotFoundError:
            self.error_count += 1
            self.file_not_found_err_files.add(file_p)
            return

        # This needs to come before testing access, because a link always fails the os.R_OK test
        if attrs["islink"]:
            self.skipped_links += 1
            return

        if not self._has_read_permissions(st_mode=attrs["st_mode"],
                                          file_uid=attrs["file_uid"],
                                          file_gid=attrs["file_gid"],
                                          uid=uid,
                                          gid=gid):
            self.error_count += 1
            self.file_permission_err_files.add(file_p)
            return

        # if not os.access(file_p, os.R_OK):
        #     self.error_count += 1
        #     self.file_permission_err_files.add(file_p)
        #     return

        if self.options.skip_zero_len:
            if attrs["size"] == 0:
                self.skipped_zero_len += 1
                return

        self.initial_count += 1

        self._append_to_scan(file_path=file_p,
                             metadata=attrs)

    #
    #
    #
    # # ------------------------------------------------------------------------------------------------------------------
    # def old_scan_file(self,
    #               file_p,
    #               root_p=None):
    #     """
    #     Scan a single file and stores its metadata.
    #
    #     :param file_p:
    #         A full path toa file to scan.
    #     :param root_p:
    #         The root path against which a relative path for the files can be extracted. If None, uses the root of the
    #         file system. Default is None.
    #
    #     :return:
    #         Nothing.
    #     """
    #
    #     assert type(file_p) is str
    #     assert root_p is None or type(root_p) is str
    #
    #     if root_p is None:
    #         root_p = self._get_filesystem_root()
    #
    #     file_d, file_n = os.path.split(file_p)
    #     path_items = [item for item in file_d.split(os.path.sep) if item != ""]
    #
    #     self.checked_count += 1
    #
    #     # This needs to come before testing access, because a link always fails the os.R_OK test
    #     if os.path.islink(file_p):
    #         self.skipped_links += 1
    #         return
    #
    #     if not os.path.exists(file_p):
    #         self.error_count += 1
    #         self.file_not_found_err_files.add(file_p)
    #         return
    #
    #     if not os.access(file_p, os.R_OK):
    #         self.error_count += 1
    #         self.file_permission_err_files.add(file_p)
    #         return
    #
    #     if self.options.skip_hidden and self._is_hidden(file_p=file_p):
    #         self.skipped_hidden += 1
    #         return
    #
    #     if self.options.incl_dir_regexes:
    #         if not self._match_regex(regexes=self.options.incl_dir_regexes, items=[file_d]):
    #             self.skipped_include += 1
    #             return
    #
    #     if self.options.excl_dir_regexes is not None:
    #         if self._match_regex(regexes=self.options.excl_dir_regexes, items=[file_d]):
    #             self.skipped_exclude += 1
    #             return
    #
    #     if self.options.incl_file_regexes is not None:
    #         if not self._match_regex(regexes=self.options.incl_file_regexes, items=[file_n]):
    #             self.skipped_include += 1
    #             return
    #
    #     if self.options.excl_file_regexes is not None:
    #         if self._match_regex(regexes=self.options.excl_file_regexes, items=[file_n]):
    #             self.skipped_exclude += 1
    #             return
    #
    #     try:
    #         file_size = os.path.getsize(file_p)
    #     except FileNotFoundError:
    #         self.file_not_found_err_files.add(file_p)
    #         self.error_count += 1
    #         return
    #
    #     if self.options.skip_zero_len:
    #         if file_size == 0:
    #             self.skipped_zero_len += 1
    #             return
    #
    #     self.initial_count += 1
    #
    #     file_metadata = self._get_metadata(file_p=file_p,
    #                                        root_p=root_p)
    #
    #     self._append_to_scan(file_path=file_p,
    #                          metadata=file_metadata)

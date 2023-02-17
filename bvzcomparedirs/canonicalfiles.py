#! /usr/bin/env python3

from . scanfiles import ScanFiles


class CanonicalFiles(ScanFiles):
    """
    A class to scan and store the attributes of the canonical list of files.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 options):
        """
        :param options:
            An options object containing the preferences for the scan parameters.
        """

        super().__init__(options)

        self.by_size = dict()
        self.by_name = dict()
        self.by_parent = dict()
        self.by_type = dict()
        self.by_rel_path = dict()
        self.by_ctime = dict()
        self.by_mtime = dict()

        self.checksum = dict()

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _append_to_dict(by_dict,
                        key,
                        file_path):
        """
        Appends the file_path to the given dictionary.

        :param by_dict:
            The dictionary to append to.
        :param file_path:
            The path that is being appended.

        :return:
            Nothing.
        """

        try:
            by_dict[key].add(file_path)
        except KeyError:
            by_dict[key] = {file_path}

    # ------------------------------------------------------------------------------------------------------------------
    def _append_to_scan(self,
                        file_path,
                        metadata):
        """
        Appends a new file to the scan dictionaries.

        :param file_path:
            The path to the file to add
        :param metadata:
            The metadata for this file.

        :return:
            Nothing.
        """

        self._append_to_dict(by_dict=self.by_size,
                             key=metadata["size"],
                             file_path=file_path)

        self._append_to_dict(by_dict=self.by_name,
                             key=metadata["name"],
                             file_path=file_path)

        self._append_to_dict(by_dict=self.by_type,
                             key=metadata["file_type"],
                             file_path=file_path)

        self._append_to_dict(by_dict=self.by_parent,
                             key=metadata["parent"],
                             file_path=file_path)

        self._append_to_dict(by_dict=self.by_rel_path,
                             key=metadata["rel_path"],
                             file_path=file_path)

        self._append_to_dict(by_dict=self.by_ctime,
                             key=metadata["ctime"],
                             file_path=file_path)

        self._append_to_dict(by_dict=self.by_mtime,
                             key=metadata["mtime"],
                             file_path=file_path)

    # ------------------------------------------------------------------------------------------------------------------
    def get_intersection(self,
                         size,
                         name=None,
                         file_type=None,
                         parent=None,
                         rel_path=None,
                         ctime=None,
                         mtime=None):
        """
        Returns a set of file paths that exist at the intersection of the given attributes. Any attributes that are set
        to None are ignored.
        
        For example: If size=1024, name="bob.txt" and all other attributes are None, then a set will be returned that
        contains all file paths that exist in BOTH the by_size[1024] dictionary and by_name["bob.txt"] dictionary.

        :param size:
            The file size key. This attribute is required.
        :param name:
            The file name key. If None, then this attribute is ignored when creating the intersection.
        :param file_type:
            The file_type key. If None, then this attribute is ignored when creating the intersection.
        :param parent:
            The parent key. If None, then this attribute is ignored when creating the intersection.
        :param rel_path:
            The rel_path key. If None, then this attribute is ignored when creating the intersection.
        :param ctime:
            The ctime key. If None, then this attribute is ignored when creating the intersection.
        :param mtime:
            The mtime key. If None, then this attribute is ignored when creating the intersection.

        :return:
            A set of file paths that exist in the intersection of all the dictionaries whose passed attribute is not
            None.
        """

        try:
            size_set = self.by_size[size]
        except KeyError:
            size_set = set()

        sets = list()

        if name:
            try:
                sets.append(self.by_name[name])
            except KeyError:
                return set()

        if file_type:
            try:
                sets.append(self.by_type[file_type])
            except KeyError:
                return set()

        if parent:
            try:
                sets.append(self.by_parent[parent])
            except KeyError:
                return set()

        if rel_path:
            try:
                sets.append(self.by_rel_path[rel_path])
            except KeyError:
                return set()

        if ctime:
            try:
                sets.append(self.by_ctime[ctime])
            except KeyError:
                return set()

        if mtime:
            try:
                sets.append(self.by_mtime[mtime])
            except KeyError:
                return set()

        intersection = size_set.intersection(*sets)

        return intersection

    # ------------------------------------------------------------------------------------------------------------------
    def get_checksum(self,
                     file_path):
        """
        Tries to load the checksum from the checksum dictionary. If there is no checksum available, returns None.

        :param file_path:
            The path to the file for which we want to get the stored checksum.

        :return:
            The checksum that was stored. If there was no stored checksum, returns None.
        """

        try:
            return self.checksum[file_path]
        except KeyError:
            return None

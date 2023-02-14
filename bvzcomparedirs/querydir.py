#! /usr/bin/env python3

from . scandir import ScanDir


class QueryDir(ScanDir):
    """
    A class to scan and store the attributes of every file in a Query directory.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """
        """
        super().__init__()

        self.files = dict()

    # ------------------------------------------------------------------------------------------------------------------
    def _append_to_scan(self,
                        file_path,
                        metadata):
        """
        Appends a new file to the scan dictionary.

        :param file_path:
               The path to the file to add
        :param metadata:
               The metadata for this file.

        :return: Nothing.
        """

        self.files[file_path] = metadata

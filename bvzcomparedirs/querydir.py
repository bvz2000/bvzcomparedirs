#! /usr/bin/env python3

from scandir import ScanDir


class QueryDir(ScanDir):
    """
    A class to scan and store the attributes of every file in a Query directory.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 scan_dir):
        """
        :param scan_dir: The directory to scan.
        """
        super().__init__(scan_dir=scan_dir)

        self.files = dict()

    # ------------------------------------------------------------------------------------------------------------------
    def _append_to_scan(self,
                        file_path,
                        metadata):
        """
        Appends a new file to the scan dictionary.

        :param file_path: The path to the file to add
        :param metadata: The metadata for this file.

        :return: Nothing.
        """

        self.files[file_path] = metadata

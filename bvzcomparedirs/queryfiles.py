#! /usr/bin/env python3

from . scanfiles import ScanFiles


class QueryFiles(ScanFiles):
    """
    A class to scan and store the attributes of a list of query files.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 options):
        """
        :param options:
            An options object containing the preferences for the scan parameters.
        """

        super().__init__(options)

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

        :return:
            Nothing.
        """

        self.files[file_path] = metadata

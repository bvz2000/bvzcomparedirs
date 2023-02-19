from dataclasses import dataclass


@dataclass
class Options:
    skip_sub_dir: bool = False
    skip_hidden_files: bool = False
    skip_hidden_dirs: bool = False
    skip_zero_len: bool = True
    incl_dir_regexes: list = None
    excl_dir_regexes: list = None
    incl_file_regexes: list = None
    excl_file_regexes: list = None
    report_frequency: int = 10

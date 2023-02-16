# bvzcomparedirs

A python library to help identify duplicate files in two different directory hierarchies.

This library takes in two directories: a canonical directory and a query directory.

Both directories are scanned (including subdirectories if so desired). After the scans are completed, the Session object can be queried to identify any files in the query directory that are identical to the files in the canonical directory, as well as any files in the query directory that are not present in the canonical directory, or are present but have different contents.

Files may be compared on any combination of name, creation date and time, modification date and time, file type, parent directory name, relative paths within each directory (canonical or query), and md5 checksum. Files are always compared on size. If only checksum (and the implied size) is selected, duplicate files regardless of location in either directory, names, and any other metadata, can be identified.

Specific files to be included in the comparison operation may be controlled by filtering out hidden files (Hidden is defined using the Linux and MacOS convention: files with a leading dot), and filtering out zero length files. Regular expressions may also be used to include or exclude both individual files and entire subdirectories.

Future features: 
- Identify files that have the same name, but are unique.
- Identify files in the canoncial directory that are missing from the query directory.
- Cache md5 checksums for re-use between sessions.

# Example Usage:

The following is a very simplified example of using this library. It takes in an arbitrary number of 'query' files and/or
directories and a "canonical" directory where these files may or may not already exist. It then scans the query files and
directories, followed by a scan of the canonical directory. Then it runs a comparison operation and reports back which
files in the query directory already exist in the canonical directory, and which are unique.

```
from argparse import ArgumentParser
import sys

from bvzcomparedirs.comparesession import Session

# Read in an arbitrary list of query directories or files from the command
# line, as well as a canonical directory.
help_msg = "enter one or more 'query' directories or files followed by a " \
           "'canonical' directory to see whether the contents of these " \
           "'query' directories already exist in the canonical directory, " \
           "or are unique."

parser = ArgumentParser(description=help_msg)

help_str = "The query directories or files. These are the directories or " \
           "files that you want to inspect to see if they already exist " \
           "in the canonical directory. You may supply as many directories " \
           "or files here as needed."
parser.add_argument('query_dir',
                    metavar='query directories',
                    nargs="+",
                    type=str,
                    help=help_str)

help_str = "The canonical directory. This is the directory where the files " \
           "should eventually live. It is the 'official' location for any " \
           "specific group of files. Images, for example, might live in " \
           "subdirectories of a 'photos' directory. "
parser.add_argument('canonical_dir',
                    metavar='canonical directory',
                    type=str,
                    help=help_str)

args = parser.parse_args(sys.argv)

# Create a comparison session object, and hand it the query and canonical
# directory paths. Set the options so that the scans will descend into
# subdirectories, but they will skip hidden files and zero length files
# when doing the directory scans. Set the options to not use any regex
# expressions to filter the files or directories that will be scanned. Also
# set the options so that it will report back during the scans every 10
# files to allow the calling function to print a status during the scan.
# Note: Although we are only passing a single directory to the query_items
# parameter, we could just as easily have passed a list of directories to
# include in the scan, or a list of files, or a mixture of both.
session_obj = Session(query_items="/Server/dev/apps/compareFolders",
                      canonical_dir="/Server/dev/apps/importPhotos",
                      skip_sub_dir=False,
                      skip_hidden=True,
                      skip_zero_len=True,
                      incl_dir_regexes=None,
                      excl_dir_regexes=None,
                      incl_file_regexes=None,
                      excl_file_regexes=None,
                      report_frequency=10)

# Actually perform the scan of the query directories and/or files.
for counter in session_obj.do_query_scan():
    print(f"scanned {counter} query files")

# Actually perform the scan of the canonical directory.
for counter in session_obj.do_canonical_scan():
    print(f"scanned {counter} canonical files")

# Run the comparison. In this case we are setting the parameters so
# that names and parent directory names must match in order for the
# files to be considered identical. We are also doing an md5 checksum to
# ensure the contents of both files are identical. During the comparison
# after each file is compared, the count of compared files is reported
# back to this function so that an update can be printed.
for counter in session_obj.do_compare(name=True,
                                      file_type=False,
                                      parent=True,
                                      rel_path=False,
                                      ctime=False,
                                      mtime=False,
                                      skip_checksum=False):
    dupes_str = f"Duplicates: {len(session_obj.actual_matches.keys())}"
    unique_str = f"Unique: {len(session_obj.unique)}"
    error_str = f"Errors: {len(session_obj.source_error_files)}"
    print(f"Compared {counter} files. {dupes_str} {unique_str} {error_str}")

# Once the comparison has been run, ask the session object for the results.
num_files_checked = len(session_obj.query_scan.files)
num_duplicates = len(session_obj.actual_matches)
num_unique = len(session_obj.unique)
num_reused_checksum = session_obj.pre_computed_checksum_count
num_self = len(session_obj.skipped_self)

print(f"Number of files checked: {num_files_checked}")
print(f"Number of query files that are duplicates of canonical files: "
      f"{num_duplicates}")
print(f"Number of query files that have no duplicates in canonical dir: "
      f"{num_unique}")
print(f"Number of times a file was compared with itself: {num_self}")
print(f"Number of times a checksum was reused: {num_reused_checksum}")

print("MATCHES:")
for file_path, matches in session_obj.actual_matches.items():
    print(file_path)
    for match in matches:
        print(match)
    print("\n\n")

print("UNIQUE")
for file_path in session_obj.unique:
    print(file_path)

```
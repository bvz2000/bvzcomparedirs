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

The following is a very simplified example of using this library.

```
from comparesession import Session

# Create a comparison session object, and hand it the query and canonical
# directory paths. Descend into subdirectories, but skip hidden files and
# zero length files when doing the comparison. Do not use any regex
# expressions to filter the files that will be compared. Report back to
# the calling function every 10 files to give an update.
session_obj = Session(query_dir="/path/to/query/dir",
                      canonical_dir="/path/to/canonical/dir",
                      skip_sub_dir=False,
                      skip_hidden=True,
                      skip_zero_len=True,
                      incl_dir_regex=None,
                      excl_dir_regex=None,
                      incl_file_regex=None,
                      excl_file_regex=None,
                      report_frequency=10)
                      
for counter in session_obj.do_query_scan():
    print(f"scanned {counter} query files")
    
for counter in session_obj.do_canonical_scan():
    print(f"scanned (counter} canonical files")
    
# Run the comparison, names and parent directory names must match. Do an md5 checksum to
# ensure the contents of both files are identical.
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
    
num_files_checked = len(session_obj.query_scan.files)
num_duplicates = len(session_obj.actual_matches)
num_unique = len(session_obj.unique)
num_reused_checksum = session_obj.pre_computed_checksum_count
num_self = len(session_obj.skipped_self)

print(f"Number of files checked: {num_files_checked}")
print(f"Number of query files that are duplicates of canonical files: {num_duplicates}")
print(f"Number of query files that have no duplicates in canonical dir: {num_unique}")
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
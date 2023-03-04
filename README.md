# bvzcomparedirs

A python library to help identify duplicate files in two different directory hierarchies.

This library takes in a directory known as the canonical directory and a set of directories and/or files known as the
query items. 

The query items are the directories and/or files that will be compared to the files located in the canonical directory. 

Items in the query directories and/or files that are duplicates of files in the Canonical directory are noted. Similarly,
any items in the query directories and/or files that do not exist in the canonical directory are also noted. 
Specifically, after the compare session is complete, the Session object can be queried to identify any files in the 
query items that are identical to the files in the canonical directory, as well as any files in the query directory 
that are not present in the canonical directory, or are present but have different contents.

Files may be compared on any combination of name, creation date and time, modification date and time, file type, 
parent directory name, relative paths within each directory (canonical or query), and md5 checksum. Files are always 
compared on size. If only checksum (and the implied size) is selected, duplicate files regardless of location in either 
directory, names, and any other metadata, can be identified.

Specific files to be included in the comparison operation may be controlled by filtering out hidden files (Hidden is 
defined using the Linux and MacOS convention: files with a leading dot), and filtering out zero length files. 
Regular expressions may also be used to include or exclude both individual files and entire subdirectories.

Future features: 
- Identify files that have the same name, but are unique.
- Identify files in the canonical directory that are missing from the query directory.
- Cache md5 checksums for re-use between sessions.

### Installation:

Download the library and make sure your PYTHONPATH shell variable includes the location of this library.

### Dependencies:

This library makes use of the ```bvzcomparefiles``` library, also available on github at: 
https://github.com/bvz2000/bvzcomparefiles

Make sure you download that library as well, and that it lives somewhere on your PYTHONPATH.

### Example Usage:

The following is a very simplified example of using this library. It takes in an arbitrary number of 'query' files and/or
directories and a "canonical" directory where these files may or may not already exist. It then scans the query files and
directories, followed by a scan of the canonical directory. Then it runs a comparison operation and reports back which
files in the query directory already exist in the canonical directory, and which are unique.

Also see the sample.py file included in this library for sample code.

To start off, import the Session class and initialize it. You should pass it a list of items that you are curious about
(i.e. files and/or directories that you want to query to see if they already exist somewhere in the canonical 
directory) as well as a path to the canonical directory (the location where files of these types should officially live). 
Here you can set any filters you want to use to control which files are considered and which are ignored.
The regex patterns are particularly powerful, and you may include a list of multiple regex patterns for each type of regex
(include directory regexes, exclude directory regexes, etc.)

```
from bvzcomparedirs.comparesession import Session

session_obj = Session(query_items=["/Path/to/query/dir/", "/path/to/query/file"],
                      canonical_dir="/path/to/canoncial/dir",
                      skip_sub_dir=False,
                      skip_hidden=True,
                      skip_zero_len=True,
                      incl_dir_regexes=None,
                      excl_dir_regexes=None,
                      incl_file_regexes=None,
                      excl_file_regexes=None,
                      report_frequency=10)
```

Next, you need to actually scan each set of files (query files and directories and the canonical directory). Since these
are both generators, you need to use them in a for loop (or use the iterator next() function). In this example we are
choosing to print out the status of each scan.
```
for counter in session_obj.do_query_scan():
    print(f"scanned {counter} query files")

for counter in session_obj.do_canonical_scan():
    print(f"scanned {counter} canonical files")
```

Finally, do the actual comparison between both sets of filtered files (remember, the filters were set when the session
object was first instantiated). Here you can control the parameters of the scan (whether to match on name, parent directory
name, and so on). Note that files are always compared on size. Once again, this is a generator and so needs to be
accessed via a loop or the iterator next() function. In this example we are taking the opportunity to update the user
on the status of the compare.
```
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
```

Once the comparison has been run, you can request the results from the session object.
```
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
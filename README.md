# bvzcomparedirs

A python library to help identify and de-duplicate files on disk.

This library can take in two directories, a canoncial directory and a query directory.

Both directories are scanned (including sub-directories if so desired). A report in the form of a python list is returned that identifies any files in the query directory that are identical to the files in the canoncial directory, as well as any files in the query directory that are unique.

Files may be compared on name, creation date and time, modification date and time, file type, parent directory name, relative paths within each directory (canonical or query), and md5 checksum.

Future features: 
- Identify files that have the same name, but are unique. .
- Identify files in the canoncial directory that are missing from the query directory.
- Cache md5 checksums for re-use between sessions.
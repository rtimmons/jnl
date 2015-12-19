plaintext daily worklogs and scratch-files

- env var `JNL_DB` controls db root.  Defaults to `testdb` locally.

- db has subdirs `worklogs` with 20-character random guid-esque filenames intentionally not sorted. Run `worklog.pl` to generate a new one and open in TextMate.

- db has subdir `daily` that has filenames like `dxx-2015-12-19.txt`. The `dxx` prefix is to help searching & grepping. Run `daily.pl` to open today's entry (creating it if doesn't already exist)



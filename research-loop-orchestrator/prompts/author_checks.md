Write the coded checks for the key variable `{{variable}}`. Each is an R script that exits non-zero (`quit(status = 1)`) on any failure and prints what failed.

1. `tests/{{variable}}_fake_cases.R`: small made-up units with answers worked out by hand, one per edge case from the decided choices in the decision log (window edges, empty cases, panel edges, duplicates, missing values). Run the fast build's logic on them and compare whole rows.
2. `tests/{{variable}}_rules.R`: properties that hold whatever the data: duplicating or shuffling input changes nothing; repeating unit rows on purpose changes nothing; a new observation in a known class changes nothing while one in a new class adds exactly one; out-of-window data is ignored; other units' data does not matter; missing exactly when expected; bounds; one row per unit. Include rules that put defects into the input on purpose.
3. `tests/{{variable}}_data_checks.R`: unique keys, row counts, value ranges, missing shares, no infinite values, on `output/{{variable}}_fast.csv`.
4. `tests/{{variable}}_source_check.R`: draw a random sample of records of the size decided at gate 2 (see the decision log), compare each with the original source, write `report/{{variable}}_source_check.csv`, and fail on any mismatch.

Run each script once and make sure it runs. Stop.

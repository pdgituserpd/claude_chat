Build the variable `{{variable}}` the normal way.

Read `spec/{{variable}}_definition.md` and `spec/{{variable}}_keys.json`. Write `R/{{variable}}_fast.R`, which reads the data under `data/` and writes `output/{{variable}}_fast.csv` with one row per unit key and the variable as a column. Check unique keys before and after every merge and stop the run on a violation; never fix duplicates quietly. Log row counts at every step to standard output. Normalize ID formats before joining. Run the script with Rscript and make sure it completes. Stop.

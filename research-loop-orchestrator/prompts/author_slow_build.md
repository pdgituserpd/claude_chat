Build the variable `{{variable}}` the slow way.

Read `spec/{{variable}}_definition.md` and `spec/{{variable}}_keys.json`. Do not read `R/{{variable}}_fast.R`. Write `R/{{variable}}_slow.R`: plain code that follows the definition line by line, one sentence of the definition per block, with the sentence quoted as a comment above the block. Prefer loops and explicit steps over clever vectorized code. It writes `output/{{variable}}_slow.csv` with the same columns as the fast build. Run it with Rscript. Stop.

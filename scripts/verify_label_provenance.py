"""Reconcile ambiguous sample content against author normalized columns.

Read-only inputs. Standard-library only. Run from the project directory.
This tests identity up to a per-sample scalar, not biological plausibility.
"""
from pathlib import Path
import argparse
import csv
import json
import statistics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('../narain_et_al-2024-translational_psychiatry/narain_et_al-2024-translational_psychiatry'))
    parser.add_argument('--output', type=Path, default=Path('docs/metadata-content-matching.json'))
    args = parser.parse_args()
    raw = args.data / '01_data_raw/03_seq/02_counts_r'
    processed = args.data / '02_data_processed/02_seq/00_counts_processed/03_counts_timeseries'
    results = []
    for phenotype, animal in [('susceptible', 'A15_A'), ('control', 'C01_E1')]:
        code = 'S' if phenotype == 'susceptible' else 'C'
        for region in ['lhb', 'scn']:
            table = f'timeseries_{region}_{phenotype}.csv'
            with (processed / table).open() as handle:
                reader = csv.DictReader(handle)
                column = next(k for k in reader.fieldnames if animal.replace('_', '-') in k)
                values = {row['']: float(row[column]) for row in reader}
            for region_code in ['L', 'S']:
                sample = f'{region_code}1{code}-{animal}'
                with (raw / f'{sample}.txt').open() as handle:
                    counts = {row[0]: int(row[1]) for row in csv.reader(handle, delimiter='\t')}
                assert set(values) <= set(counts)
                ratios = [counts[g] / v for g, v in values.items() if counts[g] > 0 and v > 0]
                factor = statistics.median(ratios)
                errors = [abs(counts[g] - v * factor) / max(1, counts[g]) for g, v in values.items()]
                zero_disagreements = sum((counts[g] == 0) != (v == 0) for g, v in values.items())
                results.append(dict(author_table=table, author_column=column, raw_sample=sample,
                                    genes=len(values), nonzero_ratios=len(ratios),
                                    median_raw_over_processed=factor,
                                    max_relative_reconstruction_error=max(errors),
                                    median_relative_reconstruction_error=statistics.median(errors),
                                    zero_pattern_disagreements=zero_disagreements))
    for row in results:
        expected_raw_region = ('S' if 'lhb' in row['author_table'] else 'L') if 'A15' in row['raw_sample'] else ('L' if 'lhb' in row['author_table'] else 'S')
        expected_match = row['raw_sample'].startswith(expected_raw_region)
        actual_match = row['max_relative_reconstruction_error'] < 1e-6 and row['zero_pattern_disagreements'] == 0
        assert actual_match == expected_match, row
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: eight content comparisons; written {args.output}')


if __name__ == '__main__':
    main()

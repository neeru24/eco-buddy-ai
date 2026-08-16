# Emission Benchmark Datasets

## Overview

This directory contains benchmark datasets for emission calculations in EcoBuddy AI. These datasets are designed to verify that emission calculations remain stable across code updates, preventing regression in calculation logic.

## Files

### `emission_benchmark_datasets.json`
Contains benchmark test scenarios with expected outputs for emission calculations.

**Structure:**
- `metadata`: Information about the dataset including static factor references
- `datasets`: Organized test scenarios grouped by emission level and test type

### `bench_emission_validation.py`
Benchmark validation tool that tests emission calculations against the benchmark datasets.

### `test_emission_benchmarks.py`
Unit tests that use the benchmark datasets to verify calculation correctness.

## Dataset Categories

### 1. Low Emission Scenarios
- **Purpose**: Test eco-friendly lifestyles
- **Examples**: Bike commuting, vegetarian diet, minimal electricity use
- **Expected**: Low carbon footprints (≤ 2000 kg CO₂/year)

### 2. Medium Emission Scenarios  
- **Purpose**: Test average urban lifestyles
- **Examples**: Public transport, mixed diets, moderate electricity
- **Expected**: Moderate carbon footprints (4000-7000 kg CO₂/year)

### 3. High Emission Scenarios
- **Purpose**: Test high-impact lifestyles
- **Examples**: Frequent flying, high electricity use, maximum values
- **Expected**: High carbon footprints (≥ 20000 kg CO₂/year)

### 4. Edge Cases
- **Purpose**: Test boundary conditions and normalization
- **Examples**: Zero values, diet normalization, invalid region fallback
- **Expected**: Proper handling of edge conditions

### 5. Regression Tests
- **Purpose**: Replicate existing test cases
- **Examples**: Test cases from `test_emissions.py`
- **Expected**: Match existing test expectations

## How to Use

### Running Validation Tests

```bash
# Run benchmark validation
python benchmarks/bench_emission_validation.py

# Run unit tests with benchmark datasets
python test_emission_benchmarks.py

# Or use pytest
pytest test_emission_benchmarks.py -v
```

### Adding New Test Scenarios

1. Edit `emission_benchmark_datasets.json`
2. Add new test case to appropriate category
3. Include:
   - `name`: Descriptive name
   - `description`: What the scenario tests
   - `inputs`: All required input parameters
   - `expected_output`: Calculated totals, contributors, and eco score

4. Verify calculations match current implementation:
   ```python
   from emissions import calculate_footprint, calculate_eco_score
   
   # Test your scenario
   total, contributors = calculate_footprint(...)
   eco_score = calculate_eco_score(total, contributors)
   ```

## Calculation Basis

All expected outputs are calculated using static emission factors:

### Transport Factors (kg CO₂/km)
- Car: 0.21
- Bike: 0.0  
- Public Transport: 0.08
- Walking: 0.0

### Diet Factors (kg CO₂/year)
- Vegetarian: 1000
- Non-Vegetarian: 1800

### Other Factors
- Electricity: 0.82 kg CO₂/kWh (static fallback)
- Flights: 250.0 kg CO₂/flight (static fallback)

### Formulas
- **Transport**: `factor * distance * 365`
- **Electricity**: `usage * 0.82 * 12` (monthly to annual)
- **Diet**: Fixed annual amount
- **Flights**: `count * 250.0`

## Verification Process

1. **Dataset Loading**: Verify JSON loads correctly
2. **Static Factor Consistency**: Verify benchmark factors match config.py
3. **Calculation Validation**: Run all scenarios against current implementation
4. **Regression Detection**: Fail if calculations deviate from expected outputs

## Maintenance

When updating emission calculation logic:

1. Run benchmark validation first
2. If calculations change, update expected outputs in benchmark datasets
3. Document changes in commit messages
4. Verify all existing tests still pass

## Related Files

- `emissions.py`: Main emission calculation logic
- `config.py`: Emission constants and factors
- `test_emissions.py`: Existing unit tests
- `bench_emissions.py`: Performance benchmarks
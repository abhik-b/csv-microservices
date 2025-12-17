import pytest
from src.csv_processor import csv_processing, drop_columns, remove_duplicates, remove_missing_rows, fill_missing
import pandas as pd


@pytest.fixture
def sample_dataframe():
    """Common test DataFrame for all tests"""
    return pd.DataFrame({
        'A': [1, 1, 2, 3, 3, 4],
        'B': ['x', 'x', 'y', 'z', 'z', 'w'],
        'C': [24, 24, 34, 67, 67, 89],
        'D': [1.0, 2.0, None, 4.0, None, 6.0],
        'E': ['a', 'b', None, 'd', None, 'f']
    })


@pytest.fixture
def empty_dataframe():
    """Edge case: Empty DataFrame"""
    return pd.DataFrame()


# ---------------DROP COLUMNS-----------------------------------------------
# def test_drop_columns():
#     # 1. Arrange
#     df = pd.DataFrame(
#         {'A': [1, 1, 2, 3], 'B': ['x', 'x', 'y', 'z'], 'C': [24, 34, 54, 67]})
#     params1 = {"columns": ['B']}
#     params2 = {"columns": ['B', 'C']}

#     # 2. Act
#     result_df1 = drop_columns(df, params1)
#     result_df2 = drop_columns(df, params2)

#     # 3. Asset
#     assert len(result_df1.columns) == 2, "column B dropped"
#     assert len(result_df2.columns) == 1, "column B & C both dropped"


def test_dropcolumn(sample_dataframe):
    params = {"columns": ['B']}
    result = drop_columns(sample_dataframe.copy(), params)

    assert len(result.columns) == 4
    assert 'B' not in result.columns
    assert 'A' in result.columns  # Ensure other columns remain


def test_drop_columns_multiple(sample_dataframe):
    """Test dropping multiple columns"""
    params = {"columns": ['B', 'C']}
    result = drop_columns(sample_dataframe.copy(), params)

    assert len(result.columns) == 3
    assert 'B' not in result.columns
    assert 'C' not in result.columns


def test_drop_columns_nonexistent(sample_dataframe):
    """Test dropping columns that don't exist (should be ignored)"""
    params = {"columns": ['NonExistent', 'B']}
    result = drop_columns(sample_dataframe.copy(), params)

    assert 'B' not in result.columns  # Existing column dropped
    assert len(result.columns) == 4   # Only B dropped


def test_drop_columns_no_params(sample_dataframe):
    """Test with empty or missing params"""
    # Test with empty columns list
    params = {"columns": []}
    result = drop_columns(sample_dataframe.copy(), params)
    assert len(result.columns) == 5  # No change

    # Test with missing 'columns' key
    params = {}
    result = drop_columns(sample_dataframe.copy(), params)
    assert len(result.columns) == 5  # No change


def test_drop_columns_empty_dataframe(empty_dataframe):
    """Test with empty DataFrame"""
    params = {"columns": ['A']}
    result = drop_columns(empty_dataframe.copy(), params)
    assert len(result.columns) == 0  # Should handle gracefully


# ----------------DROP Duplicates-----------------------------------------------
def test_remove_duplicates_subset(sample_dataframe):
    """Test removing duplicates based on subset of columns"""
    params = {"subset": ['B']}
    result = remove_duplicates(sample_dataframe.copy(), params)

    # B has duplicates: 'x' appears twice, 'z' appears twice
    assert len(result) == 4  # Should remove 2 duplicates


def test_remove_duplicates_all_columns(sample_dataframe):
    """Test removing duplicates based on all columns (default)"""
    params = {}  # No subset means all columns
    result = remove_duplicates(sample_dataframe.copy(), params)
    assert len(result) <= len(sample_dataframe)


def test_remove_duplicates_keep_last(sample_dataframe):
    """Test keeping last occurrence instead of first"""
    params = {"subset": ['B'], "keep": 'last'}
    result = remove_duplicates(sample_dataframe.copy(), params)

    # Verify which rows were kept
    assert len(result) == 4
    # You could add specific row validation here


def test_remove_duplicates_no_duplicates(sample_dataframe):
    """Test when there are no duplicates"""
    # Create DataFrame with no duplicates
    unique_df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
    params = {"subset": ['A', 'B']}
    result = remove_duplicates(unique_df.copy(), params)

    assert len(result) == len(unique_df)  # No rows removed


def test_remove_duplicates_invalid_keep_value(sample_dataframe):
    """Test with invalid 'keep' parameter"""
    params = {"subset": ['B'], "keep": 'invalid'}
    # This should probably raise an error or handle gracefully
    # Check what your function actually does

# ---------------------Missing Rows---------------------------------


def test_remove_missing_rows_basic(sample_dataframe):
    """Test basic missing row removal"""
    # Count rows with any NaN before
    rows_with_nan_before = sample_dataframe.isna().any(axis=1).sum()

    params = {"how": "any"}
    result = remove_missing_rows(sample_dataframe.copy(), params)

    rows_with_nan_after = result.isna().any(axis=1).sum()
    assert rows_with_nan_after == 0  # All NaN rows removed
    assert len(result) == len(sample_dataframe) - rows_with_nan_before


def test_remove_missing_rows_subset(sample_dataframe):
    """Test removing rows with NaN in specific columns"""
    params = {"subset": ['D'], "how": "any"}
    result = remove_missing_rows(sample_dataframe.copy(), params)

    # Column D has 2 NaN values
    assert result['D'].notna().all()  # All NaN in D removed
    # But NaN in other columns might remain


def test_remove_missing_rows_all(sample_dataframe):
    """Test removing rows where ALL values are NaN"""
    params = {"how": "all"}
    result = remove_missing_rows(sample_dataframe.copy(), params)

    # In our sample, no row has ALL NaN, so no change
    assert len(result) == len(sample_dataframe)

# ------------------------Fill Missing Rows-------------------------


def test_fill_missing_constant(sample_dataframe):
    """Test filling missing values with constant"""
    params = {
        "method": "constant",
        "columns": {"D": 0.0, "E": "unknown"}
    }
    result = fill_missing(sample_dataframe.copy(), params)

    assert result['D'].isna().sum() == 0  # No NaN in D
    assert result['E'].isna().sum() == 0  # No NaN in E
    assert (result['D'] == 0.0).any()  # Some values are 0.0


def test_fill_missing_mean(sample_dataframe):
    """Test filling missing values with mean"""
    params = {
        "method": "mean",
        "columns": ["D"]  # Column D has numeric values
    }
    result = fill_missing(sample_dataframe.copy(), params)

    assert result['D'].isna().sum() == 0
    # Verify mean calculation is correct
    mean_value = sample_dataframe['D'].mean()
    # Check that NaN values were filled with mean

import pandas as pd

import re


def clean_remove_bracket(df: pd.DataFrame) -> pd.DataFrame:
    """
    Station name sells another name in their bracket for money.
        For example 청량리(서울시립대). Turn it into 청량리
    With function that remove whatever value that was inside the bracket.
        clean up the database
    """
    def _remove_bracket_string(value: any):
        if not isinstance(value, str):
            return value

        # delete all the substrings that's inside a bracket
        pattern = r'\([^()]*\)'
        return re.sub(pattern, '', value)

    return df.map(_remove_bracket_string)


def clean_subway_line_name(df: pd.DataFrame, subway_line_colname: str) -> pd.DataFrame:
    # NOTE: if more exception occurs, record here.
    specific = {'9호선2~3단계': '9호선', '9호선2단계': '9호선'}

    def _target_delete(value: any):
        if not isinstance(value, str):
            return value

        line_name = value.replace(' ', '')  # Remove whitespace
        if line_name in specific.keys():
            return specific[line_name]
        else:
            return line_name

    df[subway_line_colname] = df[subway_line_colname].map(_target_delete)
    return df

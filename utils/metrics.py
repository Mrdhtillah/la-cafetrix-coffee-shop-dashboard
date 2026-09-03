def total_revenue(df):

    return df["Revenue"].sum()


def total_transactions(df):

    return df["transaction_id"].nunique()


def average_order(df):

    return df["Revenue"].sum() / df["transaction_id"].nunique()


def units_sold(df):

    return df["transaction_qty"].sum()

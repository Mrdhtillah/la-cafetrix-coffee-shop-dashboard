import matplotlib.pyplot as plt
import seaborn as sns

def revenue_by_store(store_summary):

    fig, ax = plt.subplots(figsize=(10,5))

    sns.barplot(
        data=store_summary,
        x="Revenue",
        y="store_location",
        color="#6F4E37",
        ax=ax
    )

    ax.set_title("Revenue by Store")

    return fig
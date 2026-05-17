# import plotly.express as px


def plot_daily_fit(df_stats: pd.DataFrame, out: str) -> None:
    df = df_stats.copy()
    fig = px.scatter(
        df,
        x="nrmse_mean",
        y="pearson",
        color="variable",
        size=df["bias_pct"].abs().clip(0, 200),
        hover_name="variable",
        facet_col="period",  # one small panel per period
        facet_col_wrap=2,
        title="Daily fit: Pearson vs nRMSE by period",
        labels={
            "nrmse_mean": "nRMSE (lower better)",
            "pearson": "Pearson (higher better)",
        },
    )
    fig.update_traces(marker=dict(line=dict(width=1, color="black")))
    fig.write_image(out)

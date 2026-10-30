"""Create reproducible report figures for the US database."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from src.us_housing import ARTIFACTS, read_sales


def main():
    data = read_sales()
    out = ARTIFACTS / 'figures'
    out.mkdir(exist_ok=True)
    sns.set_theme(style='whitegrid', font_scale=0.9)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    yearly = data.groupby(['sale_year', 'locality']).size().unstack()
    yearly.plot.bar(ax=ax, color=['#167A78', '#CA7A40'])
    ax.set(xlabel='Sale year', ylabel='Accepted transactions', title='Observed records by year and locality')
    ax.tick_params(axis='x', rotation=0)
    ax.legend(title='Locality', fontsize=8)
    fig.tight_layout()
    fig.savefig(out / '01_coverage.png', dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    monthly = data.assign(month=pd.to_datetime(data.sale_date).dt.to_period('M').dt.to_timestamp()).groupby(['month','locality']).price_usd.median().unstack()
    monthly.plot(ax=ax, color=['#167A78', '#CA7A40'])
    ax.set(xlabel='Sale month', ylabel='Median sale price (USD)', title='Monthly medians of observed sales')
    fig.tight_layout()
    fig.savefig(out / '02_trend.png', dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    sns.histplot(data=data, x='price_usd', hue='locality', bins=45, log_scale=True, ax=ax)
    ax.set(xlabel='Sale price (USD, log scale)', ylabel='Transactions', title='Price distribution in the collected sample')
    fig.tight_layout()
    fig.savefig(out / '03_distribution.png', dpi=170)
    plt.close(fig)
    scores = pd.read_csv(ARTIFACTS / 'validation_metrics.csv').sort_values('rmse')
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.barh(scores.model, scores.rmse, color='#167A78')
    ax.set(xlabel='Validation RMSE (USD)', title='Model selection using 2024 only')
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out / '04_models.png', dpi=170)
    plt.close(fig)
    predictions = pd.read_csv(ARTIFACTS / 'test_predictions.csv')
    sample = predictions.sample(min(1800, len(predictions)), random_state=42)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    sns.scatterplot(data=sample, x='price_usd', y='predicted_usd', hue='state', s=12, alpha=0.45, ax=ax)
    limit = max(sample.price_usd.max(), sample.predicted_usd.max())
    ax.plot([0, limit], [0, limit], '--', color='gray')
    ax.set(xlabel='Actual sale price (USD)', ylabel='Predicted sale price (USD)', title='Holdout 2025–2026; sample of 1,800 records')
    fig.tight_layout()
    fig.savefig(out / '05_test.png', dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    main()

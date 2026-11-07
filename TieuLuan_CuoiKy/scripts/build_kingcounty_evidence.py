"""Generate reproducible statistical figures and literal chart data for the report/deck."""
import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'real_estate_ai'))
from backend.kingcounty import ARTIFACTS, LABELS, temporal_partitions


def main():
    meta = json.loads((ARTIFACTS / 'metadata.json').read_text(encoding='utf-8'))
    data = pd.read_csv(ARTIFACTS / 'sales_clean.csv', dtype={'id': str, 'zipcode': str}, parse_dates=['sale_date'])
    train = temporal_partitions(data)['train']
    tests = pd.read_csv(ARTIFACTS / 'test_predictions.csv')
    scores = pd.read_csv(ARTIFACTS / 'validation_metrics.csv')
    importance = pd.read_csv(ARTIFACTS / 'feature_importance.csv', index_col=0).iloc[:, 0]
    example = json.loads((ARTIFACTS / 'examples.json').read_text(encoding='utf-8'))[0]
    rate = meta['exchange_rate']['usd_vnd']
    out = ARTIFACTS / 'charts'
    out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.labelcolor': '#243b43', 'text.color': '#243b43',
                         'axes.titleweight': 'bold', 'figure.facecolor': '#f7f8f3',
                         'axes.facecolor': '#f7f8f3', 'savefig.facecolor': '#f7f8f3'})
    green, copper, blue = '#17664f', '#b47b49', '#577f98'
    evidence = {'dataset_sha256': meta['dataset_sha256'], 'eda_population': 'train only',
                'exchange_rate': rate, 'example': example, 'metadata': meta}

    def save(fig, name):
        fig.savefig(out / (name + '.png'), dpi=180, bbox_inches='tight')
        plt.close(fig)

    sample = train.sample(min(1500, len(train)), random_state=42)
    fig, ax = plt.subplots(figsize=(8.4, 4.8), layout='constrained')
    ax.scatter(sample.living_m2, sample.price * rate / 1e9, s=12, alpha=.35, color=green, edgecolors='none')
    ax.set(xlabel='Diện tích ở (m²)', ylabel='Giá bán quy đổi (tỷ VND)', title='Diện tích lớn thường đi cùng giá cao hơn')
    ax.set_ylim(bottom=0)
    save(fig, 'area_price')
    evidence['area_scatter'] = {'x': sample.living_m2.tolist(), 'y': (sample.price * rate / 1e9).tolist()}
    evidence['correlations'] = train[['living_m2', 'lot_m2', 'bedrooms', 'bathrooms', 'grade', 'view', 'price']].corr().price.drop('price').to_dict()

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.6), layout='constrained')
    room_data = {}
    for ax, key, title in zip(axes, ['bedrooms', 'bathrooms'], ['Phòng ngủ', 'Phòng tắm quy đổi']):
        group = train.groupby(key).price.agg(['median', 'size'])
        group = group[group['size'] >= 50]
        room_data[key] = {'categories': [str(x) for x in group.index],
                          'median_billion_vnd': (group['median'] * rate / 1e9).tolist(),
                          'counts': group['size'].tolist()}
        ax.bar(range(len(group)), group['median'] * rate / 1e9, color=green if key == 'bedrooms' else copper)
        ax.set_xticks(range(len(group)), [str(x) for x in group.index], rotation=45 if key == 'bathrooms' else 0)
        ax.set(title=title, ylabel='Giá trung vị (tỷ VND)')
    save(fig, 'bedrooms_bathrooms')
    evidence['rooms'] = room_data

    quality = {}
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.4), layout='constrained')
    for ax, key, title in zip(axes, ['grade', 'view', 'waterfront'], ['Chất lượng xây dựng', 'Cảnh quan', 'Ven nước']):
        group = train.groupby(key).price.agg(['median', 'size'])
        group = group[group['size'] >= 20]
        labels = [str(int(x)) for x in group.index]
        if key == 'waterfront': labels = ['Không' if x == 0 else 'Có' for x in group.index]
        ax.bar(labels, group['median'] * rate / 1e9, color=green)
        ax.set(title=title, ylabel='Giá trung vị (tỷ VND)')
        quality[key] = {'categories': labels, 'values': (group['median'] * rate / 1e9).tolist(), 'counts': group['size'].tolist()}
    save(fig, 'quality_environment')
    evidence['quality'] = quality

    fig, ax = plt.subplots(figsize=(8.4, 5.4), layout='constrained')
    points = ax.scatter(sample.longitude, sample.latitude, c=np.log10(sample.price), cmap='viridis', s=9, alpha=.7)
    fig.colorbar(points, ax=ax, label='log10(giá USD)')
    ax.set(title='Vị trí và giá giao dịch trong tập train', xlabel='Kinh độ', ylabel='Vĩ độ')
    save(fig, 'location')
    evidence['location'] = {'x': sample.longitude.tolist(), 'y': sample.latitude.tolist(), 'price_usd': sample.price.tolist()}

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.6), layout='constrained')
    amenities = {}
    for ax, kind, label in zip(axes, ['school', 'convenience'], ['Trường học', 'Cửa hàng tiện lợi']):
        if train[kind + '_km'].notna().any():
            bucket = pd.cut(train[kind + '_km'], [0, .5, 1, 2, np.inf], labels=['≤0,5 km', '0,5–1 km', '1–2 km', '>2 km'], include_lowest=True)
            group = train.groupby(bucket, observed=True).price.agg(['median', 'size'])
            ax.bar([str(x) for x in group.index], group['median'] * rate / 1e9, color=green)
            ax.set(ylabel='Giá trung vị (tỷ VND)', title=label)
            amenities[kind] = {'categories': [str(x) for x in group.index], 'values': (group['median'] * rate / 1e9).tolist(), 'counts': group['size'].tolist()}
        else:
            ax.axis('off')
            ax.text(.5, .6, label, ha='center', fontsize=15, weight='bold', transform=ax.transAxes)
            ax.text(.5, .35, 'Chưa có snapshot lịch sử đã xác minh\nKhông suy ra khoảng cách từ mã bưu chính\nKhông đưa số liệu giả vào mô hình', ha='center', va='center', fontsize=11, transform=ax.transAxes)
    fig.suptitle('Đối chiếu tiện ích cần dữ liệu vị trí có nguồn')
    save(fig, 'amenities')
    evidence['amenities'] = amenities

    fig, ax = plt.subplots(figsize=(8.4, 4.7), layout='constrained')
    labels = [str(x).replace('XGBoost ', 'XGB ') for x in scores.model]
    ax.barh(labels[::-1], (scores.rmse_usd * rate / 1e9).to_numpy()[::-1], color=green)
    ax.set(xlabel='RMSE validation (tỷ VND quy đổi)', title='Chọn mô hình bằng validation')
    save(fig, 'model_comparison')
    evidence['validation'] = {'categories': scores.model.tolist(), 'rmse_usd': scores.rmse_usd.tolist(), 'mae_usd': scores.mae_usd.tolist()}

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), layout='constrained')
    axes[0].scatter(tests.price * rate / 1e9, tests.predicted_usd * rate / 1e9, s=8, alpha=.35, color=green)
    bound = max(tests.price.max(), tests.predicted_usd.max()) * rate / 1e9
    axes[0].plot([0, bound], [0, bound], '--', color=copper)
    axes[0].set(xlabel='Giá thật (tỷ VND)', ylabel='Dự đoán (tỷ VND)', title='Test theo thời gian')
    axes[1].scatter(tests.predicted_usd * rate / 1e9, (tests.price - tests.predicted_usd) * rate / 1e9, s=8, alpha=.35, color=green)
    axes[1].axhline(0, ls='--', color=copper)
    axes[1].set(xlabel='Dự đoán (tỷ VND)', ylabel='Giá thật trừ dự đoán (tỷ VND)', title='Phần dư còn lớn ở một số căn')
    save(fig, 'test_errors')
    evidence['test_scatter'] = {'x': (tests.price.iloc[::5] * rate / 1e9).tolist(), 'y': (tests.predicted_usd.iloc[::5] * rate / 1e9).tolist()}
    price_groups = pd.cut(tests.price, [0, 300000, 700000, np.inf], labels=['Dưới 300 nghìn USD', '300–700 nghìn USD', 'Từ 700 nghìn USD'])
    segments = []
    for name, group in tests.groupby(price_groups, observed=True):
        segments.append({'segment': str(name), 'n': len(group), 'mae_usd': float(group.absolute_error_usd.mean()), 'within20': float(group.ape.le(.2).mean())})
    evidence['segments'] = segments

    fig, ax = plt.subplots(figsize=(8.4, 5), layout='constrained')
    top = importance.head(10).sort_values()
    ax.barh([LABELS[x] for x in top.index], top, color=green)
    ax.set(xlabel='Trung bình |TreeSHAP| theo log(1 + USD)', title='Đặc trưng quan trọng trên validation')
    save(fig, 'importance')
    evidence['importance'] = {'categories': [LABELS[x] for x in importance.head(10).index], 'values': importance.head(10).tolist()}

    effects = example['result']['explanations'][:9][::-1]
    fig, ax = plt.subplots(figsize=(8.4, 5), layout='constrained')
    ax.barh([x['label'] for x in effects], [x['log_contribution'] for x in effects], color=[green if x['log_contribution'] >= 0 else copper for x in effects])
    ax.axvline(0, color='#536a70', lw=.8)
    ax.set(xlabel='Đóng góp log(1 + USD)', title='Giải thích căn nhà test được chọn theo giá trung vị')
    save(fig, 'example_explanation')

    train = train.assign(price_per_m2=train.price * rate / train.living_m2)
    groups = pd.cut(train.living_m2, [0, 100, 150, 200, 300, np.inf], labels=['<100', '100–150', '150–200', '200–300', '≥300'])
    per_m2 = train.groupby(groups, observed=True).price_per_m2.agg(['median', 'size'])
    fig, ax = plt.subplots(figsize=(8.4, 4.6), layout='constrained')
    ax.bar([str(x) for x in per_m2.index], per_m2['median'] / 1e6, color=green)
    ax.set(xlabel='Nhóm diện tích ở (m²)', ylabel='Giá trung vị trên m² (triệu VND)', title='Giá mỗi m² thay đổi theo nhóm diện tích')
    save(fig, 'price_per_m2')
    evidence['price_per_m2'] = {'categories': [str(x) for x in per_m2.index], 'values': (per_m2['median'] / 1e6).tolist(), 'counts': per_m2['size'].tolist()}

    fig, ax = plt.subplots(figsize=(8.4, 4.6), layout='constrained')
    ix = np.arange(50)
    rows = tests.iloc[:50]
    ax.vlines(ix, rows.lower_usd * rate / 1e9, rows.upper_usd * rate / 1e9, color=green, alpha=.6)
    inside = (rows.price >= rows.lower_usd) & (rows.price <= rows.upper_usd)
    ax.scatter(ix, rows.price * rate / 1e9, c=np.where(inside, green, copper), s=17)
    ax.set(xlabel='50 dòng test đầu theo thứ tự thời gian', ylabel='Giá (tỷ VND)', title='Khoảng dự đoán và giá bán quan sát')
    save(fig, 'calibration')
    (ARTIFACTS / 'evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Created 11 figures and editable chart data:', out)


if __name__ == '__main__':
    main()

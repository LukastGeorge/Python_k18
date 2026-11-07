"""Build reproducible plots and slide chart data from training/holdout artifacts."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'real_estate_ai'))
WORK = ROOT.parent / '.tools/kaggle-vietnam-20261107'
os.environ.setdefault('MPLCONFIGDIR', str(WORK / 'mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator, ScalarFormatter
import numpy as np
import pandas as pd
from backend.vietnam import (ARTIFACTS as ART, FEATURES, LABELS, load_bundle,
                             estimate_property, json_write)

plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11,
    'axes.spines.top':False, 'axes.spines.right':False,
    'axes.labelcolor':'#172c36', 'text.color':'#172c36', 'axes.titleweight':'bold',
    'figure.facecolor':'#f7f8f3', 'axes.facecolor':'#f7f8f3', 'savefig.facecolor':'#f7f8f3'})
COLORS = ['#17664f', '#b47b49']
CHARTS = ART / 'charts'
CHARTS.mkdir(exist_ok=True)
M = load_bundle()['metadata']
data = pd.read_csv(ART / 'listings_clean.csv.gz', dtype={'district_name':str,'ward_name':str})
splits = json.loads((ART / 'split.json').read_text(encoding='utf-8'))
train = data[data.listing_id.isin(splits['train'])].copy()
test = pd.read_csv(ART / 'test_predictions.csv', dtype={'district_name':str,'ward_name':str})
E = {'metadata': M}


def save(fig, name):
    fig.tight_layout(pad=1.8, rect=(0,0,1,.95) if fig._suptitle else (0,0,1,1))
    fig.savefig(CHARTS / (name + '.png'), dpi=155, bbox_inches='tight', pad_inches=.12)
    plt.close(fig)


# Fix examples by a declared rule: median observed asking price among complete
# bedroom/bathroom records; never select examples using prediction error.
examples = []
for city, group in test.groupby('province_name'):
    complete = group.dropna(subset=['bedroom_count','bathroom_count'])
    if len(complete) >= 10:
        group = complete
    group = group[group.district_name.isin(M['locations'][city])]
    row = group.iloc[np.argsort(group.price.to_numpy())[len(group)//2]]
    location = M['locations'].get(city, {}).get(row.district_name)
    if not location:
        continue
    values = {name: None if pd.isna(row[name]) else row[name] for name in FEATURES}
    if values['ward_name'] not in location['wards']:
        values['ward_name'] = 'Không rõ'
    examples.append({'label':f'{city} · {row.district_name}',
        'input':values | {'reference_id':row.listing_id}, 'asking_vnd':float(row.price),
        'published_at':None})
json_write(ART / 'examples.json', examples)
E['examples'] = [{'input':example, 'result':estimate_property(example['input'])} for example in examples]

fig, axes = plt.subplots(1, 2, figsize=(11,4.5))
E['area_scatter'] = []
for index, city in enumerate(['Hồ Chí Minh','Hà Nội']):
    group = train[train.province_name == city]
    sample = group.sample(min(1200,len(group)), random_state=42)
    axes[index].scatter(sample.area, sample.price/1e9, s=9, alpha=.32, c=COLORS[index], edgecolors='none')
    axes[index].set(xscale='log',yscale='log',xlabel='Diện tích khai báo (m², thang log)',
                    ylabel='Giá rao (tỷ VND, thang log)',title=city)
    axes[index].set_xticks([20,50,100,200,500])
    axes[index].set_xlim(15,600)
    axes[index].xaxis.set_major_formatter(ScalarFormatter())
    axes[index].xaxis.set_minor_locator(NullLocator())
    axes[index].yaxis.set_minor_locator(NullLocator())
    E['area_scatter'].append({'city':city,'x':sample.area.tolist(),'y':(sample.price/1e9).tolist()})
fig.suptitle('Diện tích và giá rao bán · Mẫu cố định từ tập train', y=1.02)
save(fig, 'area_price')

fig, axes = plt.subplots(1,2,figsize=(11,4.5))
E['rooms'] = {}
for axis, feature in zip(axes, ['bedroom_count','bathroom_count']):
    E['rooms'][feature] = []
    for index, city in enumerate(['Hồ Chí Minh','Hà Nội']):
        group = train[(train.province_name==city) & train[feature].between(1,6)]
        summary = group.groupby(feature).price.agg(['median','count'])
        summary = summary[summary['count'] >= 50]
        axis.plot(summary.index, summary['median']/1e9, marker='o',label=city,c=COLORS[index])
        E['rooms'][feature].append({'city':city,'categories':[str(int(x)) for x in summary.index],
            'median_billion':(summary['median']/1e9).tolist(),'counts':summary['count'].tolist()})
    axis.set(xlabel=LABELS[feature],ylabel='Giá rao trung vị (tỷ VND)',title=LABELS[feature])
    axis.legend(frameon=False,fontsize=9)
fig.suptitle('Nhà ở theo nguồn · Mỗi nhóm có ≥ 50 tin train',y=1.02)
save(fig,'rooms')

fig, axes = plt.subplots(1,2,figsize=(11,5))
E['districts'] = []
for index, city in enumerate(['Hồ Chí Minh','Hà Nội']):
    group = train[train.province_name==city].copy()
    group['unit'] = group.price/group.area/1e6
    summary = group.groupby('district_name').unit.agg(['median','count'])
    summary = summary[summary['count'] >= 100].sort_values('median').tail(7)
    axes[index].barh(summary.index,summary['median'],color=COLORS[index])
    axes[index].set(xlabel='Trung vị triệu VND/m² khai báo',title=city)
    E['districts'].append({'city':city,'categories':summary.index.tolist(),
        'median_million':summary['median'].tolist(),'counts':summary['count'].tolist()})
fig.suptitle('Nhà ở theo nguồn · Quận/huyện có đơn giá cao trong tập train',y=1.02)
save(fig,'districts')

fig, ax = plt.subplots(figsize=(10,4.7))
comparison = M['validation_comparison']
ax.barh([row['model'] for row in comparison], [row['rmse_vnd']/1e9 for row in comparison],color=[COLORS[1], '#6d8f83', COLORS[0]])
ax.set(xlabel='RMSE validation (tỷ VND, thấp hơn tốt hơn)',title='So sánh trên cùng validation theo nhóm địa chỉ và diện tích')
save(fig,'model_comparison')

importance = json.loads((ART / 'importance.json').read_text(encoding='utf-8'))
importance.sort(key=lambda x:x['mean_abs_log_contribution'])
E['importance'] = importance
fig, ax = plt.subplots(figsize=(10,5))
ax.barh([LABELS[x['feature']] for x in importance], [x['mean_abs_log_contribution'] for x in importance],color=COLORS[0])
ax.set(xlabel='Trung bình |TreeSHAP| trên thang log(VND)',title='Vai trò đặc trưng · 600 tin calibration chưa dùng fit')
save(fig,'importance')

fig, axes = plt.subplots(1,2,figsize=(11,4.5))
sample = test.sample(2000,random_state=42)
axes[0].scatter(sample.price/1e9,sample.predicted_vnd/1e9,s=8,alpha=.3,c=COLORS[0],edgecolors='none')
plot_low = max(.1,float(min(sample.price.min(),sample.predicted_vnd.min()))/1e9*.85)
plot_high = float(max(sample.price.max(),sample.predicted_vnd.max()))/1e9*1.1
axes[0].plot([plot_low,plot_high],[plot_low,plot_high],c=COLORS[1],lw=1)
axes[0].set_xlim(plot_low,plot_high);axes[0].set_ylim(plot_low,plot_high)
axes[0].set(xscale='log',yscale='log',xlabel='Giá rao nguồn (tỷ VND)',ylabel='Dự đoán (tỷ VND)',title='Giá nguồn và dự đoán · 2.000 tin test')
error=(test.predicted_vnd-test.price)/test.price*100
axes[1].hist(error.clip(-100,200),bins=60,color=COLORS[0])
axes[1].set(xlabel='Sai số tương đối (%), cắt hiển thị −100 đến 200',ylabel='Số tin test',title='Phân bố sai số có dấu')
save(fig,'test_errors')

fig, ax = plt.subplots(figsize=(10,4.5))
missing = train[['area','bedroom_count','bathroom_count','floor_count','frontage_width','road_width']].isna().mean().sort_values()
E['missingness'] = [{'feature':name,'fraction':float(value)} for name,value in missing.items()]
ax.barh([LABELS[name] for name in missing.index],missing.values*100,color=COLORS[1])
ax.set(xlabel='Tỷ lệ thiếu trên train (%)',title='Độ đầy đủ của thông tin kết cấu')
save(fig,'missingness')

example = next(x for x in E['examples'] if x['input']['input']['province_name']=='Hồ Chí Minh')
E['main_example'] = example
effects = sorted(example['result']['explanations'], key=lambda x:abs(x['log_contribution']))
fig, ax = plt.subplots(figsize=(10,5))
ax.barh([x['label'] for x in effects], [x['log_contribution'] for x in effects],color=[COLORS[0] if x['log_contribution']>=0 else COLORS[1] for x in effects])
ax.axvline(0,color='#73817b',lw=.8)
ax.set(xlabel='Đóng góp TreeSHAP trên thang log(VND)',title='Giải thích dự đoán căn nhà ví dụ tại TP.HCM')
save(fig,'example_explanation')

E['population'] = train.groupby('province_name').agg(n=('price','size'),median_price=('price','median')).reset_index().to_dict('records')
fig, axes = plt.subplots(1,2,figsize=(11,4.5))
counts, edges = np.histogram(train.price/1e9,bins=25)
axes[0].hist(train.price/1e9,bins=edges,color=COLORS[0])
axes[0].set(xlabel='Giá rao (tỷ VND)',ylabel='Số tin train',title='Phân bố giá rao')
axes[1].hist(np.log(train.price/1e9),bins=25,color=COLORS[1])
axes[1].set(xlabel='Log tự nhiên của giá theo tỷ VND',ylabel='Số tin train',title='Giá sau biến đổi log')
E['price_distribution']={'counts':counts.tolist(),'edges_billion':edges.tolist()}
save(fig,'price_distribution')
E['test_scatter'] = {'actual_billion':(sample.price/1e9).tolist(),'predicted_billion':(sample.predicted_vnd/1e9).tolist()}
linear_path = ART / 'linear_analysis.json'
if linear_path.exists():
    linear = json.loads(linear_path.read_text(encoding='utf-8'))
    E['linear'] = linear
    fig, ax = plt.subplots(figsize=(10,5))
    importance = list(reversed(linear['importance']))
    ax.barh([x['label'] for x in importance], [x['delta_rmse_log'] for x in importance],
            color=[COLORS[0] if x['delta_rmse_log'] > 0 else COLORS[1] for x in importance])
    ax.axvline(0,color='#73817b',lw=.8)
    ax.set(xlabel='RMSE log(VND) tăng khi bỏ biến và fit lại OLS',
           title='Độ quan trọng theo hồi quy tuyến tính · Tập validation')
    save(fig,'linear_importance')
    fig, ax = plt.subplots(figsize=(10,4.5))
    coefficients = sorted(linear['numeric_coefficients'],key=lambda x:abs(x['standardized_log_coefficient']))
    ax.barh([x['label'] for x in coefficients], [x['standardized_log_coefficient'] for x in coefficients],
        color=[COLORS[0] if x['standardized_log_coefficient']>=0 else COLORS[1] for x in coefficients])
    ax.axvline(0,color='#73817b',lw=.8)
    ax.set(xlabel='Hệ số log(VND) khi biến số tăng 1 độ lệch chuẩn',title='Hệ số OLS của sáu biến số đã chuẩn hóa')
    save(fig,'linear_coefficients')
    fig, ax = plt.subplots(figsize=(10,4.2))
    curve = linear['subsets']
    ax.plot([x['k'] for x in curve],[x['validation']['rmse_log'] for x in curve],color=COLORS[0],marker='o')
    ax.axvline(linear['selected']['k'],color=COLORS[1],linestyle='--',label='Số biến chọn: '+str(linear['selected']['k']))
    ax.set(xlabel='Số biến gốc trong hồi quy',ylabel='RMSE log(VND) trên validation',title='Chọn số biến theo sai số validation')
    ax.set_xticks(range(1,len(FEATURES)+1));ax.legend(frameon=False)
    save(fig,'linear_selection')
json_write(ART / 'evidence.json', E)
print('Built chart evidence; example',example['input']['label'],example['result']['predicted_vnd'])

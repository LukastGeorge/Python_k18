from pathlib import Path
import json
import unicodedata
import pandas as pd

raw = Path(__file__).resolve().parents[1] / 'real_estate_ai/data/raw/kaggle_vietnam_2024'
data = pd.read_csv(raw / 'vietnam_housing_dataset.csv')
parts = data.Address.map(lambda value: [unicodedata.normalize('NFC', x.strip().rstrip('.')) for x in value.split(',')])
data['city'] = parts.map(lambda x: x[-1])
scope = data[data.city.isin(['Hồ Chí Minh', 'Hà Nội'])].copy()
scope['district'] = parts[scope.index].map(lambda x: x[-2] if len(x)>1 else '')
print('SCOPE', len(scope), 'exact duplicates', scope.duplicated(subset=list(data.columns[:12])).sum())
print('CITIES', scope.city.value_counts().to_dict())
print('QUANTILES', scope.select_dtypes('number').quantile([0,.001,.01,.5,.99,.999,1]).to_string())
print('DISTRICTS', scope.groupby('city').district.value_counts().to_dict())
for col in ['House direction','Balcony direction','Legal status','Furniture state']:
    print(col, scope[col].value_counts(dropna=False).to_dict())
print('SHORT ADDRESS',scope[scope.Address.str.count(',')<3].Address.head(20).tolist())
print('THIRD PART',parts[scope.index].map(lambda x:x[-3] if len(x)>2 else '').value_counts().head(25).to_dict())
print('OUTSIDE SCOPE',len(scope[~scope.Price.between(.5,200) | ~scope.Area.between(15,1000) | ~(scope.Price*1e9/scope.Area).between(5e6,800e6)]))

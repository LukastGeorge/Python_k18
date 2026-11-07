"""Select interpretable input groups using OLS and held-out drop-column evidence."""
import json
from pathlib import Path
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'real_estate_ai'))
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from backend.vietnam import ARTIFACTS as ART, FEATURES, NUMERIC, CATEGORICAL, LABELS, normalize_features, json_write


def model_for(features):
    numbers = [name for name in NUMERIC if name in features]
    categories = [name for name in CATEGORICAL if name in features]
    transformers = []
    if numbers:
        transformers.append(('numeric', Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True)),
                                                  ('scale', StandardScaler())]), numbers))
    if categories:
        transformers.append(('category', OneHotEncoder(drop='first', handle_unknown='ignore',
            min_frequency=20, max_categories=100, sparse_output=True), categories))
    return Pipeline([('features', ColumnTransformer(transformers)), ('model', LinearRegression())])


def design(frame):
    x = normalize_features(frame)
    # Log area describes a proportional size-price relation and reduces skew.
    x['area'] = np.log(x['area'])
    return x


def scores(y, log_hat):
    log_hat = np.asarray(log_hat, float)
    predicted = np.exp(log_hat)
    return {'rmse_log':float(np.sqrt(mean_squared_error(np.log(y),log_hat))),
            'rmse_vnd':float(np.sqrt(mean_squared_error(y,predicted))),
            'r2_vnd':float(r2_score(y,predicted)),
            'median_ape':float(np.median(np.abs(predicted-y)/y))}


def main():
    warnings.filterwarnings('ignore', message='Found unknown categories')
    data = pd.read_csv(ART / 'listings_clean.csv.gz',dtype={'district_name':str,'ward_name':str})
    splits = json.loads((ART / 'split.json').read_text(encoding='utf-8'))
    train, val = [data[data.listing_id.isin(splits[key])] for key in ['train','validation']]
    xtrain, xval = design(train), design(val)
    ytrain, yval = train.price.to_numpy(),val.price.to_numpy()
    full = model_for(FEATURES).fit(xtrain,np.log(ytrain))
    full_score = scores(yval,full.predict(xval))
    print('OLS full',full_score,flush=True)
    important = []
    for name in FEATURES:
        reduced = model_for([feature for feature in FEATURES if feature != name]).fit(xtrain,np.log(ytrain))
        reduced_score = scores(yval,reduced.predict(xval))
        important.append({'feature':name,'label':LABELS[name],
            'delta_rmse_log':reduced_score['rmse_log']-full_score['rmse_log'],
            'delta_rmse_vnd':reduced_score['rmse_vnd']-full_score['rmse_vnd'],
            'without':reduced_score})
        print('Without',name,important[-1]['delta_rmse_log'],flush=True)
    important.sort(key=lambda row:row['delta_rmse_log'],reverse=True)
    ranked = [row['feature'] for row in important]
    subsets = []
    for k in range(1,len(ranked)+1):
        selected = ranked[:k]
        candidate = model_for(selected).fit(xtrain,np.log(ytrain))
        subsets.append({'k':k,'features':selected,'validation':scores(yval,candidate.predict(xval))})
    best = min(subsets,key=lambda row:row['validation']['rmse_log'])
    # Predeclared tolerance rewards a simpler linear model within 1% of the best.
    chosen = next(row for row in subsets if row['validation']['rmse_log'] <= best['validation']['rmse_log']*1.01)
    numbers = full.named_steps['features'].get_feature_names_out()
    coefficients = dict(zip(numbers,full.named_steps['model'].coef_))
    numeric_coefficients = [{'feature':name,'label':LABELS[name] + (' (log)' if name=='area' else ''),
        'standardized_log_coefficient':float(coefficients['numeric__'+name])} for name in NUMERIC]
    result = {'raw_column_count':12,'raw_predictor_count':11,'screened_raw_predictor_count':10,
        'candidate_input_count':len(FEATURES),
        'encoded_column_count':len(numbers),'numeric_count':len(NUMERIC),'categorical_count':len(CATEGORICAL),
        'method':'Ordinary least squares of log(VND); log(area), train median imputation, missing indicators, standardized numeric inputs, grouped one-hot categories.',
        'importance_method':'Refit OLS for each candidate input group, omitting that group; rank increase in log RMSE on the same validation set.',
        'selection_rule':'Smallest prefix of importance ranking within 1% of the minimum validation log RMSE across prefixes.',
        'full_validation':full_score,'importance':important,'numeric_coefficients':numeric_coefficients,
        'subsets':subsets,'selected':chosen,
        'excluded_raw_columns':{'Price':'Nhãn y theo tỷ VND; nhân 1e9. Không được đưa vào X.',
            'Balcony direction':'Thiếu trên 80% ở tập train nên loại theo ngưỡng sàng lọc đã định.'},
        'address_transformation':'Address không được đưa nguyên văn vào mô hình; tách thành thành phố, quận/huyện, phường/xã. Không suy đoán loại nhà hoặc ngày đăng.',
        'caveats':['Độ quan trọng thuộc mô hình tuyến tính và cách chia dữ liệu này, không phải tác động nhân quả.',
            'Các biến địa bàn lồng nhau và số phòng/diện tích tương quan nên có thể chia sẻ thông tin.',
            'Biểu đồ hệ số chỉ so sánh sáu biến số đã chuẩn hóa; nhóm danh mục xếp hạng bằng bỏ biến rồi fit lại.',
            'Danh sách tuyến tính là thí nghiệm chọn biến riêng; mô hình phục vụ XGBoost dùng 12 đầu vào sau sàng lọc để học tương tác phi tuyến.',
            'Không có ngày đăng; chia theo nhóm địa chỉ và diện tích, không được diễn giải là kiểm thử ở thời kỳ tương lai.']}
    json_write(ART / 'linear_analysis.json',result)
    print('Selected',chosen,flush=True)


if __name__=='__main__':
    main()

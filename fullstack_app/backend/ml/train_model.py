import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# 1. Generate Synthetic Data
# We create a small dataset mapping soil/season/region to crops
data = {
    'soil_type': [
        'clay', 'clay', 'clay', 'loam', 'loam', 'loam', 'sandy', 'sandy', 'silt', 'silt',
        'clay', 'loam', 'sandy', 'silt', 'clay', 'loam', 'sandy', 'silt'
    ],
    'season': [
        'kharif', 'rabi', 'zaid', 'kharif', 'rabi', 'zaid', 'kharif', 'rabi', 'kharif', 'rabi',
        'winter', 'winter', 'winter', 'winter', 'summer', 'summer', 'summer', 'summer'
    ],
    'region': [
        'dhaka', 'dhaka', 'dhaka', 'rajshahi', 'rajshahi', 'rajshahi', 'cumilla', 'cumilla', 'barisal', 'barisal',
        'dhaka', 'rajshahi', 'cumilla', 'barisal', 'dhaka', 'rajshahi', 'cumilla', 'barisal'
    ],
    'crop': [
        'Rice', 'Wheat', 'Watermelon', 'Mango', 'Potato', 'Jute', 'Peanut', 'Mustard', 'Rice', 'Wheat',
        'Wheat', 'Potato', 'Mustard', 'Wheat', 'Rice', 'Mango', 'Watermelon', 'Rice'
    ]
}

# Expand dataset to make it robust (simple replication for demo)
df = pd.DataFrame(data)
df = pd.concat([df]*50, ignore_index=True) # Duplicate 50 times

print("Dataset shape:", df.shape)
print(df.head())

# 2. Preprocessing
le_soil = LabelEncoder()
le_season = LabelEncoder()
le_region = LabelEncoder()
le_crop = LabelEncoder()

df['soil_type_encoded'] = le_soil.fit_transform(df['soil_type'])
df['season_encoded'] = le_season.fit_transform(df['season'])
df['region_encoded'] = le_region.fit_transform(df['region'])
df['crop_encoded'] = le_crop.fit_transform(df['crop'])

X = df[['soil_type_encoded', 'season_encoded', 'region_encoded']]
y = df['crop_encoded']

# 3. Train Model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

# 4. Save Model and Encoders
# Use absolute path relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(current_dir, 'saved_models')
os.makedirs(output_dir, exist_ok=True)

joblib.dump(model, os.path.join(output_dir, 'crop_model.pkl'))
joblib.dump(le_soil, os.path.join(output_dir, 'le_soil.pkl'))
joblib.dump(le_season, os.path.join(output_dir, 'le_season.pkl'))
joblib.dump(le_region, os.path.join(output_dir, 'le_region.pkl'))
joblib.dump(le_crop, os.path.join(output_dir, 'le_crop.pkl'))

print(f"Model and encoders saved to {output_dir}")

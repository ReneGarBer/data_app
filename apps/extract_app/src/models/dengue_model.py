"""dengue_model.py

Small, self-contained module to train and use a dengue cases forecasting model per municipality.

Functions:
 - train_model(df, ...): trains and returns (or saves) a model pipeline
 - load_model(path): loads saved model dict
 - predict(model_or_path, df): returns predictions aligned with the input rows

Design choices (kept simple and robust):
 - numeric features are scaled; municipality is encoded via OrdinalEncoder
 - default estimator: XGBoost (if installed) else RandomForestRegressor
 - model artifact is saved with joblib as a dict: {"model": estimator, "preprocessor": preproc, "feature_columns": [...], "target_col": ...}
"""
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os
from datetime import datetime

try:
    from xgboost import XGBRegressor
    _HAS_XGB = True
except Exception:
    XGBRegressor = None
    _HAS_XGB = False


def _default_estimator(random_state: int = 42, **kwargs):
    if _HAS_XGB:
        return XGBRegressor(n_estimators=200, random_state=random_state, tree_method='hist', **kwargs)
    else:
        return RandomForestRegressor(n_estimators=200, random_state=random_state, n_jobs=-1, **kwargs)

def _create_preprocessor(numeric_features, categorical_features):
    numeric_transformer = Pipeline(steps=[('scaler', StandardScaler())])
    # municipality is categorical; use OrdinalEncoder (keeps dimensionality small). If you prefer dummies, switch to OneHotEncoder
    categorical_transformer = Pipeline(steps=[('ordinal', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))])

    preprocessor = ColumnTransformer(transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ], remainder='drop')

    return preprocessor

def _make_lag_features(df: pd.DataFrame, target_col: str, group_col: str, date_col: str, lags=(1,2,3), rolling_windows=(3,7)):
    df = df.sort_values([group_col, date_col]).copy()
    for lag in lags:
        df[f'{target_col}_lag_{lag}'] = df.groupby(group_col)[target_col].shift(lag)

    for w in rolling_windows:
        df[f'{target_col}_roll_mean_{w}'] = df.groupby(group_col)[target_col].shift(1).rolling(window=w, min_periods=1).mean().reset_index(level=0, drop=True)

    return df

def _prepare_to_insert(monthly_averages: pd.DataFrame,id_modelo: int =-1) -> pd.DataFrame:

    # Work on a copy to be safe
    ma = monthly_averages.copy()

    # 1) Add id_fecha_prediccion as current UTC date in YYYYMMDD string
    ma['id_fecha_prediccion'] = datetime.utcnow().strftime('%Y%m%d')

    # 2) Rename 'date' -> 'id_desde' and format as YYYYMMDD string
    if 'date' in ma.columns:
        ma['id_desde'] = pd.to_datetime(ma['date']).dt.strftime('%Y%m%d')
        ma = ma.drop(columns=['date'])
    else:
        # if already have a column with month/year, try to build id_desde from year/month
        if {'year', 'month'}.issubset(ma.columns):
            ma['id_desde'] = pd.to_datetime(ma[['year', 'month']].assign(day=1)).dt.strftime('%Y%m%d')
        else:
            raise ValueError("No 'date' column found and can't build id_desde from year/month")

    # 3) Create id_hasta as end-of-month in YYYYMMDD
    ma['id_hasta'] = pd.to_datetime(ma['id_desde'], format='%Y%m%d').dt.to_period('M').dt.to_timestamp('M').dt.strftime('%Y%m%d')

    # 4) Add id_model = 1
    ma['id_modelo'] = id_modelo

    # 5) Rename 'mean' -> 'prediccion' (if present) and ensure integer
    if 'mean' in ma.columns:
        ma = ma.rename(columns={'mean': 'prediccion'})
        try:
            ma['prediccion'] = ma['prediccion'].astype(int)
        except Exception:
            # if conversion fails, leave as-is
            pass
    elif 'prediccion' not in ma.columns:
        # if neither present, create prediccion from number of rows per group if sensible
        if {'id_region', 'id_desde'}.issubset(ma.columns):
            # fallback: set prediccion = 1
            ma['prediccion'] = id

    #drop columns
    ma = ma.drop(columns=['count','std','year','month'])

    # Optional: reorder columns to a canonical layout
    cols_order = [ 'id_fecha_prediccion', 'id_desde', 'id_hasta', 'id_modelo', 'prediccion','id_region']
    other_cols = [c for c in ma.columns if c not in cols_order]
    ma = ma[cols_order + other_cols]

    # Replace monthly_averages in the notebook with the transformed frame
    return ma

def prepare_features(df: pd.DataFrame,
                     target_col: str = 'cases',
                     municipality_col: str = 'municipio',
                     date_col: str = 'date',
                     climate_cols: Optional[list] = None,
                     create_time_features: bool = True,
                     lags=(1,2,3),
                     rolling_windows=(3,7)) -> pd.DataFrame:
    """Return dataframe ready for training: includes lag features and selected climate columns.

    Requirements: df must contain target_col, municipality_col and date_col.
    date_col should be parseable as datetime.
    """

    df = df.copy()
    # parse date
    df[date_col] = pd.to_datetime(df[date_col])

    # ensure sorted
    df = df.sort_values([municipality_col, date_col])

    # create time features
    if create_time_features:
        df['month'] = df[date_col].dt.month
        df['weekofyear'] = df[date_col].dt.isocalendar().week.astype(int)

    # create lag and rolling features for target
    df = _make_lag_features(df, target_col, municipality_col, date_col, lags=lags, rolling_windows=rolling_windows)

    # choose climate features
    if climate_cols is None:
        # pick numeric columns excluding target and identifiers
        climate_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in [target_col]]

    # drop rows with NA in lag features (these are caused by shifting)
    lag_cols = [f'{target_col}_lag_{lag}' for lag in lags] + [f'{target_col}_roll_mean_{w}' for w in rolling_windows]
    keep_cols = [municipality_col, date_col, target_col] + climate_cols + ['month', 'weekofyear'] + lag_cols
    keep_cols = [c for c in keep_cols if c in df.columns]

    df = df[keep_cols].dropna()

    df_train,df_test = train_test_split(df, test_size=0.2, shuffle=False)

    return df_train,df_test

def train_model(df: pd.DataFrame,
                target_col: str = 'cases',
                municipality_col: str = 'municipio',
                date_col: str = 'date',
                climate_cols: Optional[list] = None,
                test_size: float = 0.2,
                random_state: int = 42,
                model_path: Optional[str] = None,
                estimator_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Train and optionally save a model. Returns a dict with trained artifacts and metrics.

    model_path: if provided, the artifact dict will be saved to this file via joblib.
    """
    estimator_kwargs = estimator_kwargs or {}
    # Prepare features
    df_prepared = prepare_features(df, target_col, municipality_col, date_col, climate_cols)

    # feature columns
    feature_cols = [c for c in df_prepared.columns if c not in [target_col, date_col]]

    # separate features and target
    X = df_prepared[feature_cols]
    y = df_prepared[target_col]

    # identify numeric and categorical features
    numeric_feats = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_feats = [c for c in X.columns if c not in numeric_feats]

    preprocessor = _create_preprocessor(numeric_feats, categorical_feats)

    estimator = _default_estimator(random_state=random_state, **estimator_kwargs)

    pipe = Pipeline(steps=[('preproc', preprocessor), ('model', estimator)])

    # train/test split (random split keeps municipalities mixed; for time-aware split, user can call outside)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)

    metrics = {
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'mse': float(mean_squared_error(y_test, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }

    artifact = {
        'pipeline': pipe,
        'feature_columns': feature_cols,
        'target_col': target_col,
        'municipality_col': municipality_col,
        'date_col': date_col,
        'metrics': metrics
    }

    if model_path:
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(artifact, model_path)

    return artifact

def load_model(checkpoint_path: str, map_location: str = "cpu") -> TemporalFusionTransformer:
    try:
        model = TemporalFusionTransformer.load_from_checkpoint(
            checkpoint_path,
            map_location=map_location
        )
        model.eval()  # Set to evaluation mode
        return model
    except Exception as e:
        raise Exception(f"Error loading model from {checkpoint_path}: {str(e)}")

def predict(model_or_path: Any, df_prepared: pd.DataFrame) -> pd.Series:
    """Return a Series of predictions aligned with input df rows.

    model_or_path can be a path to saved artifact (joblib) or the artifact dict returned by train_model.
    Input df should contain the same columns used in prepare_features (date/municipio/climate cols) and may be raw.
    """
    if isinstance(model_or_path, str):
        artifact = load_model(model_or_path)
    else:
        artifact = model_or_path

    pipe = artifact['pipeline']
    target_col = artifact['target_col']
    municipality_col = artifact['municipality_col']
    date_col = artifact['date_col']

    # Prepare features using same logic: keep climate columns inferred from artifact
    
    X = df_prepared[artifact['feature_columns']]

    preds = pipe.predict(X)

    # Return aligned with input prepared df index
    preds_series = pd.Series(preds, index=df_prepared.index, name='predicted_' + target_col)

    return preds_series

def tft_predict(model: TemporalFusionTransformer, 
                df: pd.DataFrame,
                target_col: str = 'casos',
                municipality_col: str = 'id_region',
                date_col: str = 'fin_de_mes',
                max_prediction_length: int = 7,
                min_prediction_length: int = 1,
                max_encoder_length: int = 30,
                min_encoder_length: int = 1,
                batch_size: int = 64) -> pd.DataFrame:
    """Make predictions using a trained TemporalFusionTransformer.
    
    Parameters
    ----------
    model : TemporalFusionTransformer
        Trained TFT model from tft_train_model
    df : pd.DataFrame
        Input data with municipality_col, date_col and features
    target_col : str
        Name of the target column
    municipality_col : str
        Name of the municipality/region column
    date_col : str
        Name of the date column
    max_prediction_length : int
        Number of future steps to predict
    batch_size : int
        Batch size for prediction
        
    Returns
    -------
    pd.DataFrame
        Predictions with columns [municipality_col, date, predicted_target, step]
    """
    try:
        from pytorch_forecasting import TimeSeriesDataSet
        from pytorch_forecasting.data import GroupNormalizer
    except ImportError as e:
        raise ImportError("tft_predict requires pytorch_forecasting to be installed") from e

    # Ensure date column is datetime
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Create time index required by TimeSeriesDataSet
    df = df.sort_values([municipality_col, date_col])
    df['time_idx'] = df.groupby(municipality_col).cumcount()
    
    # Get numeric features (excluding target and time_idx)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    time_varying_reals = [c for c in numeric_cols if c not in [target_col, 'time_idx']]
    
    # Recreate training dataset structure (needed for prediction)
    dataset = TimeSeriesDataSet(
        df,
        time_idx='time_idx',
        target=target_col,
        group_ids=[municipality_col],
        static_categoricals=[municipality_col],
        time_varying_known_reals=time_varying_reals,
        time_varying_unknown_reals=[target_col],
        max_encoder_length=model.hparams.max_encoder_length,
        max_prediction_length=max_prediction_length,
        min_encoder_length=min_encoder_length,
        min_prediction_length=min_prediction_length,
        target_normalizer=GroupNormalizer(groups=[municipality_col]),
        allow_missing_timesteps=True
    )
    
    out_rows = []
    groups = df[municipality_col].unique()
    
    for g in groups:
        group_df = df[df[municipality_col] == g].sort_values('time_idx')
        if len(group_df) < model.hparams.max_encoder_length:
            continue
            
        # Get last window of data for prediction
        last_data = group_df.iloc[-model.hparams.max_encoder_length:]
        last_date = pd.to_datetime(last_data[date_col].iloc[-1])
        
        # Create prediction dataset
        pred_dataset = TimeSeriesDataSet.from_dataset(dataset, last_data, predict=True, stop_randomization=True)##
        pred_loader = pred_dataset.to_dataloader(train=False, batch_size=batch_size, num_workers=3)
        
        # Make prediction
        raw_predictions = model.predict(pred_loader)
        
        # Convert predictions to numpy if needed
        if hasattr(raw_predictions, 'numpy'):
            predictions = raw_predictions.numpy()
        elif isinstance(raw_predictions, pd.DataFrame):
            predictions = raw_predictions.values
        else:
            predictions = np.asarray(raw_predictions)
            
        # Ensure 2D array and take first sample if multiple
        if predictions.ndim == 2:
            predictions = predictions[0]
            
        # Create rows for each prediction step
        for step, pred in enumerate(predictions[:max_prediction_length], 1):
            pred_date = last_date + pd.Timedelta(days=step)
            out_rows.append({
                municipality_col: g,
                'date': pred_date,
                f'predicted_{target_col}': float(pred),
                'step': step
            })
    
    return pd.DataFrame(out_rows)

def monthly_average_predictions(df_predictions: pd.DataFrame) -> pd.DataFrame:
    monthly_averages = (
    df_predictions.assign(
        year=lambda x: pd.to_datetime(x['date']).dt.year,
        month=lambda x: pd.to_datetime(x['date']).dt.month
    )
    .groupby(['id_region', 'year', 'month'])
    ['predicted_casos']
    .agg(['mean', 'count', 'std'])
    .round(2)
    .reset_index()
    )

    # Add a formatted date column and sort
    monthly_averages['date'] = pd.to_datetime(monthly_averages[['year', 'month']].assign(day=1))
    monthly_averages = monthly_averages.sort_values(['id_region', 'date'])

    return monthly_averages

def tft_evaluate(model: TemporalFusionTransformer,
                 df: pd.DataFrame,
                 target_col: str = 'casos',
                 municipality_col: str = 'id_region',
                 date_col: str = 'fin_de_mes',
                 encoder_length: Optional[int] = None,
                 forecast_horizon: Optional[int] = None,
                 batch_size: int = 64) -> pd.DataFrame:
    """Evaluate a trained TemporalFusionTransformer on historical data.

    The function slides an encoder window across each group's history where a full
    forecast horizon of true targets exists, uses the model to predict the horizon,
    and computes MAE per horizon step and an overall MAE.

    Returns a DataFrame with columns: ['horizon', 'mae', 'count'] and a final
    row with horizon=0 containing overall MAE.
    """
    try:
        from pytorch_forecasting import TimeSeriesDataSet
        from pytorch_forecasting.data import GroupNormalizer
    except Exception as e:
        raise ImportError("tft_evaluate requires pytorch_forecasting to be installed") from e

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values([municipality_col, date_col])
    df['time_idx'] = df.groupby(municipality_col).cumcount()

    # set lengths from model if not provided
    encoder_length = int(encoder_length or getattr(model.hparams, 'max_encoder_length', 30))
    forecast_horizon = int(forecast_horizon or getattr(model.hparams, 'max_prediction_length', 7))

    # numeric covariates except target and time_idx
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    time_varying_reals = [c for c in numeric_cols if c not in [target_col, 'time_idx']]

    # create a dataset object mirroring training structure
    training_ds = TimeSeriesDataSet(
        df,
        time_idx='time_idx',
        target=target_col,
        group_ids=[municipality_col],
        static_categoricals=[municipality_col],
        time_varying_known_reals=time_varying_reals,
        time_varying_unknown_reals=[target_col],
        max_encoder_length=encoder_length,
        max_prediction_length=forecast_horizon,
        target_normalizer=GroupNormalizer(groups=[municipality_col]),
        allow_missing_timesteps=True,
    )

    # accumulators
    errors = np.zeros(forecast_horizon, dtype=float)
    counts = np.zeros(forecast_horizon, dtype=int)

    groups = df[municipality_col].unique()
    for g in groups:
        g_df = df[df[municipality_col] == g].sort_values('time_idx')
        # need at least encoder + horizon rows to evaluate one point
        if len(g_df) < encoder_length + 1:
            continue

        # iterate over valid windows where future truth exists
        for end_pos in range(encoder_length, len(g_df) - forecast_horizon + 1):
            # encoder window is rows [end_pos - encoder_length : end_pos)
            last_window = g_df.iloc[end_pos - encoder_length:end_pos].copy()
            # true future values are the next forecast_horizon rows
            true_future = g_df.iloc[end_pos:end_pos + forecast_horizon][target_col].values
            if len(true_future) < 1:
                continue

            # build predict dataset and loader
            predict_ds = TimeSeriesDataSet.from_dataset(training_ds, last_window, predict=True, stop_randomization=True)
            predict_loader = predict_ds.to_dataloader(train=False, batch_size=batch_size, num_workers=0)

            raw = model.predict(predict_loader)
            if hasattr(raw, 'numpy'):
                arr = raw.numpy()
            elif isinstance(raw, pd.DataFrame):
                arr = raw.values
            else:
                arr = np.asarray(raw)

            if arr.ndim == 2:
                sample = arr[0]
            else:
                sample = arr

            # ensure sample length covers forecast_horizon
            pred = np.asarray(sample[:forecast_horizon], dtype=float)
            # if true_future length shorter than pred slice, truncate
            L = min(len(pred), len(true_future))
            if L == 0:
                continue

            abs_err = np.abs(pred[:L] - np.asarray(true_future[:L], dtype=float))
            errors[:L] += abs_err
            counts[:L] += 1

    # compute per-horizon MAE
    mae_per_horizon = np.divide(errors, counts, out=np.zeros_like(errors), where=counts > 0)

    rows = []
    for h in range(forecast_horizon):
        rows.append({'horizon': h + 1, 'mae': float(mae_per_horizon[h]) if counts[h] > 0 else None, 'count': int(counts[h])})

    # overall mae (weighted by counts)
    total_counts = counts.sum()
    overall_mae = float(errors.sum() / total_counts) if total_counts > 0 else None
    rows.append({'horizon': 0, 'mae': overall_mae, 'count': int(total_counts)})

    return pd.DataFrame(rows)

def tft_train_model(df_prepared: pd.DataFrame,
                          target_col: str = 'cases',
                          municipality_col: str = 'municipio',
                          date_col: str = 'date',
                          climate_cols: Optional[list] = None,
                          max_encoder_length: int = 30,
                          max_prediction_length: int = 7,
                          max_epochs: int = 5,
                          batch_size: int = 64,
                          learning_rate: float = 0.03,
                          random_state: int = 42,
                          device: Optional[str] = None,
                          path: str = "trained_models",
                          name: str = "tft_train_model") -> pd.DataFrame:
    """Train a Temporal Fusion Transformer and return multi-step forecasts.

    Convenience wrapper:
     - prepares features using `prepare_features`
     - builds a TimeSeriesDataSet
     - trains a TFT model (small defaults)
     - predicts per-group and returns a DataFrame with forecasts

    Returns
    -------
    pd.DataFrame
        columns: [municipio, date, predicted_<target_col>, step]
    """
    # lazy imports to provide clearer error messages if libs are missing
    try:
        import torch
        #from pytorch_lightning import Trainer
        from lightning.pytorch import Trainer
        from pytorch_forecasting.data import GroupNormalizer
        from pytorch_forecasting.metrics import QuantileLoss
        from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer
        from pytorch_forecasting.metrics import RMSE
    except Exception as e:
        raise ImportError(
            "tft_train_and_predict requires pytorch, pytorch_lightning and pytorch_forecasting. Install them to use this function."
        ) from e

    if df_prepared.empty:
        raise ValueError("No data available after feature preparation. Check input dataframe and lag settings.")

    # create a time_idx per group (necessary for TimeSeriesDataSet)
    df_prepared = df_prepared.sort_values([municipality_col, date_col]).copy()
    df_prepared['time_idx'] = df_prepared.groupby(municipality_col).cumcount()
    

    # choose covariates: numeric columns except target and time_idx
    numeric_cols = df_prepared.select_dtypes(include=[np.number]).columns.tolist()
    time_varying_reals = [c for c in numeric_cols if c not in [target_col, 'time_idx']]

    static_categoricals = [municipality_col]

    # build TimeSeriesDataSet
    training = TimeSeriesDataSet(
        df_prepared,
        time_idx='time_idx',
        target=target_col,
        group_ids=[municipality_col],
        static_categoricals=static_categoricals,
        time_varying_known_reals=time_varying_reals,
        time_varying_unknown_reals=[target_col],
        max_encoder_length=max_encoder_length,
        max_prediction_length=max_prediction_length,
        target_normalizer=GroupNormalizer(groups=[municipality_col]),
        allow_missing_timesteps=True,
    )

    # dataloader (not used for per-group prediction, but needed to create model)
    train_dataloader = training.to_dataloader(train=True, batch_size=batch_size, num_workers=0)

    # create model
    torch.manual_seed(random_state)
    tft = TemporalFusionTransformer.from_dataset(
        training,
        learning_rate=learning_rate,
        hidden_size=16,
        attention_head_size=4,
        dropout=0.1,
        hidden_continuous_size=8,
        output_size=max_prediction_length,
        loss=QuantileLoss(),
    )
    
    # tft.save_hyperparameters(ignore=['loss', 'logging_metrics'])
    # trainer
    trainer_kwargs = dict(max_epochs=max_epochs, enable_model_summary=False)
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    if device == 'cuda' and torch.cuda.is_available():
        trainer_kwargs['accelerator'] = 'gpu'
        trainer_kwargs['devices'] = 1
    else:
        trainer_kwargs['accelerator'] = 'cpu'

    trainer = Trainer(**trainer_kwargs)

    # fit
    trainer.fit(
         model = tft
        ,train_dataloaders=train_dataloader
    )

    trainer.save_checkpoint(f"{path}{name}.ckpt")

    torch.save(tft.state_dict(),f"{path}{name}.pth")

    return tft

def load_predictions(df: pd.DataFrame, conn,modelo: int = -1, schema: str = "analytics", table: str = "predicciones") -> int:

    df = _prepare_to_insert(df,modelo)

    print(df)

    df.to_sql(
         name = table
        ,con = conn
        ,schema = schema
        ,if_exists= 'append'
        ,index = False
    )   

# if __name__ == '__main__':
#     print('This module provides train_model() and predict() for dengue forecasting.')

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from scipy import stats

class DataProcessor:
    def clean_data(self, data: Dict[str, Any]) -> Dict[str, List[float]]:
        cleaned = {}

        for key, value in data.items():
            if isinstance(value, list):
                # Flatten nested lists
                flat = []
                for v in value:
                    if isinstance(v, (list, tuple)):
                        flat.extend(v)
                    else:
                        flat.append(v)

                # Remove None/NaN and non-informative values
                flat = [v for v in flat if v is not None]

                # Try converting to float where possible (with sensible fallbacks)
                numeric = []
                for v in flat:
                    try:
                        # accept strings like '1,234.56'
                        if isinstance(v, str):
                            v_clean = v.replace(',', '')
                        else:
                            v_clean = v
                        numeric.append(float(v_clean))
                    except Exception:
                        # keep non-numeric values for potential text inspection
                        continue

                if numeric:
                    cleaned[key] = numeric
                else:
                    # keep a preview if cannot convert to numeric
                    cleaned[key] = flat[:50]
            else:
                cleaned[key] = value

        return cleaned

    def compute_statistics(self, data: List[float]) -> Dict[str, float]:
        if not data or len(data) < 1:
            return {}
        arr = np.array(data)
        return {
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "count": int(len(arr))
        }

    def perform_ttest(self, group1: List[float], group2: List[float]) -> Dict[str, Any]:
        if len(group1) < 2 or len(group2) < 2:
            return {"error": "Insufficient data for t-test", "p_value": 1.0, "significant": False, "effect_size": 0.0}
        try:
            t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)
            # Cohen's d
            pooled_sd = np.sqrt(((np.std(group1, ddof=1) ** 2) + (np.std(group2, ddof=1) ** 2)) / 2)
            effect_size = abs(np.mean(group1) - np.mean(group2)) / pooled_sd if pooled_sd > 0 else 0.0
            return {
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "significant": p_value < 0.05,
                "effect_size": float(effect_size)
            }
        except Exception as e:
            return {"error": str(e)}

    def correlation_analysis(self, data: Dict[str, List[float]]) -> Dict[str, Any]:
        try:
            df = pd.DataFrame({k: pd.Series(v) for k, v in data.items()})
            corr_matrix = df.corr()
            strong = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    val = corr_matrix.iat[i, j]
                    if pd.notna(val) and abs(val) > 0.7:
                        strong.append({
                            "var1": corr_matrix.columns[i],
                            "var2": corr_matrix.columns[j],
                            "correlation": float(val)
                        })
            return {"correlation_matrix": corr_matrix.to_dict(), "strong_correlations": strong}
        except Exception as e:
            return {"error": str(e)}
    
    def _find_strong_correlations(self, corr_matrix: pd.DataFrame, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find strong correlations"""
        strong_corrs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > threshold:
                    strong_corrs.append({
                        "var1": corr_matrix.columns[i],
                        "var2": corr_matrix.columns[j],
                        "correlation": float(corr_value)
                    })
        
        return strong_corrs

# Global data processor instance
data_processor = DataProcessor()
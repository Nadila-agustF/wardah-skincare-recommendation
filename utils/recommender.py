import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SkincareRecommender:
    def __init__(self, df: pd.DataFrame):

        if df is None or df.empty:
            raise ValueError("DataFrame kosong, tidak dapat menginisialisasi recommender")

        self.df = df.copy()

        # ===============================
        # VALIDASI KOLOM WAJIB
        # ===============================
        required_columns = ["name", "category", "skin_type"]
        missing_columns = [c for c in required_columns if c not in self.df.columns]
        if missing_columns:
            raise ValueError(f"Kolom yang hilang: {missing_columns}")

        # ===============================
        # NORMALISASI DATA
        # ===============================
        def normalize_list(val):
            if isinstance(val, list):
                return [str(v).lower().strip() for v in val if str(v).strip()]
            elif isinstance(val, str):
                return [v.lower().strip() for v in val.split(",") if v.strip()]
            return []

        self.df["skin_type"] = self.df["skin_type"].apply(normalize_list)
        self.df["category"] = self.df["category"].apply(normalize_list)

        # ===============================
        # COMBINED TEXT
        # ===============================
        if "combined_text" not in self.df.columns:
            self.df["combined_text"] = self.df.apply(
                lambda row: " ".join([
                    str(row.get("name", "")),
                    str(row.get("about", "")),
                    str(row.get("ingredients", "")),
                    " ".join(row.get("category", [])),
                    " ".join(row.get("skin_type", []))
                ]),
                axis=1
            )

        # ===============================
        # TF-IDF
        # ===============================
        self.tfidf = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words=None
        )

        self.tfidf_matrix = self.tfidf.fit_transform(self.df["combined_text"])
        self.cosine_sim = cosine_similarity(self.tfidf_matrix)
        self.feature_names = self.tfidf.get_feature_names_out()

    # =====================================================
    # RECOMMENDATION
    # =====================================================
    def recommend(self, skin_types=None, categories=None, top_n=5):

        if self.df.empty:
            return pd.DataFrame()

        skin_types = skin_types or []
        categories = categories or []

        if isinstance(skin_types, str):
            skin_types = [skin_types]
        if isinstance(categories, str):
            categories = [categories]

        skin_types = [s.lower().strip() for s in skin_types]
        categories = [c.lower().strip() for c in categories]

        filtered_idx = []

        for idx, row in self.df.iterrows():
            row_skin_types = row["skin_type"]
            row_categories = row["category"]

            # ===============================
            # SKIN TYPE FILTER (FIXED)
            # ===============================
            if "all skin types" in skin_types:
                skin_match = True
            elif "all skin types" in row_skin_types:
                skin_match = True
            else:
                skin_match = any(s in row_skin_types for s in skin_types)

            # ===============================
            # CATEGORY FILTER (FLEXIBLE MATCH)
            # ===============================
            category_match = any(
                c in rc for c in categories for rc in row_categories
            )

            if skin_match and category_match:
                filtered_idx.append(idx)

        if not filtered_idx:
            return pd.DataFrame()

        # ===============================
        # SIMILARITY
        # ===============================
        if len(filtered_idx) == 1:
            sim_scores = self.cosine_sim[filtered_idx[0]]
        else:
            sim_scores = self.cosine_sim[filtered_idx].mean(axis=0)

        scores_df = pd.DataFrame({
            "index": filtered_idx,
            "similarity": sim_scores[filtered_idx]
        }).sort_values(by="similarity", ascending=False)

        top_indices = scores_df.head(top_n)["index"].tolist()

        recommendations = self.df.loc[top_indices].copy()
        recommendations["similarity_score"] = scores_df.head(top_n)["similarity"].values

        return recommendations

    # =====================================================
    # STATISTICS
    # =====================================================
    def get_statistics(self):
        return {
            "total_products": len(self.df),
            "total_categories": len(
                set(cat for sub in self.df["category"] for cat in sub)
            ),
            "total_skin_types": len(
                set(skin for sub in self.df["skin_type"] for skin in sub)
            ),
            "feature_count": len(self.feature_names)
        }

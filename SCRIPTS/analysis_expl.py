from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ============================================================
# CONFIGURATION
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}


@dataclass
class AnalysisConfig:
    csv_path: Path
    output_dir: Path
    currency_symbol: str = "€"
    rolling_window: int = 3
    min_adr_threshold: float = 0.0
    max_adr_threshold: float = 2000.0


class HotelRevenueAnalytics:
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.df_raw: Optional[pd.DataFrame] = None
        self.df: Optional[pd.DataFrame] = None
        self.df_active: Optional[pd.DataFrame] = None

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    def load_from_csv(self) -> pd.DataFrame:
        logging.info("Loading CSV data from: %s", self.config.csv_path)

        if not self.config.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.config.csv_path}")

        self.df_raw = pd.read_csv(self.config.csv_path)
        logging.info("Dataset loaded: %s rows, %s columns", len(self.df_raw), len(self.df_raw.columns))
        return self.df_raw

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    def validate_schema(self, df: pd.DataFrame) -> None:
        required_cols = {
            "hotel",
            "is_canceled",
            "lead_time",
            "arrival_date_year",
            "arrival_date_month",
            "stays_in_weekend_nights",
            "stays_in_week_nights",
            "adr",
            "market_segment",
            "distribution_channel",
            "customer_type"
        }

        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        logging.info("Schema validation passed")

    # --------------------------------------------------------
    # CLEANING + FEATURE ENGINEERING
    # --------------------------------------------------------

    def clean_and_engineer_features(self) -> pd.DataFrame:
        if self.df_raw is None:
            raise ValueError("No dataset loaded")

        df = self.df_raw.copy()
        df.columns = [c.strip().lower() for c in df.columns]

        self.validate_schema(df)

        df["arrival_month_num"] = df["arrival_date_month"].map(MONTH_MAP)
        if df["arrival_month_num"].isna().any():
            bad_months = df.loc[df["arrival_month_num"].isna(), "arrival_date_month"].unique()
            raise ValueError(f"Unknown month names in dataset: {bad_months}")

        df["arrival_date"] = pd.to_datetime({
            "year": df["arrival_date_year"],
            "month": df["arrival_month_num"],
            "day": 1
        })

        df["total_nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
        df["total_nights"] = df["total_nights"].clip(lower=0)

        df["adr"] = pd.to_numeric(df["adr"], errors="coerce")
        df = df[df["adr"].between(self.config.min_adr_threshold, self.config.max_adr_threshold)]

        df["total_revenue"] = df["adr"] * df["total_nights"]

        df["booking_channel"] = np.where(
            df["distribution_channel"].str.contains("direct", case=False, na=False),
            "Direct",
            "Indirect / OTA"
        )

        df["lead_time_bucket"] = pd.cut(
            df["lead_time"],
            bins=[-1, 7, 30, 90, 180, np.inf],
            labels=["0-7d", "8-30d", "31-90d", "91-180d", "180d+"]
        )

        self.df = df
        self.df_active = df[df["is_canceled"] == 0].copy()

        logging.info("Cleaned dataset: %s rows", len(self.df))
        logging.info("Active bookings only: %s rows", len(self.df_active))

        return self.df

    # --------------------------------------------------------
    # KPI TABLES
    # --------------------------------------------------------

    def compute_global_kpis(self) -> pd.DataFrame:
        if self.df is None or self.df_active is None:
            raise ValueError("Prepare data before computing KPIs")

        total_bookings = len(self.df)
        active_bookings = len(self.df_active)
        cancellations = int(self.df["is_canceled"].sum())
        cancellation_rate = (cancellations / total_bookings * 100) if total_bookings else np.nan
        average_adr = self.df_active["adr"].mean()
        total_revenue = self.df_active["total_revenue"].sum()
        average_stay = self.df_active["total_nights"].mean()
        average_lead_time = self.df["lead_time"].mean()

        kpis = pd.DataFrame({
            "metric": [
                "total_bookings",
                "active_bookings",
                "cancellations",
                "cancellation_rate_pct",
                "average_adr",
                "total_revenue",
                "average_length_of_stay",
                "average_lead_time"
            ],
            "value": [
                total_bookings,
                active_bookings,
                cancellations,
                round(cancellation_rate, 2),
                round(average_adr, 2),
                round(total_revenue, 2),
                round(average_stay, 2),
                round(average_lead_time, 2)
            ]
        })

        output_path = self.config.output_dir / "global_kpis.csv"
        kpis.to_csv(output_path, index=False)
        logging.info("Saved: %s", output_path)

        return kpis

    def compute_monthly_financials(self) -> pd.DataFrame:
        if self.df_active is None:
            raise ValueError("Active dataset missing")

        monthly = (
            self.df_active
            .groupby("arrival_date", as_index=False)
            .agg(
                bookings=("hotel", "count"),
                revenue=("total_revenue", "sum"),
                adr=("adr", "mean"),
                avg_stay=("total_nights", "mean")
            )
            .sort_values("arrival_date")
        )

        monthly["revenue_growth_pct"] = monthly["revenue"].pct_change() * 100
        monthly["revenue_rolling_mean"] = monthly["revenue"].rolling(self.config.rolling_window).mean()

        output_path = self.config.output_dir / "monthly_financials.csv"
        monthly.to_csv(output_path, index=False)
        logging.info("Saved: %s", output_path)

        return monthly

    def compute_channel_profitability(self) -> pd.DataFrame:
        if self.df_active is None:
            raise ValueError("Active dataset missing")

        channel = (
            self.df_active
            .groupby(["market_segment", "booking_channel"], as_index=False)
            .agg(
                bookings=("hotel", "count"),
                avg_adr=("adr", "mean"),
                total_revenue=("total_revenue", "sum"),
                avg_stay=("total_nights", "mean")
            )
            .sort_values(["total_revenue", "avg_adr"], ascending=False)
        )

        output_path = self.config.output_dir / "channel_profitability.csv"
        channel.to_csv(output_path, index=False)
        logging.info("Saved: %s", output_path)

        return channel

    def compute_cancellation_risk(self) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("Prepared dataset missing")

        cancel = (
            self.df
            .groupby(
                ["market_segment", "customer_type", "lead_time_bucket"],
                observed=False
            )
            .agg(
                total_bookings=("is_canceled", "count"),
                cancelled=("is_canceled", "sum")
            )
            .reset_index()
        )

        cancel["cancellation_rate_pct"] = (
            100 * cancel["cancelled"] / cancel["total_bookings"]
        ).round(2)

        output_path = self.config.output_dir / "cancellation_risk.csv"
        cancel.to_csv(output_path, index=False)
        logging.info("Saved: %s", output_path)

        return cancel

    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    def format_currency_axis(self, ax) -> None:
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{self.config.currency_symbol}{x:,.0f}")
        )

    def plot_monthly_revenue(self, monthly: pd.DataFrame) -> None:
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(
            monthly["arrival_date"],
            monthly["revenue"],
            linewidth=2.5,
            marker="o",
            label="Monthly Revenue"
        )

        ax.plot(
            monthly["arrival_date"],
            monthly["revenue_rolling_mean"],
            linewidth=2.0,
            linestyle="--",
            label=f"{self.config.rolling_window}-Month Rolling Mean"
        )

        ax.set_title("Monthly Revenue Trend", fontsize=14, fontweight="bold")
        ax.set_xlabel("Month")
        ax.set_ylabel("Revenue")
        self.format_currency_axis(ax)
        ax.legend()
        ax.grid(alpha=0.3)

        plt.tight_layout()
        path = self.config.output_dir / "monthly_revenue_trend.png"
        plt.savefig(path, dpi=180, bbox_inches="tight")
        plt.close()
        logging.info("Saved chart: %s", path)

    def plot_adr_by_segment(self, channel_df: pd.DataFrame) -> None:
        data = (
            channel_df.groupby("market_segment", as_index=False)["avg_adr"]
            .mean()
            .sort_values("avg_adr", ascending=False)
        )

        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(data["market_segment"], data["avg_adr"])

        ax.set_title("Average Daily Rate by Market Segment", fontsize=14, fontweight="bold")
        ax.set_xlabel("Market Segment")
        ax.set_ylabel("Average ADR")
        self.format_currency_axis(ax)
        ax.grid(axis="y", alpha=0.25)

        for bar in bars:
            value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value,
                f"{self.config.currency_symbol}{value:,.0f}",
                ha="center",
                va="bottom",
                fontsize=9
            )

        plt.xticks(rotation=35, ha="right")
        plt.tight_layout()
        path = self.config.output_dir / "adr_by_market_segment.png"
        plt.savefig(path, dpi=180, bbox_inches="tight")
        plt.close()
        logging.info("Saved chart: %s", path)

    def plot_cancellation_risk(self, cancel_df: pd.DataFrame) -> None:
        pivot = cancel_df.pivot_table(
            index="market_segment",
            columns="lead_time_bucket",
            values="cancellation_rate_pct",
            aggfunc="mean"
        )

        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(pivot.values, aspect="auto")

        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)

        ax.set_title("Cancellation Risk by Segment and Lead Time", fontsize=14, fontweight="bold")
        ax.set_xlabel("Lead Time Bucket")
        ax.set_ylabel("Market Segment")

        for i in range(pivot.shape[0]):
            for j in range(pivot.shape[1]):
                value = pivot.iloc[i, j]
                if pd.notna(value):
                    ax.text(j, i, f"{value:.1f}%", ha="center", va="center", fontsize=8)

        fig.colorbar(im, ax=ax, label="Cancellation Rate (%)")
        plt.tight_layout()
        path = self.config.output_dir / "cancellation_risk_heatmap.png"
        plt.savefig(path, dpi=180, bbox_inches="tight")
        plt.close()
        logging.info("Saved chart: %s", path)

    # --------------------------------------------------------
    # FULL PIPELINE
    # --------------------------------------------------------

    def run(self) -> Dict[str, pd.DataFrame]:
        self.load_from_csv()
        self.clean_and_engineer_features()

        global_kpis = self.compute_global_kpis()
        monthly = self.compute_monthly_financials()
        channel = self.compute_channel_profitability()
        cancel = self.compute_cancellation_risk()

        self.plot_monthly_revenue(monthly)
        self.plot_adr_by_segment(channel)
        self.plot_cancellation_risk(cancel)

        return {
            "global_kpis": global_kpis,
            "monthly_financials": monthly,
            "channel_profitability": channel,
            "cancellation_risk": cancel
        }


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Hotel Revenue Analytics")
    parser.add_argument(
        "--csv",
        required=True,
        help="Full path to the CSV file"
    )
    parser.add_argument(
        "--output",
        default="output_analysis",
        help="Output folder for CSV results and charts"
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = AnalysisConfig(
        csv_path=csv_path,
        output_dir=output_dir
    )

    analytics = HotelRevenueAnalytics(config)
    results = analytics.run()

    print("\n=== GLOBAL KPIs ===")
    print(results["global_kpis"].to_string(index=False))

    print("\n=== TOP CHANNEL PROFITABILITY ===")
    print(results["channel_profitability"].head(10).to_string(index=False))

    print(f"\nResults saved in folder: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
# ============================================================
# Marriott International – Hotel Revenue Analytics
# Python Analysis Script
# ============================================================
# Requirements: pip install pandas matplotlib seaborn psycopg2-binary
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

# ─────────────────────────────────────────
# OPTION A : Load from CSV (Kaggle dataset)
# ─────────────────────────────────────────
# Download from: https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'DATA', 'hotel_bookings.csv')

def load_data(path=CSV_PATH):
    """Load and clean the hotel bookings dataset."""
    df = pd.read_csv(path)

    # Drop cancelled reservations for revenue analysis
    df_active = df[df['is_canceled'] == 0].copy()

    # Build arrival date
    month_map = {'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,
                 'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
    df_active['arrival_month_num'] = df_active['arrival_date_month'].map(month_map)
    df_active['arrival_date'] = pd.to_datetime(
        df_active['arrival_date_year'].astype(str) + '-' +
        df_active['arrival_month_num'].astype(str) + '-01'
    )

    # Total nights & estimated revenue
    df_active['total_nights'] = df_active['stays_in_weekend_nights'] + df_active['stays_in_week_nights']
    df_active['total_revenue'] = df_active['adr'] * df_active['total_nights']

    return df_active


# ─────────────────────────────────────────
# OPTION B : Load from PostgreSQL (optional)
# ─────────────────────────────────────────
def load_from_postgres(host='localhost', dbname='marriott_db',
                       user='postgres', password='yourpassword'):
    """
    Load reservation data directly from PostgreSQL.
    Run schema.sql first to create and populate the database.
    """
    import psycopg2
    conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
    query = """
        SELECT r.reservation_id, h.name AS hotel, ro.room_type,
               r.check_in, r.check_out, r.channel,
               r.total_revenue, c.loyalty_tier
        FROM Reservations r
        JOIN Rooms     ro ON ro.room_id    = r.room_id
        JOIN Hotels    h  ON h.hotel_id    = ro.hotel_id
        JOIN Customers c  ON c.customer_id = r.customer_id
        WHERE r.is_cancelled = FALSE
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# ─────────────────────────────────────────
# ANALYSIS 1 : ADR by booking channel
# ─────────────────────────────────────────
def plot_adr_by_channel(df):
    adr = df.groupby('market_segment')['adr'].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#C9A84C' if v == adr.max() else '#1B2A4A' for v in adr.values]
    bars = ax.bar(adr.index, adr.values, color=colors, edgecolor='white', linewidth=0.5)

    ax.set_title('Average Daily Rate (ADR) by Booking Channel', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Booking Channel', fontsize=11)
    ax.set_ylabel('ADR (€)', fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('€%.0f'))

    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'€{bar.get_height():.0f}', ha='center', va='bottom', fontsize=9)

    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    plt.savefig('adr_by_channel.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Chart saved: adr_by_channel.png")


# ─────────────────────────────────────────
# ANALYSIS 2 : Monthly revenue trend
# ─────────────────────────────────────────
def plot_monthly_revenue(df):
    monthly = df.groupby('arrival_date')['total_revenue'].sum().reset_index()
    monthly.columns = ['month', 'revenue']

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly['month'], monthly['revenue'], color='#1B2A4A', linewidth=2.5, marker='o', markersize=4)
    ax.fill_between(monthly['month'], monthly['revenue'], alpha=0.15, color='#C9A84C')

    ax.set_title('Monthly Revenue Trend', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Month', fontsize=11)
    ax.set_ylabel('Total Revenue (€)', fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'€{x:,.0f}'))

    plt.tight_layout()
    plt.savefig('monthly_revenue.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Chart saved: monthly_revenue.png")


# ─────────────────────────────────────────
# ANALYSIS 3 : Cancellation rate by customer type
# ─────────────────────────────────────────
def plot_cancellation_by_segment(df_full):
    cancel = df_full.groupby('market_segment').agg(
        total=('is_canceled', 'count'),
        cancelled=('is_canceled', 'sum')
    )
    cancel['rate'] = (cancel['cancelled'] / cancel['total'] * 100).round(1)
    cancel = cancel.sort_values('rate', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(cancel.index, cancel['rate'], color='#1B2A4A', edgecolor='white')
    ax.set_title('Cancellation Rate by Market Segment (%)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Cancellation Rate (%)', fontsize=11)

    for i, v in enumerate(cancel['rate']):
        ax.text(v + 0.3, i, f'{v}%', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig('cancellation_by_segment.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Chart saved: cancellation_by_segment.png")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == '__main__':
    print("Loading Marriott Revenue Analytics...")
    print(f"   Looking for data at: {CSV_PATH}\n")

    try:
        df_full = pd.read_csv(CSV_PATH)
        df = load_data(CSV_PATH)

        print(f"Dataset loaded: {len(df_full):,} total records | {len(df):,} non-cancelled")
        print(f"   Columns: {list(df.columns[:8])} ...\n")

        print("── Analysis 1: ADR by booking channel ──")
        plot_adr_by_channel(df)

        print("── Analysis 2: Monthly revenue trend ──")
        plot_monthly_revenue(df)

        print("── Analysis 3: Cancellation rates ──")
        plot_cancellation_by_segment(df_full)

        print("\n All analyses complete!")

    except FileNotFoundError:
        print("CSV file not found.")
        print("Download it from: https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand")
        print("Place it in the DATA/ folder as 'hotel_bookings.csv'")

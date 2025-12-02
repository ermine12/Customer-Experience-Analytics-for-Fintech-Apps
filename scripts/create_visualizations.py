"""
Task 4: Visualization Generator

Creates 3-5 visualizations for insights and recommendations:
1. Sentiment trends over time
2. Rating distribution by bank
3. Theme sentiment heatmap
4. Keyword analysis (word cloud alternative)
5. Bank comparison dashboard

Output:
- All visualizations saved to reports/visualizations/
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import THEME_DATA_PATH, SENTIMENT_DATA_PATH

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def load_data() -> pd.DataFrame:
    """Load reviews with themes and sentiment."""
    print("Loading review data...")
    
    if not THEME_DATA_PATH.exists():
        raise FileNotFoundError(f"Theme data not found: {THEME_DATA_PATH}")
    
    df = pd.read_csv(THEME_DATA_PATH)
    
    # Convert date column
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['year_month'] = df['date'].dt.to_period('M')
    
    print(f"Loaded {len(df):,} reviews")
    return df


def plot_sentiment_distribution_by_bank(df: pd.DataFrame, output_dir: Path):
    """Plot 1: Sentiment distribution comparison by bank."""
    print("Creating sentiment distribution plot...")
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Stacked bar chart
    sentiment_by_bank = pd.crosstab(df['bank'], df['sentiment_label'], normalize='index') * 100
    
    sentiment_by_bank.plot(kind='bar', stacked=True, ax=axes[0], 
                          color=['#2ecc71', '#f39c12', '#e74c3c'],
                          edgecolor='black', linewidth=0.5)
    axes[0].set_title('Sentiment Distribution by Bank (Percentage)', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Bank', fontsize=12)
    axes[0].set_ylabel('Percentage (%)', fontsize=12)
    axes[0].legend(title='Sentiment', labels=['Positive', 'Neutral', 'Negative'])
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].grid(axis='y', alpha=0.3)
    
    # Plot 2: Average rating by bank
    avg_rating = df.groupby('bank')['rating'].mean().sort_values(ascending=False)
    colors = ['#3498db' if r >= 4.0 else '#e67e22' if r >= 3.5 else '#e74c3c' 
              for r in avg_rating.values]
    
    bars = axes[1].bar(range(len(avg_rating)), avg_rating.values, color=colors, 
                       edgecolor='black', linewidth=0.5)
    axes[1].set_title('Average Rating by Bank', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Bank', fontsize=12)
    axes[1].set_ylabel('Average Rating (out of 5)', fontsize=12)
    axes[1].set_xticks(range(len(avg_rating)))
    axes[1].set_xticklabels(avg_rating.index, rotation=45, ha='right')
    axes[1].set_ylim(0, 5)
    axes[1].grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, avg_rating.values)):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    output_path = output_dir / "1_sentiment_distribution_by_bank.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_path.name}")


def plot_rating_distribution(df: pd.DataFrame, output_dir: Path):
    """Plot 2: Rating distribution by bank."""
    print("Creating rating distribution plot...")
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    banks = df['bank'].unique()
    colors_map = {5: '#2ecc71', 4: '#3498db', 3: '#f39c12', 2: '#e67e22', 1: '#e74c3c'}
    
    for idx, bank in enumerate(banks):
        bank_df = df[df['bank'] == bank]
        rating_counts = bank_df['rating'].value_counts().sort_index(ascending=False)
        
        bars = axes[idx].bar(range(len(rating_counts)), rating_counts.values,
                            color=[colors_map.get(r, '#95a5a6') for r in rating_counts.index],
                            edgecolor='black', linewidth=0.5)
        
        axes[idx].set_title(f'{bank}\nTotal Reviews: {len(bank_df)}', 
                           fontsize=12, fontweight='bold')
        axes[idx].set_xlabel('Rating (Stars)', fontsize=10)
        axes[idx].set_ylabel('Number of Reviews', fontsize=10)
        axes[idx].set_xticks(range(len(rating_counts)))
        axes[idx].set_xticklabels([f'{r}⭐' for r in rating_counts.index])
        axes[idx].grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar, val in zip(bars, rating_counts.values):
            axes[idx].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                          f'{val}', ha='center', va='bottom', fontsize=9)
    
    plt.suptitle('Rating Distribution by Bank', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    output_path = output_dir / "2_rating_distribution_by_bank.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_path.name}")


def plot_theme_sentiment_heatmap(df: pd.DataFrame, output_dir: Path):
    """Plot 3: Theme sentiment heatmap by bank."""
    print("Creating theme sentiment heatmap...")
    
    # Extract themes and calculate sentiment by theme and bank
    theme_data = []
    
    for _, row in df.iterrows():
        bank = row['bank']
        sentiment = row['sentiment_label']
        themes_str = row.get('themes', '')
        
        if pd.notna(themes_str) and themes_str:
            themes = [t.strip() for t in str(themes_str).split(',')]
            for theme in themes:
                theme_data.append({
                    'bank': bank,
                    'theme': theme,
                    'sentiment': sentiment
                })
    
    if not theme_data:
        print("  ⚠ No theme data available, skipping heatmap")
        return
    
    theme_df = pd.DataFrame(theme_data)
    
    # Calculate positive sentiment percentage by theme and bank
    heatmap_data = []
    for bank in theme_df['bank'].unique():
        for theme in theme_df['theme'].unique():
            subset = theme_df[(theme_df['bank'] == bank) & (theme_df['theme'] == theme)]
            if len(subset) > 0:
                positive_pct = (len(subset[subset['sentiment'] == 'positive']) / len(subset) * 100)
                heatmap_data.append({
                    'bank': bank,
                    'theme': theme,
                    'positive_pct': positive_pct,
                    'count': len(subset)
                })
    
    heatmap_df = pd.DataFrame(heatmap_data)
    
    if len(heatmap_df) == 0:
        print("  ⚠ No heatmap data available, skipping")
        return
    
    # Pivot for heatmap
    pivot_data = heatmap_df.pivot(index='theme', columns='bank', values='positive_pct')
    
    # Filter themes with sufficient data
    theme_counts = heatmap_df.groupby('theme')['count'].sum()
    significant_themes = theme_counts[theme_counts >= 20].index
    pivot_data = pivot_data.loc[significant_themes]
    
    if len(pivot_data) == 0:
        print("  ⚠ No significant themes for heatmap, skipping")
        return
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='RdYlGn', 
                vmin=0, vmax=100, center=50,
                cbar_kws={'label': 'Positive Sentiment (%)'},
                linewidths=0.5, linecolor='gray', ax=ax)
    
    ax.set_title('Theme Sentiment Heatmap by Bank\n(Positive Sentiment Percentage)', 
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Bank', fontsize=12)
    ax.set_ylabel('Theme', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    output_path = output_dir / "3_theme_sentiment_heatmap.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_path.name}")


def plot_sentiment_trends(df: pd.DataFrame, output_dir: Path):
    """Plot 4: Sentiment trends over time."""
    print("Creating sentiment trends plot...")
    
    if 'year_month' not in df.columns or df['year_month'].isna().all():
        print("  ⚠ No date data available, skipping trends plot")
        return
    
    # Group by month and bank
    monthly_sentiment = df.groupby(['year_month', 'bank', 'sentiment_label']).size().unstack(fill_value=0)
    
    if len(monthly_sentiment) == 0:
        print("  ⚠ No monthly data available, skipping trends plot")
        return
    
    fig, axes = plt.subplots(len(df['bank'].unique()), 1, figsize=(14, 5 * len(df['bank'].unique())))
    
    if len(df['bank'].unique()) == 1:
        axes = [axes]
    
    for idx, bank in enumerate(df['bank'].unique()):
        bank_df = df[df['bank'] == bank]
        bank_monthly = bank_df.groupby(['year_month', 'sentiment_label']).size().unstack(fill_value=0)
        
        # Convert period to string for plotting
        bank_monthly.index = bank_monthly.index.astype(str)
        
        ax = axes[idx]
        bank_monthly.plot(kind='line', ax=ax, marker='o', linewidth=2, markersize=6,
                          color={'positive': '#2ecc71', 'neutral': '#f39c12', 'negative': '#e74c3c'})
        
        ax.set_title(f'Sentiment Trends Over Time - {bank}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Month', fontsize=10)
        ax.set_ylabel('Number of Reviews', fontsize=10)
        ax.legend(title='Sentiment', labels=['Positive', 'Neutral', 'Negative'])
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
    
    plt.suptitle('Sentiment Trends Over Time by Bank', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    output_path = output_dir / "4_sentiment_trends_over_time.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_path.name}")


def plot_keyword_analysis(df: pd.DataFrame, output_dir: Path):
    """Plot 5: Top keywords by sentiment and bank."""
    print("Creating keyword analysis plot...")
    
    # Load keywords if available
    from config import KEYWORD_SUMMARY_PATH
    
    if not KEYWORD_SUMMARY_PATH.exists():
        print("  ⚠ Keywords file not found, creating alternative analysis...")
        # Alternative: Analyze review text for common words by sentiment
        return
    
    keywords_df = pd.read_csv(KEYWORD_SUMMARY_PATH)
    
    # Create visualization of top keywords by bank
    fig, axes = plt.subplots(len(df['bank'].unique()), 1, 
                            figsize=(12, 4 * len(df['bank'].unique())))
    
    if len(df['bank'].unique()) == 1:
        axes = [axes]
    
    for idx, bank in enumerate(df['bank'].unique()):
        bank_keywords = keywords_df[keywords_df['bank'] == bank].head(10)
        
        if len(bank_keywords) == 0:
            continue
        
        ax = axes[idx]
        y_pos = np.arange(len(bank_keywords))
        
        bars = ax.barh(y_pos, bank_keywords['tfidf_score'].values, 
                      color='#3498db', edgecolor='black', linewidth=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(bank_keywords['keyword'].values)
        ax.set_xlabel('TF-IDF Score', fontsize=10)
        ax.set_title(f'Top Keywords - {bank}', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, bank_keywords['tfidf_score'].values)):
            ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                   f'{val:.3f}', ha='left', va='center', fontsize=8)
    
    plt.suptitle('Top Keywords by Bank (TF-IDF Analysis)', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    output_path = output_dir / "5_keyword_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_path.name}")


def plot_bank_comparison_dashboard(df: pd.DataFrame, output_dir: Path):
    """Plot 6: Comprehensive bank comparison dashboard."""
    print("Creating bank comparison dashboard...")
    
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Overall sentiment comparison
    ax1 = fig.add_subplot(gs[0, 0])
    sentiment_pct = df.groupby('bank')['sentiment_label'].apply(
        lambda x: (x == 'positive').sum() / len(x) * 100
    ).sort_values(ascending=False)
    bars = ax1.bar(range(len(sentiment_pct)), sentiment_pct.values, 
                  color='#2ecc71', edgecolor='black', linewidth=0.5)
    ax1.set_title('Positive Sentiment %', fontweight='bold')
    ax1.set_xticks(range(len(sentiment_pct)))
    ax1.set_xticklabels(sentiment_pct.index, rotation=45, ha='right')
    ax1.set_ylabel('Percentage (%)')
    ax1.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, sentiment_pct.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 2. Average rating
    ax2 = fig.add_subplot(gs[0, 1])
    avg_rating = df.groupby('bank')['rating'].mean().sort_values(ascending=False)
    bars = ax2.bar(range(len(avg_rating)), avg_rating.values,
                  color='#3498db', edgecolor='black', linewidth=0.5)
    ax2.set_title('Average Rating', fontweight='bold')
    ax2.set_xticks(range(len(avg_rating)))
    ax2.set_xticklabels(avg_rating.index, rotation=45, ha='right')
    ax2.set_ylabel('Rating (out of 5)')
    ax2.set_ylim(0, 5)
    ax2.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, avg_rating.values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Review count
    ax3 = fig.add_subplot(gs[0, 2])
    review_count = df['bank'].value_counts()
    bars = ax3.bar(range(len(review_count)), review_count.values,
                  color='#9b59b6', edgecolor='black', linewidth=0.5)
    ax3.set_title('Total Reviews', fontweight='bold')
    ax3.set_xticks(range(len(review_count)))
    ax3.set_xticklabels(review_count.index, rotation=45, ha='right')
    ax3.set_ylabel('Number of Reviews')
    ax3.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, review_count.values):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{val}', ha='center', va='bottom', fontweight='bold')
    
    # 4. Rating distribution (stacked)
    ax4 = fig.add_subplot(gs[1, :])
    rating_by_bank = pd.crosstab(df['bank'], df['rating'])
    rating_by_bank.plot(kind='bar', stacked=True, ax=ax4, 
                       color=['#e74c3c', '#e67e22', '#f39c12', '#3498db', '#2ecc71'],
                       edgecolor='black', linewidth=0.5)
    ax4.set_title('Rating Distribution by Bank', fontweight='bold')
    ax4.set_xlabel('Bank')
    ax4.set_ylabel('Number of Reviews')
    ax4.legend(title='Rating', labels=['1⭐', '2⭐', '3⭐', '4⭐', '5⭐'], 
              bbox_to_anchor=(1.05, 1), loc='upper left')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(axis='y', alpha=0.3)
    
    # 5. Sentiment breakdown
    ax5 = fig.add_subplot(gs[2, :])
    sentiment_by_bank = pd.crosstab(df['bank'], df['sentiment_label'])
    sentiment_by_bank.plot(kind='bar', ax=ax5, 
                           color=['#2ecc71', '#f39c12', '#e74c3c'],
                           edgecolor='black', linewidth=0.5)
    ax5.set_title('Sentiment Count by Bank', fontweight='bold')
    ax5.set_xlabel('Bank')
    ax5.set_ylabel('Number of Reviews')
    ax5.legend(title='Sentiment', labels=['Positive', 'Neutral', 'Negative'])
    ax5.tick_params(axis='x', rotation=45)
    ax5.grid(axis='y', alpha=0.3)
    
    plt.suptitle('Bank Comparison Dashboard', fontsize=18, fontweight='bold', y=0.995)
    
    output_path = output_dir / "6_bank_comparison_dashboard.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_path.name}")


def main():
    """Main execution function."""
    print("=" * 80)
    print("CREATING VISUALIZATIONS")
    print("=" * 80)
    
    # Create output directory
    output_dir = PROJECT_ROOT / "reports" / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_data()
    
    # Create all visualizations
    plot_sentiment_distribution_by_bank(df, output_dir)
    plot_rating_distribution(df, output_dir)
    plot_theme_sentiment_heatmap(df, output_dir)
    plot_sentiment_trends(df, output_dir)
    plot_keyword_analysis(df, output_dir)
    plot_bank_comparison_dashboard(df, output_dir)
    
    print("\n" + "=" * 80)
    print("✓ All visualizations created successfully!")
    print(f"  Output directory: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()


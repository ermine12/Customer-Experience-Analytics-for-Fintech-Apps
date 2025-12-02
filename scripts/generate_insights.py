"""
Task 4: Insights and Recommendations Generator

This script analyzes sentiment and theme data to generate:
- Drivers (positive aspects) per bank
- Pain points (negative aspects) per bank
- Bank comparisons
- Improvement recommendations

Output:
- insights_summary.json: Structured insights data
- insights_report.txt: Human-readable insights report
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import json
from collections import defaultdict
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import THEME_DATA_PATH, SENTIMENT_DATA_PATH, BANKS


def load_data() -> pd.DataFrame:
    """Load reviews with themes and sentiment."""
    print("Loading review data...")
    
    if not THEME_DATA_PATH.exists():
        raise FileNotFoundError(f"Theme data not found: {THEME_DATA_PATH}")
    
    df = pd.read_csv(THEME_DATA_PATH)
    print(f"Loaded {len(df):,} reviews with themes and sentiment")
    return df


def analyze_theme_sentiment(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Analyze sentiment by theme for each bank.
    
    Returns:
        Dictionary with bank -> theme -> sentiment stats
    """
    results = {}
    
    for bank_name in df['bank'].unique():
        bank_df = df[df['bank'] == bank_name]
        bank_results = {}
        
        # Get all themes (from themes column, which may contain multiple themes)
        all_themes = set()
        for themes_str in bank_df['themes'].dropna():
            if pd.notna(themes_str):
                themes = [t.strip() for t in str(themes_str).split(',')]
                all_themes.update(themes)
        
        for theme in all_themes:
            # Filter reviews with this theme
            theme_reviews = bank_df[
                bank_df['themes'].str.contains(theme, case=False, na=False)
            ]
            
            if len(theme_reviews) > 0:
                total = len(theme_reviews)
                positive = len(theme_reviews[theme_reviews['sentiment_label'] == 'positive'])
                negative = len(theme_reviews[theme_reviews['sentiment_label'] == 'negative'])
                avg_rating = theme_reviews['rating'].mean()
                
                bank_results[theme] = {
                    'total_reviews': total,
                    'positive_count': positive,
                    'negative_count': negative,
                    'positive_pct': (positive / total * 100) if total > 0 else 0,
                    'negative_pct': (negative / total * 100) if total > 0 else 0,
                    'avg_rating': round(avg_rating, 2),
                    'sample_reviews': {
                        'positive': theme_reviews[theme_reviews['sentiment_label'] == 'positive']['review'].head(2).tolist(),
                        'negative': theme_reviews[theme_reviews['sentiment_label'] == 'negative']['review'].head(2).tolist(),
                    }
                }
        
        results[bank_name] = bank_results
    
    return results


def identify_drivers(df: pd.DataFrame, theme_sentiment: Dict) -> Dict[str, List[Dict]]:
    """
    Identify drivers (positive aspects) for each bank.
    
    Drivers are themes with:
    - High positive sentiment percentage (>60%)
    - High average rating (>4.0)
    - Significant number of reviews (>20)
    """
    drivers = {}
    
    for bank_name in df['bank'].unique():
        bank_drivers = []
        bank_themes = theme_sentiment.get(bank_name, {})
        
        for theme, stats in bank_themes.items():
            if (stats['positive_pct'] >= 60 and 
                stats['avg_rating'] >= 4.0 and 
                stats['total_reviews'] >= 20):
                
                bank_drivers.append({
                    'theme': theme,
                    'positive_pct': round(stats['positive_pct'], 1),
                    'avg_rating': stats['avg_rating'],
                    'review_count': stats['total_reviews'],
                    'evidence': stats['sample_reviews']['positive'][:2]
                })
        
        # Sort by positive percentage
        bank_drivers.sort(key=lambda x: x['positive_pct'], reverse=True)
        drivers[bank_name] = bank_drivers[:5]  # Top 5 drivers
    
    return drivers


def identify_pain_points(df: pd.DataFrame, theme_sentiment: Dict) -> Dict[str, List[Dict]]:
    """
    Identify pain points (negative aspects) for each bank.
    
    Pain points are themes with:
    - High negative sentiment percentage (>30%)
    - Low average rating (<3.0)
    - Significant number of reviews (>10)
    """
    pain_points = {}
    
    for bank_name in df['bank'].unique():
        bank_pain_points = []
        bank_themes = theme_sentiment.get(bank_name, {})
        
        for theme, stats in bank_themes.items():
            if (stats['negative_pct'] >= 30 and 
                stats['avg_rating'] < 3.0 and 
                stats['total_reviews'] >= 10):
                
                bank_pain_points.append({
                    'theme': theme,
                    'negative_pct': round(stats['negative_pct'], 1),
                    'avg_rating': stats['avg_rating'],
                    'review_count': stats['total_reviews'],
                    'evidence': stats['sample_reviews']['negative'][:2]
                })
        
        # Sort by negative percentage
        bank_pain_points.sort(key=lambda x: x['negative_pct'], reverse=True)
        pain_points[bank_name] = bank_pain_points[:5]  # Top 5 pain points
    
    return pain_points


def compare_banks(df: pd.DataFrame) -> Dict:
    """Compare banks across key metrics."""
    comparison = {}
    
    for bank_name in df['bank'].unique():
        bank_df = df[df['bank'] == bank_name]
        
        total_reviews = len(bank_df)
        avg_rating = bank_df['rating'].mean()
        positive_pct = (len(bank_df[bank_df['sentiment_label'] == 'positive']) / total_reviews * 100) if total_reviews > 0 else 0
        negative_pct = (len(bank_df[bank_df['sentiment_label'] == 'negative']) / total_reviews * 100) if total_reviews > 0 else 0
        
        # Rating distribution
        rating_dist = bank_df['rating'].value_counts().to_dict()
        
        # Top themes
        all_themes = []
        for themes_str in bank_df['themes'].dropna():
            if pd.notna(themes_str):
                themes = [t.strip() for t in str(themes_str).split(',')]
                all_themes.extend(themes)
        
        theme_counts = pd.Series(all_themes).value_counts().head(5).to_dict()
        
        comparison[bank_name] = {
            'total_reviews': total_reviews,
            'avg_rating': round(avg_rating, 2),
            'positive_pct': round(positive_pct, 1),
            'negative_pct': round(negative_pct, 1),
            'rating_distribution': {int(k): int(v) for k, v in rating_dist.items()},
            'top_themes': {k: int(v) for k, v in theme_counts.items()}
        }
    
    return comparison


def generate_recommendations(drivers: Dict, pain_points: Dict, comparison: Dict) -> Dict[str, List[Dict]]:
    """
    Generate improvement recommendations for each bank.
    
    Recommendations are based on:
    - Pain points that need addressing
    - Opportunities to leverage drivers
    - Competitive gaps
    """
    recommendations = {}
    
    # Get all banks for comparison
    banks = list(comparison.keys())
    
    for bank_name in banks:
        bank_recs = []
        
        # Recommendations based on pain points
        for pain_point in pain_points.get(bank_name, [])[:3]:
            theme = pain_point['theme']
            
            if theme == "Performance & Reliability":
                rec = {
                    'priority': 'HIGH',
                    'category': 'Technical',
                    'recommendation': 'Improve app stability and performance',
                    'rationale': f"{pain_point['negative_pct']}% of reviews mention {theme} issues with avg rating {pain_point['avg_rating']}",
                    'actions': [
                        'Conduct comprehensive performance testing',
                        'Optimize app startup time and response speed',
                        'Fix reported crashes and freezing issues',
                        'Implement better error handling and recovery'
                    ]
                }
            elif theme == "Access & Login":
                rec = {
                    'priority': 'HIGH',
                    'category': 'Security & UX',
                    'recommendation': 'Streamline login and authentication process',
                    'rationale': f"{pain_point['negative_pct']}% of reviews mention {theme} issues",
                    'actions': [
                        'Simplify login flow (reduce steps)',
                        'Improve biometric authentication reliability',
                        'Fix OTP delivery issues',
                        'Add "Remember me" option for trusted devices'
                    ]
                }
            elif theme == "Transactions & Payments":
                rec = {
                    'priority': 'HIGH',
                    'category': 'Core Functionality',
                    'recommendation': 'Enhance transaction reliability and user experience',
                    'rationale': f"{pain_point['negative_pct']}% of reviews mention {theme} issues",
                    'actions': [
                        'Improve transaction success rate',
                        'Add transaction status notifications',
                        'Simplify payment flow',
                        'Add transaction history search and filters'
                    ]
                }
            elif theme == "Customer Support":
                rec = {
                    'priority': 'MEDIUM',
                    'category': 'Service',
                    'recommendation': 'Enhance customer support channels',
                    'rationale': f"{pain_point['negative_pct']}% of reviews mention {theme} issues",
                    'actions': [
                        'Add in-app chat support',
                        'Reduce response time',
                        'Improve support agent training',
                        'Add FAQ section within app'
                    ]
                }
            elif theme == "User Experience":
                rec = {
                    'priority': 'MEDIUM',
                    'category': 'Design',
                    'recommendation': 'Improve app interface and navigation',
                    'rationale': f"{pain_point['negative_pct']}% of reviews mention {theme} issues",
                    'actions': [
                        'Redesign navigation for better intuitiveness',
                        'Improve visual design consistency',
                        'Add user customization options',
                        'Conduct UX research and user testing'
                    ]
                }
            else:
                rec = {
                    'priority': 'MEDIUM',
                    'category': 'General',
                    'recommendation': f'Address {theme} concerns',
                    'rationale': f"{pain_point['negative_pct']}% of reviews mention {theme} issues",
                    'actions': [
                        'Analyze specific complaints in detail',
                        'Prioritize most common issues',
                        'Develop targeted solutions'
                    ]
                }
            
            bank_recs.append(rec)
        
        # Competitive recommendations (based on what competitors do well)
        bank_avg_rating = comparison[bank_name]['avg_rating']
        for other_bank in banks:
            if other_bank != bank_name:
                other_rating = comparison[other_bank]['avg_rating']
                if other_rating > bank_avg_rating + 0.3:  # Significant gap
                    other_drivers = drivers.get(other_bank, [])
                    for driver in other_drivers[:2]:  # Top 2 drivers from competitor
                        if driver['theme'] not in [r.get('theme', '') for r in bank_recs]:
                            bank_recs.append({
                                'priority': 'MEDIUM',
                                'category': 'Competitive',
                                'recommendation': f"Learn from {other_bank}: Improve {driver['theme']}",
                                'rationale': f"{other_bank} has {driver['positive_pct']}% positive sentiment for {driver['theme']}",
                                'actions': [
                                    f'Study {other_bank}\'s approach to {driver["theme"]}',
                                    'Adapt best practices to your app',
                                    'Conduct user research on this aspect'
                                ]
                            })
        
        recommendations[bank_name] = bank_recs[:5]  # Top 5 recommendations
    
    return recommendations


def generate_insights_report(insights: Dict, output_path: Path):
    """Generate human-readable insights report."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CUSTOMER EXPERIENCE ANALYTICS - INSIGHTS REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        # Drivers
        f.write("DRIVERS (Positive Aspects)\n")
        f.write("-" * 80 + "\n\n")
        for bank_name, bank_drivers in insights['drivers'].items():
            f.write(f"{bank_name}:\n")
            if bank_drivers:
                for i, driver in enumerate(bank_drivers, 1):
                    f.write(f"  {i}. {driver['theme']}\n")
                    f.write(f"     - Positive sentiment: {driver['positive_pct']}%\n")
                    f.write(f"     - Average rating: {driver['avg_rating']}/5.0\n")
                    f.write(f"     - Reviews: {driver['review_count']}\n")
                    if driver['evidence']:
                        f.write(f"     - Sample: \"{driver['evidence'][0][:100]}...\"\n")
                    f.write("\n")
            else:
                f.write("  No significant drivers identified.\n\n")
        
        # Pain Points
        f.write("\n" + "=" * 80 + "\n")
        f.write("PAIN POINTS (Negative Aspects)\n")
        f.write("-" * 80 + "\n\n")
        for bank_name, bank_pain_points in insights['pain_points'].items():
            f.write(f"{bank_name}:\n")
            if bank_pain_points:
                for i, pain_point in enumerate(bank_pain_points, 1):
                    f.write(f"  {i}. {pain_point['theme']}\n")
                    f.write(f"     - Negative sentiment: {pain_point['negative_pct']}%\n")
                    f.write(f"     - Average rating: {pain_point['avg_rating']}/5.0\n")
                    f.write(f"     - Reviews: {pain_point['review_count']}\n")
                    if pain_point['evidence']:
                        f.write(f"     - Sample: \"{pain_point['evidence'][0][:100]}...\"\n")
                    f.write("\n")
            else:
                f.write("  No significant pain points identified.\n\n")
        
        # Bank Comparison
        f.write("\n" + "=" * 80 + "\n")
        f.write("BANK COMPARISON\n")
        f.write("-" * 80 + "\n\n")
        for bank_name, stats in insights['comparison'].items():
            f.write(f"{bank_name}:\n")
            f.write(f"  Total Reviews: {stats['total_reviews']}\n")
            f.write(f"  Average Rating: {stats['avg_rating']}/5.0\n")
            f.write(f"  Positive Sentiment: {stats['positive_pct']}%\n")
            f.write(f"  Negative Sentiment: {stats['negative_pct']}%\n")
            f.write(f"  Top Themes: {', '.join(stats['top_themes'].keys())}\n")
            f.write("\n")
        
        # Recommendations
        f.write("\n" + "=" * 80 + "\n")
        f.write("RECOMMENDATIONS\n")
        f.write("-" * 80 + "\n\n")
        for bank_name, bank_recs in insights['recommendations'].items():
            f.write(f"{bank_name}:\n\n")
            for i, rec in enumerate(bank_recs, 1):
                f.write(f"  {i}. [{rec['priority']}] {rec['recommendation']}\n")
                f.write(f"     Category: {rec['category']}\n")
                f.write(f"     Rationale: {rec['rationale']}\n")
                f.write(f"     Actions:\n")
                for action in rec['actions']:
                    f.write(f"       - {action}\n")
                f.write("\n")


def main():
    """Main execution function."""
    print("=" * 80)
    print("GENERATING INSIGHTS AND RECOMMENDATIONS")
    print("=" * 80)
    
    # Load data
    df = load_data()
    
    # Analyze theme sentiment
    print("\nAnalyzing theme sentiment by bank...")
    theme_sentiment = analyze_theme_sentiment(df)
    
    # Identify drivers
    print("Identifying drivers (positive aspects)...")
    drivers = identify_drivers(df, theme_sentiment)
    
    # Identify pain points
    print("Identifying pain points (negative aspects)...")
    pain_points = identify_pain_points(df, theme_sentiment)
    
    # Compare banks
    print("Comparing banks...")
    comparison = compare_banks(df)
    
    # Generate recommendations
    print("Generating recommendations...")
    recommendations = generate_recommendations(drivers, pain_points, comparison)
    
    # Compile insights
    insights = {
        'drivers': drivers,
        'pain_points': pain_points,
        'comparison': comparison,
        'recommendations': recommendations
    }
    
    # Save JSON
    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / "insights_summary.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved insights to: {json_path}")
    
    # Generate report
    report_path = output_dir / "insights_report.txt"
    generate_insights_report(insights, report_path)
    print(f"✓ Saved insights report to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("INSIGHTS SUMMARY")
    print("=" * 80)
    
    for bank_name in df['bank'].unique():
        print(f"\n{bank_name}:")
        print(f"  Drivers: {len(drivers.get(bank_name, []))}")
        print(f"  Pain Points: {len(pain_points.get(bank_name, []))}")
        print(f"  Recommendations: {len(recommendations.get(bank_name, []))}")
    
    print("\n" + "=" * 80)
    print("✓ Insights generation completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()

